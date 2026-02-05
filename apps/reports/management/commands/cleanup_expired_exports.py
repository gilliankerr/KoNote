"""
Management command to clean up expired secure export links and orphan files.

Usage:
    python manage.py cleanup_expired_exports          # Delete expired links + orphan files
    python manage.py cleanup_expired_exports --dry-run # Preview what would be deleted

Intended to run as a scheduled task (e.g., daily cron) to keep the export
directory tidy and remove database records for links that are well past expiry.
"""

import os
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.reports.models import SecureExportLink


class Command(BaseCommand):
    help = (
        "Remove expired secure export links (DB records + files) and "
        "clean up orphan files with no matching database record."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting anything.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing will be deleted.\n"))

        # --- Step 1: Clean up expired links ---
        # Grace period: only delete links that expired more than 1 day ago.
        # This avoids deleting a link moments after it expires while a user
        # might still be mid-download.
        cutoff = timezone.now() - timedelta(days=1)
        expired_links = SecureExportLink.objects.filter(expires_at__lt=cutoff)

        expired_count = expired_links.count()
        db_deleted = 0
        files_deleted = 0
        file_delete_errors = 0

        self.stdout.write(
            f"Found {expired_count} expired export link(s) "
            f"(expired before {cutoff.strftime('%Y-%m-%d %H:%M %Z')})."
        )

        for link in expired_links:
            file_path = link.file_path
            link_id = str(link.id)

            if dry_run:
                file_exists = os.path.exists(file_path) if file_path else False
                self.stdout.write(
                    f"  Would delete link {link_id} — "
                    f"type: {link.export_type}, "
                    f"expired: {link.expires_at.strftime('%Y-%m-%d %H:%M')}, "
                    f"file exists: {file_exists}"
                )
                db_deleted += 1
                if file_exists:
                    files_deleted += 1
                continue

            # Delete DB record FIRST, then the file.
            # If DB delete succeeds but file delete fails, we have a harmless
            # orphan file (cleaned up in step 2 or next run).
            # If we deleted the file first and DB delete failed, the link
            # would show "file missing" errors to users.
            try:
                link.delete()
                db_deleted += 1
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"  Failed to delete DB record {link_id}: {exc}"
                    )
                )
                continue  # Skip file deletion if DB record still exists

            # Now remove the file on disk
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    files_deleted += 1
                except OSError as exc:
                    file_delete_errors += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  DB record deleted but could not remove file "
                            f"{file_path}: {exc}"
                        )
                    )

        # --- Step 2: Clean up orphan files ---
        # Files in SECURE_EXPORT_DIR that have no matching database record.
        # These can appear if a DB delete succeeded but a file delete failed,
        # or if files were created manually / left behind by crashes.
        export_dir = getattr(settings, "SECURE_EXPORT_DIR", None)
        orphan_count = 0

        if export_dir and os.path.isdir(export_dir):
            # Build a set of normalised file paths that still have live DB records
            active_paths = set(
                SecureExportLink.objects.values_list("file_path", flat=True)
            )
            active_normalised = {os.path.normpath(p) for p in active_paths}

            for filename in os.listdir(export_dir):
                full_path = os.path.join(export_dir, filename)

                # Skip directories — we only care about files
                if not os.path.isfile(full_path):
                    continue

                # Normalise path for comparison (consistent slashes, etc.)
                normalised = os.path.normpath(full_path)

                if normalised not in active_normalised:
                    if dry_run:
                        self.stdout.write(
                            f"  Would delete orphan file: {filename}"
                        )
                        orphan_count += 1
                    else:
                        try:
                            os.remove(full_path)
                            orphan_count += 1
                        except OSError as exc:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  Could not remove orphan file "
                                    f"{filename}: {exc}"
                                )
                            )
        elif export_dir:
            self.stdout.write(
                self.style.WARNING(
                    f"Export directory does not exist: {export_dir}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "SECURE_EXPORT_DIR is not configured — skipping orphan file cleanup."
                )
            )

        # --- Summary ---
        self.stdout.write("")  # blank line before summary
        action = "Would delete" if dry_run else "Deleted"

        self.stdout.write(
            self.style.SUCCESS(
                f"{action} {db_deleted} expired link(s) "
                f"({files_deleted} file(s) removed)."
            )
        )

        if file_delete_errors:
            self.stdout.write(
                self.style.WARNING(
                    f"{file_delete_errors} file(s) could not be removed "
                    f"(orphan files will be caught on next run)."
                )
            )

        if orphan_count:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} {orphan_count} orphan file(s) "
                    f"with no matching database record."
                )
            )
        else:
            self.stdout.write("No orphan files found.")

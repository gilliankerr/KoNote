"""
Django management command to seed the database with default data.

Run with: python manage.py seed
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed database with metric library, default terminology, and feature toggles."

    def handle(self, *args, **options):
        self._seed_metrics()
        self._seed_feature_toggles()
        self._seed_instance_settings()
        self._seed_event_types()
        self._seed_note_templates()
        self._seed_intake_fields()
        if settings.DEMO_MODE:
            self._create_demo_users_and_clients()
            self._update_demo_client_fields()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _seed_event_types(self):
        """Delegate to the seed_event_types command so all seeding runs in one place."""
        from django.core.management import call_command

        call_command("seed_event_types", stdout=self.stdout)

    def _seed_intake_fields(self):
        """Seed default custom fields for client intake forms."""
        from django.core.management import call_command

        call_command("seed_intake_fields", stdout=self.stdout)

    def _seed_note_templates(self):
        """Seed default note templates (Standard session, Brief check-in, etc.)."""
        from django.core.management import call_command

        call_command("seed_note_templates", stdout=self.stdout)

    def _seed_metrics(self):
        from apps.plans.models import MetricDefinition

        seed_file = Path(__file__).resolve().parent.parent.parent.parent.parent / "seeds" / "metric_library.json"
        with open(seed_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        created = 0
        for m in metrics:
            _, was_created = MetricDefinition.objects.get_or_create(
                name=m["name"],
                defaults={
                    "definition": m["definition"],
                    "category": m["category"],
                    "is_library": True,
                    "is_enabled": True,
                    "min_value": m.get("min_value"),
                    "max_value": m.get("max_value"),
                    "unit": m.get("unit", ""),
                },
            )
            if was_created:
                created += 1
        self.stdout.write(f"  Metrics: {created} created, {len(metrics) - created} already existed.")

    def _seed_feature_toggles(self):
        from apps.admin_settings.models import FeatureToggle

        defaults = [
            ("shift_summaries", False),
            ("client_avatar", False),
            ("programs", True),
            ("plan_export_to_word", False),
            ("events", True),
            ("alerts", True),
            ("quick_notes", True),
            ("analysis_charts", True),
            ("ai_assist", False),
        ]
        created = 0
        for key, enabled in defaults:
            _, was_created = FeatureToggle.objects.get_or_create(
                feature_key=key, defaults={"is_enabled": enabled}
            )
            if was_created:
                created += 1
        self.stdout.write(f"  Feature toggles: {created} created.")

    def _seed_instance_settings(self):
        from apps.admin_settings.models import InstanceSetting

        defaults = {
            "product_name": "KoNote2",
            "logo_url": "",
            "date_format": "YYYY-MM-DD",
            "time_format": "h:mma",
            "timestamp_format": "MMM D, YYYY - h:mma",
            "session_timeout_minutes": "30",
            "print_header": "",
            "print_footer": "CONFIDENTIAL",
            "default_client_tab": "notes",
        }
        created = 0
        for key, value in defaults.items():
            _, was_created = InstanceSetting.objects.get_or_create(
                setting_key=key, defaults={"setting_value": value}
            )
            if was_created:
                created += 1
        self.stdout.write(f"  Instance settings: {created} created.")

    def _create_demo_users_and_clients(self):
        """Create demo users, programs, and sample clients when DEMO_MODE is on."""
        from apps.auth_app.models import User
        from apps.clients.models import ClientFile, ClientProgramEnrolment
        from apps.programs.models import Program, UserProgramRole

        # Create demo programs
        program1, _ = Program.objects.get_or_create(
            name="Demo Program",
            defaults={"description": "A sample program for exploring KoNote2.", "colour_hex": "#6366F1"},
        )
        program2, _ = Program.objects.get_or_create(
            name="Youth Services",
            defaults={"description": "Youth outreach and support services.", "colour_hex": "#10B981"},
        )

        # Demo users: (username, display_name, is_admin)
        demo_users = [
            ("demo-frontdesk", "Dana Front Desk", False),
            ("demo-worker", "Casey Worker", False),
            ("demo-manager", "Morgan Manager", False),
            ("demo-executive", "Eva Executive", False),
            ("demo-admin", "Alex Admin", True),
        ]

        for username, display_name, is_admin in demo_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "display_name": display_name,
                    "is_admin": is_admin,
                    "is_demo": True,  # Demo users can only see demo clients
                },
            )
            if created:
                user.set_password("demo1234")
                user.save()

        # Assign program roles with specific access patterns:
        # - Front Desk: both programs (can see list of everyone, limited field access)
        # - Direct Service: only Demo Program (limited access to demonstrate permissions)
        # - Manager: both programs (can see details of everyone)
        # - Executive: both programs (dashboard only, no individual client access)
        front_desk = User.objects.get(username="demo-frontdesk")
        worker = User.objects.get(username="demo-worker")
        manager = User.objects.get(username="demo-manager")
        executive = User.objects.get(username="demo-executive")

        # Front Desk gets access to both programs
        UserProgramRole.objects.get_or_create(
            user=front_desk, program=program1,
            defaults={"role": "receptionist"},
        )
        UserProgramRole.objects.get_or_create(
            user=front_desk, program=program2,
            defaults={"role": "receptionist"},
        )

        # Direct Service worker gets access to only Demo Program (not Youth Services)
        UserProgramRole.objects.get_or_create(
            user=worker, program=program1,
            defaults={"role": "staff"},
        )

        # Manager gets access to both programs
        UserProgramRole.objects.get_or_create(
            user=manager, program=program1,
            defaults={"role": "program_manager"},
        )
        UserProgramRole.objects.get_or_create(
            user=manager, program=program2,
            defaults={"role": "program_manager"},
        )

        # Executive gets access to both programs (dashboard/aggregate view only)
        UserProgramRole.objects.get_or_create(
            user=executive, program=program1,
            defaults={"role": "executive"},
        )
        UserProgramRole.objects.get_or_create(
            user=executive, program=program2,
            defaults={"role": "executive"},
        )

        # Sample clients for Demo Program (DEMO-001 to DEMO-005)
        program1_clients = [
            ("Jordan", "Rivera", "2000-03-15", "DEMO-001"),
            ("Taylor", "Chen", "1995-07-22", "DEMO-002"),
            ("Avery", "Johnson", "1988-11-03", "DEMO-003"),
            ("Riley", "Patel", "2001-01-09", "DEMO-004"),
            ("Sam", "Williams", "1992-06-18", "DEMO-005"),
        ]

        # Sample clients for Youth Services (DEMO-006 to DEMO-010)
        program2_clients = [
            ("Jayden", "Martinez", "2007-05-12", "DEMO-006"),
            ("Maya", "Thompson", "2006-09-28", "DEMO-007"),
            ("Ethan", "Nguyen", "2008-01-15", "DEMO-008"),
            ("Zara", "Ahmed", "2005-11-03", "DEMO-009"),
            ("Liam", "O'Connor", "2007-08-22", "DEMO-010"),
        ]

        for first, last, dob, record_id in program1_clients:
            existing = ClientFile.objects.filter(record_id=record_id).first()
            if not existing:
                client = ClientFile()
                client.first_name = first
                client.last_name = last
                client.birth_date = dob
                client.record_id = record_id
                client.status = "active"
                client.is_demo = True  # Demo clients visible only to demo users
                client.save()
                ClientProgramEnrolment.objects.create(
                    client_file=client, program=program1, status="enrolled",
                )

        for first, last, dob, record_id in program2_clients:
            existing = ClientFile.objects.filter(record_id=record_id).first()
            if not existing:
                client = ClientFile()
                client.first_name = first
                client.last_name = last
                client.birth_date = dob
                client.record_id = record_id
                client.status = "active"
                client.is_demo = True  # Demo clients visible only to demo users
                client.save()
                ClientProgramEnrolment.objects.create(
                    client_file=client, program=program2, status="enrolled",
                )

        self.stdout.write("  Demo data: users, 2 programs, and 10 sample clients created.")
        self.stdout.write("    - Front Desk: sees all 10 clients (limited field access)")
        self.stdout.write("    - Direct Service: sees only 5 clients (Demo Program only)")
        self.stdout.write("    - Manager: sees all 10 clients with full details")
        self.stdout.write("    - Executive: sees aggregate dashboard (no individual clients)")

        # Populate demo clients with rich data for charts and reports
        from django.core.management import call_command

        call_command("seed_demo_data", stdout=self.stdout)

    def _update_demo_client_fields(self):
        """Populate custom field values and consent for demo clients."""
        from django.core.management import call_command

        call_command("update_demo_client_fields", stdout=self.stdout)

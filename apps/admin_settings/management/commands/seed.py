"""
Django management command to seed the database with default data.

Run with: python manage.py seed
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed database with metric library, default terminology, and feature toggles."

    def handle(self, *args, **options):
        self._seed_metrics()
        self._seed_feature_toggles()
        self._seed_instance_settings()
        self.stdout.write(self.style.SUCCESS("Seed data loaded successfully."))

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
            "product_name": "KoNote",
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

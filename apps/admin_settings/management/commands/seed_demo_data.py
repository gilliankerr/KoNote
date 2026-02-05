"""
Seed rich demo data for demo clients (DEMO-001 through DEMO-010).

Creates:
- Plans with sections and targets linked to metrics
- Progress notes with metric recordings following realistic trends
- Events (intake, follow-ups, referrals, crises)
- Alerts for clients with notable situations
- Custom field values (contact info, emergency contacts, referral sources)

This gives charts and reports meaningful data to display.

Run with: python manage.py seed_demo_data
Only runs when DEMO_MODE is enabled.
"""
import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.clients.models import ClientDetailValue, ClientFile, CustomFieldDefinition
from apps.events.models import Alert, Event, EventType
from apps.notes.models import MetricValue, ProgressNote, ProgressNoteTarget
from apps.plans.models import (
    MetricDefinition,
    PlanSection,
    PlanTarget,
    PlanTargetMetric,
    PlanTargetRevision,
)
from apps.programs.models import Program
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------------------
# Data definitions for each demo client
# ---------------------------------------------------------------------------

# Each client gets a "journey" profile that shapes the metric trends.
# Format per client:
#   sections: list of {name, targets: [{name, desc, metrics: [metric_name, ...]}]}
#   trend: "improving" | "struggling" | "mixed" | "stable" | "crisis_then_improving"
#   note_count: how many progress notes to create
#   note_texts_quick / note_texts_full: sample narrative snippets

CLIENT_PLANS = {
    # =========================================================================
    # Demo Program clients (DEMO-001 to DEMO-005)
    # =========================================================================
    "DEMO-001": {
        "label": "Jordan Rivera — steady improvement",
        "program": "Demo Program",
        "trend": "improving",
        "note_count": 10,
        "sections": [
            {
                "name": "Mental Health",
                "targets": [
                    {
                        "name": "Reduce depression symptoms",
                        "desc": "Bring PHQ-9 score below 10 within 6 months.",
                        "metrics": ["PHQ-9 (Depression)", "Wellness Scale"],
                    },
                    {
                        "name": "Build coping strategies",
                        "desc": "Develop at least 3 healthy coping techniques.",
                        "metrics": ["Coping Skills Rating"],
                    },
                ],
            },
            {
                "name": "Employment",
                "targets": [
                    {
                        "name": "Obtain part-time employment",
                        "desc": "Secure at least 15 hours/week of paid work.",
                        "metrics": ["Job Readiness Score", "Hours Worked (past week)"],
                    },
                ],
            },
        ],
    },
    "DEMO-002": {
        "label": "Taylor Chen — struggling, slow progress",
        "program": "Demo Program",
        "trend": "struggling",
        "note_count": 12,
        "sections": [
            {
                "name": "Housing",
                "targets": [
                    {
                        "name": "Secure stable housing",
                        "desc": "Transition from shelter to permanent housing.",
                        "metrics": ["Housing Stability Index", "Nights in Shelter (past 30 days)"],
                    },
                    {
                        "name": "Increase monthly income",
                        "desc": "Connect with income supports and employment.",
                        "metrics": ["Monthly Income"],
                    },
                ],
            },
            {
                "name": "Mental Health",
                "targets": [
                    {
                        "name": "Manage anxiety",
                        "desc": "Reduce GAD-7 score through counselling and supports.",
                        "metrics": ["GAD-7 (Anxiety)", "Wellness Scale"],
                    },
                ],
            },
        ],
    },
    "DEMO-003": {
        "label": "Avery Johnson — mixed results",
        "program": "Demo Program",
        "trend": "mixed",
        "note_count": 10,
        "sections": [
            {
                "name": "Substance Use",
                "targets": [
                    {
                        "name": "Reduce substance use",
                        "desc": "Increase days clean and reduce harm.",
                        "metrics": ["Days Clean", "Harm Reduction Score"],
                    },
                    {
                        "name": "Manage cravings",
                        "desc": "Develop strategies to cope with cravings.",
                        "metrics": ["Cravings Intensity"],
                    },
                ],
            },
            {
                "name": "Employment",
                "targets": [
                    {
                        "name": "Build job readiness",
                        "desc": "Complete resume, practise interviews.",
                        "metrics": ["Job Readiness Score", "Job Applications (past month)"],
                    },
                ],
            },
            {
                "name": "General Wellbeing",
                "targets": [
                    {
                        "name": "Strengthen support network",
                        "desc": "Reconnect with positive community supports.",
                        "metrics": ["Social Support Network", "Service Engagement"],
                    },
                ],
            },
        ],
    },
    "DEMO-004": {
        "label": "Riley Patel — youth, crisis then improving",
        "program": "Demo Program",
        "trend": "crisis_then_improving",
        "note_count": 10,
        "sections": [
            {
                "name": "Youth Development",
                "targets": [
                    {
                        "name": "Improve school attendance",
                        "desc": "Reach 80%+ attendance rate.",
                        "metrics": ["School Attendance Rate"],
                    },
                    {
                        "name": "Reduce risk behaviours",
                        "desc": "Decrease involvement in risky activities.",
                        "metrics": ["Risk Behaviour Index"],
                    },
                ],
            },
            {
                "name": "Family & Relationships",
                "targets": [
                    {
                        "name": "Improve family connection",
                        "desc": "Rebuild relationship with caregivers.",
                        "metrics": ["Family Connection Score"],
                    },
                ],
            },
            {
                "name": "Mental Health",
                "targets": [
                    {
                        "name": "Reduce psychological distress",
                        "desc": "Lower K10 score through counselling.",
                        "metrics": ["K10 (Psychological Distress)"],
                    },
                ],
            },
        ],
    },
    "DEMO-005": {
        "label": "Sam Williams — stable, near discharge",
        "program": "Demo Program",
        "trend": "stable",
        "note_count": 8,
        "sections": [
            {
                "name": "Life Skills",
                "targets": [
                    {
                        "name": "Develop independent living skills",
                        "desc": "Budgeting, cooking, time management.",
                        "metrics": ["Life Skills Assessment", "Goal Progress (1-10)"],
                    },
                ],
            },
            {
                "name": "Employment",
                "targets": [
                    {
                        "name": "Maintain employment",
                        "desc": "Keep current part-time job and explore full-time.",
                        "metrics": ["Employment Status", "Hours Worked (past week)"],
                    },
                ],
            },
        ],
    },
    # =========================================================================
    # Youth Services clients (DEMO-006 to DEMO-010)
    # =========================================================================
    "DEMO-006": {
        "label": "Jayden Martinez — new to program, showing promise",
        "program": "Youth Services",
        "trend": "improving",
        "note_count": 8,
        "sections": [
            {
                "name": "Education",
                "targets": [
                    {
                        "name": "Improve academic engagement",
                        "desc": "Increase participation and grades in core subjects.",
                        "metrics": ["School Attendance Rate", "Goal Progress (1-10)"],
                    },
                ],
            },
            {
                "name": "Life Skills",
                "targets": [
                    {
                        "name": "Develop conflict resolution skills",
                        "desc": "Learn to manage disagreements without escalation.",
                        "metrics": ["Coping Skills Rating"],
                    },
                ],
            },
        ],
    },
    "DEMO-007": {
        "label": "Maya Thompson — overcoming social anxiety",
        "program": "Youth Services",
        "trend": "crisis_then_improving",
        "note_count": 10,
        "sections": [
            {
                "name": "Mental Health",
                "targets": [
                    {
                        "name": "Manage social anxiety",
                        "desc": "Reduce avoidance behaviours and increase social activities.",
                        "metrics": ["GAD-7 (Anxiety)", "Wellness Scale"],
                    },
                ],
            },
            {
                "name": "Social Connection",
                "targets": [
                    {
                        "name": "Build peer relationships",
                        "desc": "Participate in group activities and make new friends.",
                        "metrics": ["Social Support Network", "Service Engagement"],
                    },
                ],
            },
        ],
    },
    "DEMO-008": {
        "label": "Ethan Nguyen — struggling with family conflict",
        "program": "Youth Services",
        "trend": "struggling",
        "note_count": 9,
        "sections": [
            {
                "name": "Family & Relationships",
                "targets": [
                    {
                        "name": "Improve family communication",
                        "desc": "Work with family on healthier communication patterns.",
                        "metrics": ["Family Connection Score"],
                    },
                ],
            },
            {
                "name": "Mental Health",
                "targets": [
                    {
                        "name": "Reduce emotional distress",
                        "desc": "Build coping strategies for family stress.",
                        "metrics": ["K10 (Psychological Distress)", "Coping Skills Rating"],
                    },
                ],
            },
            {
                "name": "Education",
                "targets": [
                    {
                        "name": "Maintain school attendance",
                        "desc": "Stay engaged despite home challenges.",
                        "metrics": ["School Attendance Rate"],
                    },
                ],
            },
        ],
    },
    "DEMO-009": {
        "label": "Zara Ahmed — leadership potential, mixed focus",
        "program": "Youth Services",
        "trend": "mixed",
        "note_count": 11,
        "sections": [
            {
                "name": "Youth Development",
                "targets": [
                    {
                        "name": "Develop leadership skills",
                        "desc": "Take on peer mentorship and group facilitation roles.",
                        "metrics": ["Goal Progress (1-10)", "Service Engagement"],
                    },
                    {
                        "name": "Balance commitments",
                        "desc": "Manage school, work, and program activities.",
                        "metrics": ["Life Skills Assessment"],
                    },
                ],
            },
            {
                "name": "Education",
                "targets": [
                    {
                        "name": "Prepare for post-secondary",
                        "desc": "Research options and prepare applications.",
                        "metrics": ["Job Readiness Score"],
                    },
                ],
            },
        ],
    },
    "DEMO-010": {
        "label": "Liam O'Connor — stable, transitioning out",
        "program": "Youth Services",
        "trend": "stable",
        "note_count": 7,
        "sections": [
            {
                "name": "Life Skills",
                "targets": [
                    {
                        "name": "Prepare for independent living",
                        "desc": "Master budgeting, cooking, and self-care routines.",
                        "metrics": ["Life Skills Assessment", "Goal Progress (1-10)"],
                    },
                ],
            },
            {
                "name": "Employment",
                "targets": [
                    {
                        "name": "Secure part-time employment",
                        "desc": "Balance work with school and maintain income.",
                        "metrics": ["Job Readiness Score", "Hours Worked (past week)"],
                    },
                ],
            },
        ],
    },
}

# Quick note text samples
QUICK_NOTE_TEXTS = [
    "Brief check-in. Client reports feeling well today.",
    "Phone call — client confirmed attendance for group session tomorrow.",
    "Client dropped in to update address. No concerns raised.",
    "Left voicemail for client re: upcoming appointment.",
    "Quick chat in the hallway. Client in good spirits.",
    "Client called to reschedule. Moved to next Thursday.",
    "Checked in after missed appointment. Client apologised, will attend next week.",
    "Client picked up transit tokens. Seemed tired but stable.",
]

# Full note summary samples
FULL_NOTE_SUMMARIES = [
    "Reviewed progress on plan targets. Client showing engagement and motivation.",
    "Counselling session focused on coping strategies. Practised deep breathing exercises.",
    "Discussed housing search progress. Reviewed two apartment listings together.",
    "Reviewed employment goals. Updated resume and practised interview questions.",
    "Family mediation session. Some progress on communication between client and parent.",
    "Group session debrief. Client participated actively and supported peers.",
    "Goal-setting session. Adjusted timelines for two targets based on recent progress.",
    "Crisis follow-up. Client is stable; updated safety plan.",
    "Substance use check-in. Client reports reduced use but still struggling on weekends.",
    "Comprehensive review of all plan targets. Celebrated milestones achieved.",
    "Joint meeting with client and housing worker. Application submitted for supportive housing.",
    "Session focused on anxiety management. Introduced grounding techniques.",
]


def _generate_trend_values(trend, count, metric_name, metric_def):
    """Generate a list of metric values that follow a realistic trend."""
    lo = metric_def.min_value or 0
    hi = metric_def.max_value or 100

    # For "lower is better" metrics, invert the trend direction
    lower_is_better = metric_name in (
        "PHQ-9 (Depression)", "GAD-7 (Anxiety)", "K10 (Psychological Distress)",
        "Nights in Shelter (past 30 days)", "Cravings Intensity",
    )

    values = []
    for i in range(count):
        t = i / max(count - 1, 1)  # 0.0 to 1.0

        if trend == "improving":
            if lower_is_better:
                base = hi * 0.7 + (hi * 0.2 - hi * 0.7) * t  # high → low
            else:
                base = lo + (lo + (hi - lo) * 0.3) + ((hi - lo) * 0.5) * t  # low → high
                base = lo + (hi - lo) * (0.25 + 0.5 * t)

        elif trend == "struggling":
            if lower_is_better:
                base = hi * 0.5 + (hi * 0.1) * t  # stays high, slight increase
            else:
                base = lo + (hi - lo) * (0.35 - 0.1 * t)  # stays low, slight decrease

        elif trend == "mixed":
            # Zigzag pattern
            if i % 3 == 0:
                base = lo + (hi - lo) * 0.5
            elif i % 3 == 1:
                base = lo + (hi - lo) * 0.35
            else:
                base = lo + (hi - lo) * 0.6
            if lower_is_better:
                base = hi - base + lo  # invert

        elif trend == "crisis_then_improving":
            if t < 0.3:
                # Crisis phase — bad values
                if lower_is_better:
                    base = hi * 0.8
                else:
                    base = lo + (hi - lo) * 0.15
            else:
                # Recovery
                recovery_t = (t - 0.3) / 0.7
                if lower_is_better:
                    base = hi * 0.8 - (hi * 0.5) * recovery_t
                else:
                    base = lo + (hi - lo) * (0.15 + 0.55 * recovery_t)

        elif trend == "stable":
            if lower_is_better:
                base = lo + (hi - lo) * 0.2
            else:
                base = lo + (hi - lo) * 0.75

        else:
            base = lo + (hi - lo) * 0.5

        # Add noise (±10% of range)
        noise = (hi - lo) * 0.08 * (random.random() - 0.5)
        val = base + noise
        val = max(lo, min(hi, val))

        # Round appropriately
        if metric_def.unit in ("days", "nights", "hours", "applications"):
            val = int(round(val))
        elif metric_def.unit == "$":
            val = round(val / 50) * 50  # round to nearest $50
        elif metric_def.unit == "%":
            val = round(val)
        else:
            val = round(val, 1)

        values.append(val)

    return values


# Events to create per client
CLIENT_EVENTS = {
    # Demo Program clients
    "DEMO-001": [
        {"type": "Intake", "title": "Initial intake assessment", "days_ago": 175},
        {"type": "Follow-up", "title": "30-day check-in", "days_ago": 145},
        {"type": "Follow-up", "title": "60-day check-in", "days_ago": 115},
        {"type": "Referral", "title": "Referred to employment services", "days_ago": 90},
    ],
    "DEMO-002": [
        {"type": "Intake", "title": "Initial intake — shelter referral", "days_ago": 180},
        {"type": "Crisis", "title": "Housing crisis — eviction notice", "days_ago": 140},
        {"type": "Follow-up", "title": "Housing search update", "days_ago": 100},
        {"type": "Follow-up", "title": "Monthly review", "days_ago": 60},
        {"type": "Referral", "title": "Referred to mental health services", "days_ago": 30},
    ],
    "DEMO-003": [
        {"type": "Intake", "title": "Program intake", "days_ago": 170},
        {"type": "Follow-up", "title": "Substance use check-in", "days_ago": 120},
        {"type": "Follow-up", "title": "Employment readiness review", "days_ago": 70},
        {"type": "Referral", "title": "Referred to peer support group", "days_ago": 40},
    ],
    "DEMO-004": [
        {"type": "Intake", "title": "Youth intake assessment", "days_ago": 165},
        {"type": "Crisis", "title": "School suspension incident", "days_ago": 130},
        {"type": "Follow-up", "title": "Post-crisis follow-up", "days_ago": 120},
        {"type": "Follow-up", "title": "Family meeting", "days_ago": 80},
        {"type": "Follow-up", "title": "Quarterly progress review", "days_ago": 20},
    ],
    "DEMO-005": [
        {"type": "Intake", "title": "Initial intake", "days_ago": 180},
        {"type": "Follow-up", "title": "90-day review", "days_ago": 90},
        {"type": "Follow-up", "title": "Discharge planning meeting", "days_ago": 15},
    ],
    # Youth Services clients
    "DEMO-006": [
        {"type": "Intake", "title": "Youth Services intake", "days_ago": 120},
        {"type": "Follow-up", "title": "School liaison meeting", "days_ago": 90},
        {"type": "Follow-up", "title": "Progress review", "days_ago": 45},
    ],
    "DEMO-007": [
        {"type": "Intake", "title": "Initial intake assessment", "days_ago": 150},
        {"type": "Crisis", "title": "Panic attack at school", "days_ago": 130},
        {"type": "Follow-up", "title": "Post-crisis support session", "days_ago": 125},
        {"type": "Follow-up", "title": "Monthly check-in", "days_ago": 60},
        {"type": "Follow-up", "title": "Group activity participation", "days_ago": 25},
    ],
    "DEMO-008": [
        {"type": "Intake", "title": "Family referral intake", "days_ago": 140},
        {"type": "Follow-up", "title": "Family mediation session", "days_ago": 110},
        {"type": "Crisis", "title": "Ran away from home overnight", "days_ago": 85},
        {"type": "Follow-up", "title": "Safety planning session", "days_ago": 80},
        {"type": "Follow-up", "title": "Monthly review", "days_ago": 30},
    ],
    "DEMO-009": [
        {"type": "Intake", "title": "Self-referral intake", "days_ago": 160},
        {"type": "Follow-up", "title": "Leadership workshop participation", "days_ago": 100},
        {"type": "Follow-up", "title": "Post-secondary planning meeting", "days_ago": 55},
        {"type": "Referral", "title": "Referred to career counselling", "days_ago": 30},
    ],
    "DEMO-010": [
        {"type": "Intake", "title": "Program intake", "days_ago": 180},
        {"type": "Follow-up", "title": "Life skills assessment", "days_ago": 120},
        {"type": "Follow-up", "title": "Employment support session", "days_ago": 60},
        {"type": "Follow-up", "title": "Transition planning meeting", "days_ago": 20},
    ],
}

# Custom field values for demo clients (Contact, Emergency, Referral)
# Field names must match those in seed_intake_fields.py
CLIENT_CUSTOM_FIELDS = {
    "DEMO-001": {
        # Contact Information
        "Preferred Name": "Jordan",
        "Primary Phone": "(416) 555-0123",
        "Email": "jordan.rivera@example.com",
        "Preferred Contact Method": "Text message",
        "Best Time to Contact": "Afternoon (12pm-5pm)",
        "Preferred Language of Service": "English",
        # Emergency Contact
        "Emergency Contact Name": "Maria Rivera",
        "Emergency Contact Relationship": "Parent/Guardian",
        "Emergency Contact Phone": "(416) 555-0124",
        # Referral
        "Referral Source": "Community agency",
        "Referring Agency Name": "Downtown Community Health Centre",
    },
    "DEMO-002": {
        "Preferred Name": "Taylor",
        "Primary Phone": "(647) 555-0234",
        "Preferred Contact Method": "Phone call",
        "Best Time to Contact": "Morning (9am-12pm)",
        "Preferred Language of Service": "English",
        "Emergency Contact Name": "Alex Chen",
        "Emergency Contact Relationship": "Friend",
        "Emergency Contact Phone": "(647) 555-0235",
        "Referral Source": "Shelter/Housing provider",
        "Referring Agency Name": "Covenant House",
        # Accessibility
        "Accommodation Needs": "Prefers written appointment reminders",
    },
    "DEMO-003": {
        "Preferred Name": "Avery",
        "Primary Phone": "(905) 555-0345",
        "Email": "avery.j@example.com",
        "Preferred Contact Method": "Email",
        "Best Time to Contact": "Any time",
        "Preferred Language of Service": "English",
        "Emergency Contact Name": "Jamie Johnson",
        "Emergency Contact Relationship": "Sibling",
        "Emergency Contact Phone": "(905) 555-0346",
        "Referral Source": "Hospital/Health provider",
        "Referring Agency Name": "CAMH",
    },
    "DEMO-004": {
        "Primary Phone": "(416) 555-0456",
        "Preferred Contact Method": "Text message",
        "Best Time to Contact": "Evening (5pm-8pm)",
        "Preferred Language of Service": "English",
        "Emergency Contact Name": "Priya Patel",
        "Emergency Contact Relationship": "Parent/Guardian",
        "Emergency Contact Phone": "(416) 555-0457",
        "Referral Source": "School/Education",
        "Referring Agency Name": "Toronto District School Board",
    },
    "DEMO-005": {
        "Preferred Name": "Sam",
        "Primary Phone": "(647) 555-0567",
        "Email": "sam.williams@example.com",
        "Preferred Contact Method": "Email",
        "Best Time to Contact": "Any time",
        "Preferred Language of Service": "English",
        "Emergency Contact Name": "Drew Williams",
        "Emergency Contact Relationship": "Spouse/Partner",
        "Emergency Contact Phone": "(647) 555-0568",
        "Referral Source": "Self-referral",
    },
    "DEMO-006": {
        "Primary Phone": "(416) 555-0678",
        "Preferred Contact Method": "Text message",
        "Best Time to Contact": "Afternoon (12pm-5pm)",
        "Preferred Language of Service": "English",
        "Emergency Contact Name": "Rosa Martinez",
        "Emergency Contact Relationship": "Parent/Guardian",
        "Emergency Contact Phone": "(416) 555-0679",
        "Referral Source": "School/Education",
    },
    "DEMO-007": {
        "Preferred Name": "Maya",
        "Primary Phone": "(905) 555-0789",
        "Preferred Contact Method": "Phone call",
        "Best Time to Contact": "Morning (9am-12pm)",
        "Preferred Language of Service": "English",
        "Emergency Contact Name": "David Thompson",
        "Emergency Contact Relationship": "Parent/Guardian",
        "Emergency Contact Phone": "(905) 555-0790",
        "Referral Source": "Hospital/Health provider",
        "Accommodation Needs": "Needs quiet space for meetings; social anxiety",
    },
    "DEMO-008": {
        "Primary Phone": "(647) 555-0890",
        "Preferred Contact Method": "Text message",
        "Best Time to Contact": "Evening (5pm-8pm)",
        "Preferred Language of Service": "English",
        "Emergency Contact Name": "Lisa Nguyen",
        "Emergency Contact Relationship": "Parent/Guardian",
        "Emergency Contact Phone": "(647) 555-0891",
        "Referral Source": "Social services (OW/ODSP)",
    },
    "DEMO-009": {
        "Preferred Name": "Zara",
        "Primary Phone": "(416) 555-0901",
        "Email": "zara.a@example.com",
        "Preferred Contact Method": "Email",
        "Best Time to Contact": "Afternoon (12pm-5pm)",
        "Preferred Language of Service": "English",
        "Emergency Contact Name": "Fatima Ahmed",
        "Emergency Contact Relationship": "Parent/Guardian",
        "Emergency Contact Phone": "(416) 555-0902",
        "Referral Source": "Self-referral",
    },
    "DEMO-010": {
        "Preferred Name": "Liam",
        "Primary Phone": "(905) 555-1012",
        "Email": "liam.oconnor@example.com",
        "Preferred Contact Method": "Phone call",
        "Best Time to Contact": "Any time",
        "Preferred Language of Service": "English",
        "Emergency Contact Name": "Patrick O'Connor",
        "Emergency Contact Relationship": "Parent/Guardian",
        "Emergency Contact Phone": "(905) 555-1013",
        "Referral Source": "Community agency",
        "Referring Agency Name": "Youth Employment Services",
    },
}


class Command(BaseCommand):
    help = "Populate demo clients with plans, notes, events, and alerts for charts/reports."

    def handle(self, *args, **options):
        if not settings.DEMO_MODE:
            self.stdout.write(self.style.WARNING("DEMO_MODE is not enabled. Skipping."))
            return

        # Check if data already exists (idempotent guard)
        if ProgressNote.objects.filter(client_file__record_id__startswith="DEMO-").exists():
            self.stdout.write("  Demo rich data already exists. Skipping.")
            return

        # Fetch shared resources
        try:
            counsellor = User.objects.get(username="demo-counsellor")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("demo-counsellor user not found. Run seed first."))
            return

        try:
            manager = User.objects.get(username="demo-manager")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("demo-manager user not found. Run seed first."))
            return

        # Fetch both programs
        programs_by_name = {p.name: p for p in Program.objects.all()}
        if "Demo Program" not in programs_by_name:
            self.stdout.write(self.style.ERROR("Demo Program not found. Run seed first."))
            return
        if "Youth Services" not in programs_by_name:
            self.stdout.write(self.style.ERROR("Youth Services not found. Run seed first."))
            return

        # Map programs to their note authors:
        # - Demo Program notes written by demo-counsellor
        # - Youth Services notes written by demo-manager (counsellor doesn't have access)
        program_authors = {
            "Demo Program": counsellor,
            "Youth Services": manager,
        }

        # Cache metric definitions by name
        metrics_by_name = {m.name: m for m in MetricDefinition.objects.filter(is_library=True)}

        # Cache event types by name
        event_types = {et.name: et for et in EventType.objects.all()}

        now = timezone.now()
        random.seed(42)  # Reproducible demo data

        for record_id, plan_config in CLIENT_PLANS.items():
            client = ClientFile.objects.filter(record_id=record_id).first()
            if not client:
                self.stdout.write(self.style.WARNING(f"  Client {record_id} not found. Skipping."))
                continue

            # Get the program and author for this client
            program_name = plan_config.get("program", "Demo Program")
            program = programs_by_name.get(program_name)
            author = program_authors.get(program_name, counsellor)

            if not program:
                self.stdout.write(self.style.WARNING(f"  Program '{program_name}' not found. Skipping {record_id}."))
                continue

            self.stdout.write(f"  Seeding {record_id}: {plan_config['label']} ({program_name})...")

            # ----------------------------------------------------------
            # 1. Create plan sections, targets, and link metrics
            # ----------------------------------------------------------
            all_targets = []  # [(PlanTarget, [MetricDefinition, ...])]

            for s_idx, section_data in enumerate(plan_config["sections"]):
                section = PlanSection.objects.create(
                    client_file=client,
                    name=section_data["name"],
                    program=program,
                    sort_order=s_idx,
                )

                for t_idx, target_data in enumerate(section_data["targets"]):
                    target = PlanTarget.objects.create(
                        plan_section=section,
                        client_file=client,
                        name=target_data["name"],
                        description=target_data["desc"],
                        sort_order=t_idx,
                    )

                    # Create initial revision
                    PlanTargetRevision.objects.create(
                        plan_target=target,
                        name=target.name,
                        description=target.description,
                        status="default",
                        changed_by=author,
                    )

                    # Link metrics
                    target_metrics = []
                    for m_idx, metric_name in enumerate(target_data["metrics"]):
                        metric_def = metrics_by_name.get(metric_name)
                        if metric_def:
                            PlanTargetMetric.objects.create(
                                plan_target=target,
                                metric_def=metric_def,
                                sort_order=m_idx,
                            )
                            target_metrics.append(metric_def)
                        else:
                            self.stdout.write(
                                self.style.WARNING(f"    Metric '{metric_name}' not found.")
                            )

                    all_targets.append((target, target_metrics))

            # ----------------------------------------------------------
            # 2. Create progress notes with metric recordings
            # ----------------------------------------------------------
            note_count = plan_config["note_count"]
            trend = plan_config["trend"]

            # Spread notes over 180 days (6 months)
            note_days = sorted(
                [random.randint(5, 175) for _ in range(note_count)], reverse=True
            )

            # Pre-generate metric value sequences
            metric_value_sequences = {}
            for target, target_metrics in all_targets:
                for md in target_metrics:
                    key = (target.pk, md.pk)
                    metric_value_sequences[key] = _generate_trend_values(
                        trend, note_count, md.name, md
                    )

            for note_idx, days_ago in enumerate(note_days):
                is_quick = note_idx % 3 == 0  # ~1/3 quick notes
                note_type = "quick" if is_quick else "full"
                backdate = now - timedelta(days=days_ago, hours=random.randint(8, 17))

                note = ProgressNote.objects.create(
                    client_file=client,
                    note_type=note_type,
                    author=author,
                    author_program=program,
                    backdate=backdate,
                    notes_text=(
                        random.choice(QUICK_NOTE_TEXTS) if is_quick else ""
                    ),
                    summary=(
                        "" if is_quick else random.choice(FULL_NOTE_SUMMARIES)
                    ),
                )

                # For full notes, record metrics against each target
                if not is_quick:
                    for target, target_metrics in all_targets:
                        pnt = ProgressNoteTarget.objects.create(
                            progress_note=note,
                            plan_target=target,
                            notes=random.choice(FULL_NOTE_SUMMARIES),
                        )

                        for md in target_metrics:
                            key = (target.pk, md.pk)
                            seq = metric_value_sequences[key]
                            val = seq[note_idx] if note_idx < len(seq) else seq[-1]
                            MetricValue.objects.create(
                                progress_note_target=pnt,
                                metric_def=md,
                                value=str(val),
                            )

            # ----------------------------------------------------------
            # 3. Create events
            # ----------------------------------------------------------
            for evt_data in CLIENT_EVENTS.get(record_id, []):
                et = event_types.get(evt_data["type"])
                if not et:
                    continue
                Event.objects.create(
                    client_file=client,
                    title=evt_data["title"],
                    event_type=et,
                    author_program=program,
                    start_timestamp=now - timedelta(days=evt_data["days_ago"]),
                )

            # ----------------------------------------------------------
            # 4. Create alerts (for selected clients)
            # ----------------------------------------------------------
            if record_id == "DEMO-002":
                Alert.objects.create(
                    client_file=client,
                    content="Housing instability — currently staying in emergency shelter. Check in weekly.",
                    author=author,
                    author_program=program,
                )
            elif record_id == "DEMO-004":
                Alert.objects.create(
                    client_file=client,
                    content="Safety concern flagged during school suspension. Updated safety plan on file.",
                    author=author,
                    author_program=program,
                )
            elif record_id == "DEMO-007":
                Alert.objects.create(
                    client_file=client,
                    content="Social anxiety — avoid large group settings initially. Build up gradually.",
                    author=author,
                    author_program=program,
                )
            elif record_id == "DEMO-008":
                Alert.objects.create(
                    client_file=client,
                    content="Family conflict — youth has run away before. Maintain weekly contact.",
                    author=author,
                    author_program=program,
                )

            # ----------------------------------------------------------
            # 5. Populate custom field values (contact, emergency, referral)
            # ----------------------------------------------------------
            custom_values = CLIENT_CUSTOM_FIELDS.get(record_id, {})
            for field_name, value in custom_values.items():
                try:
                    field_def = CustomFieldDefinition.objects.get(name=field_name)
                    cdv, _ = ClientDetailValue.objects.get_or_create(
                        client_file=client,
                        field_def=field_def,
                    )
                    cdv.set_value(value)
                    cdv.save()
                except CustomFieldDefinition.DoesNotExist:
                    # Field may not exist if seed_intake_fields wasn't run
                    pass

        self.stdout.write(self.style.SUCCESS("  Demo rich data seeded successfully (10 clients across 2 programs)."))

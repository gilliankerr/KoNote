"""AI-powered HTMX endpoints — all POST, all rate-limited, no PII."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit

from apps.admin_settings.models import FeatureToggle
from konote import ai
from konote.forms import (
    GenerateNarrativeForm,
    ImproveOutcomeForm,
    SuggestMetricsForm,
    SuggestNoteStructureForm,
)


def _ai_enabled():
    """Check both the feature toggle and the API key."""
    if not ai.is_ai_available():
        return False
    return FeatureToggle.get_all_flags().get("ai_assist", False)


@login_required
@ratelimit(key="user", rate="20/h", method="POST", block=True)
def suggest_metrics_view(request):
    """Suggest metrics for a plan target description."""
    if not _ai_enabled():
        return HttpResponseForbidden("AI features are not enabled.")

    form = SuggestMetricsForm(request.POST)
    if not form.is_valid():
        return render(request, "ai/_error.html", {"message": "Please enter a target description first."})
    target_description = form.cleaned_data["target_description"]

    # Build catalogue from non-PII metric data
    from apps.plans.models import MetricDefinition

    metrics = list(
        MetricDefinition.objects.filter(is_enabled=True, status="active").values(
            "id", "name", "definition", "category"
        )
    )

    suggestions = ai.suggest_metrics(target_description, metrics)
    if suggestions is None:
        return render(request, "ai/_error.html", {"message": "AI suggestion unavailable. Please try again later."})

    return render(request, "ai/_metric_suggestions.html", {"suggestions": suggestions})


@login_required
@ratelimit(key="user", rate="20/h", method="POST", block=True)
def improve_outcome_view(request):
    """Improve a draft outcome statement."""
    if not _ai_enabled():
        return HttpResponseForbidden("AI features are not enabled.")

    form = ImproveOutcomeForm(request.POST)
    if not form.is_valid():
        return render(request, "ai/_error.html", {"message": "Please enter a draft outcome first."})
    draft_text = form.cleaned_data["draft_text"]

    improved = ai.improve_outcome(draft_text)
    if improved is None:
        return render(request, "ai/_error.html", {"message": "AI suggestion unavailable. Please try again later."})

    return render(request, "ai/_improved_outcome.html", {"improved_text": improved, "original_text": draft_text})


@login_required
@ratelimit(key="user", rate="20/h", method="POST", block=True)
def generate_narrative_view(request):
    """Generate a funder narrative from aggregate metrics."""
    if not _ai_enabled():
        return HttpResponseForbidden("AI features are not enabled.")

    from apps.notes.models import MetricValue
    from apps.programs.models import Program

    form = GenerateNarrativeForm(request.POST)
    if not form.is_valid():
        return render(request, "ai/_error.html", {"message": "Please select a programme and date range."})

    program_id = form.cleaned_data["program_id"]
    date_from = form.cleaned_data["date_from"]
    date_to = form.cleaned_data["date_to"]

    try:
        program = Program.objects.get(pk=program_id)
    except Program.DoesNotExist:
        return HttpResponseBadRequest("Programme not found.")

    # Build aggregate stats from metric values — no PII, just numbers
    values = (
        MetricValue.objects.filter(
            progress_note_target__progress_note__client_file__enrolments__program=program,
            progress_note_target__progress_note__client_file__enrolments__status="enrolled",
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        .select_related("metric_def")
    )

    # Aggregate by metric
    from collections import defaultdict

    aggregates = defaultdict(lambda: {"total": 0.0, "count": 0})
    for mv in values:
        try:
            num = float(mv.value)
        except (ValueError, TypeError):
            continue
        key = mv.metric_def.name
        aggregates[key]["total"] += num
        aggregates[key]["count"] += 1
        aggregates[key]["unit"] = mv.metric_def.unit

    aggregate_stats = [
        {
            "metric_name": name,
            "average": round(data["total"] / data["count"], 1) if data["count"] else 0,
            "count": data["count"],
            "unit": data.get("unit", ""),
        }
        for name, data in aggregates.items()
    ]

    if not aggregate_stats:
        return render(request, "ai/_error.html", {"message": "No metric data found for this period."})

    date_range = f"{date_from} to {date_to}"
    narrative = ai.generate_narrative(program.name, date_range, aggregate_stats)
    if narrative is None:
        return render(request, "ai/_error.html", {"message": "AI narrative unavailable. Please try again later."})

    return render(request, "ai/_narrative.html", {"narrative": narrative, "program_name": program.name})


@login_required
@ratelimit(key="user", rate="20/h", method="POST", block=True)
def suggest_note_structure_view(request):
    """Suggest a progress note structure for a plan target."""
    if not _ai_enabled():
        return HttpResponseForbidden("AI features are not enabled.")

    from apps.plans.models import PlanTarget

    form = SuggestNoteStructureForm(request.POST)
    if not form.is_valid():
        return render(request, "ai/_error.html", {"message": "No target selected."})

    try:
        target = PlanTarget.objects.get(pk=form.cleaned_data["target_id"])
    except PlanTarget.DoesNotExist:
        return HttpResponseBadRequest("Target not found.")

    metric_names = list(target.metrics.filter(status="active").values_list("name", flat=True))

    sections = ai.suggest_note_structure(target.name, target.description, metric_names)
    if sections is None:
        return render(request, "ai/_error.html", {"message": "AI suggestion unavailable. Please try again later."})

    return render(request, "ai/_note_structure.html", {"sections": sections, "target_name": target.name})

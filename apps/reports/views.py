"""Report views — aggregate metric CSV export."""
import csv
from datetime import datetime, time

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.clients.models import ClientProgramEnrolment
from apps.notes.models import MetricValue, ProgressNote
from .forms import MetricExportForm


@login_required
def export_form(request):
    """
    GET  — display the export filter form.
    POST — validate, query metric values, and return a CSV download.
    """
    if not request.user.is_admin:
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method != "POST":
        form = MetricExportForm()
        return render(request, "reports/export_form.html", {"form": form})

    form = MetricExportForm(request.POST)
    if not form.is_valid():
        return render(request, "reports/export_form.html", {"form": form})

    program = form.cleaned_data["program"]
    selected_metrics = form.cleaned_data["metrics"]
    date_from = form.cleaned_data["date_from"]
    date_to = form.cleaned_data["date_to"]

    # Find clients enrolled in the selected programme
    client_ids = ClientProgramEnrolment.objects.filter(
        program=program, status="enrolled",
    ).values_list("client_file_id", flat=True)

    # Build date-aware boundaries
    date_from_dt = timezone.make_aware(datetime.combine(date_from, time.min))
    date_to_dt = timezone.make_aware(datetime.combine(date_to, time.max))

    # Filter progress notes by effective date (backdate when present, else created_at)
    notes = ProgressNote.objects.filter(
        client_file_id__in=client_ids,
        status="default",
    ).filter(
        Q(backdate__range=(date_from_dt, date_to_dt))
        | Q(backdate__isnull=True, created_at__range=(date_from_dt, date_to_dt))
    )

    # Get the actual metric values
    metric_values = (
        MetricValue.objects.filter(
            metric_def__in=selected_metrics,
            progress_note_target__progress_note__in=notes,
        )
        .select_related(
            "metric_def",
            "progress_note_target__progress_note__client_file",
            "progress_note_target__progress_note__author",
        )
    )

    if not metric_values.exists():
        return render(
            request,
            "reports/export_form.html",
            {
                "form": form,
                "no_data": True,
            },
        )

    # Count unique clients in the result set
    unique_clients = set()
    rows = []
    for mv in metric_values:
        note = mv.progress_note_target.progress_note
        client = note.client_file
        unique_clients.add(client.pk)
        rows.append(
            {
                "record_id": client.record_id,
                "metric_name": mv.metric_def.name,
                "value": mv.value,
                "date": note.effective_date.strftime("%Y-%m-%d"),
                "author": note.author.display_name,
            }
        )

    # Build CSV response
    response = HttpResponse(content_type="text/csv")
    filename = f"metric_export_{program.name.replace(' ', '_')}_{date_from}_{date_to}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    # Summary header rows (prefixed with # so spreadsheet apps treat them as comments)
    writer.writerow([f"# Programme: {program.name}"])
    writer.writerow([f"# Date Range: {date_from} to {date_to}"])
    writer.writerow([f"# Total Clients: {len(unique_clients)}"])
    writer.writerow([f"# Total Data Points: {len(rows)}"])
    writer.writerow([])  # blank separator

    # Column headers
    writer.writerow(["Client Record ID", "Metric Name", "Value", "Date", "Author"])

    for row in rows:
        writer.writerow([
            row["record_id"],
            row["metric_name"],
            row["value"],
            row["date"],
            row["author"],
        ])

    # Audit log
    AuditLog.objects.using("audit").create(
        event_timestamp=timezone.now(),
        user_id=request.user.pk,
        user_display=request.user.display_name,
        action="export",
        resource_type="metric_report",
        metadata={
            "program": program.name,
            "metrics": [m.name for m in selected_metrics],
            "date_from": str(date_from),
            "date_to": str(date_to),
            "total_clients": len(unique_clients),
            "total_data_points": len(rows),
        },
    )

    return response

"""Audit log viewer — admin only."""
import csv
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from apps.reports.csv_utils import sanitise_csv_row

from .models import AuditLog


@login_required
def audit_log_list(request):
    """Display paginated, filterable audit log."""
    if not request.user.is_admin:
        return HttpResponseForbidden("Access denied. Admin privileges required.")

    qs = AuditLog.objects.using("audit").all()

    # Collect filter values
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    user_display = request.GET.get("user_display", "")
    action = request.GET.get("action", "")
    resource_type = request.GET.get("resource_type", "")
    demo_filter = request.GET.get("demo_filter", "")

    # Apply filters
    if demo_filter == "real":
        qs = qs.filter(is_demo_context=False)
    elif demo_filter == "demo":
        qs = qs.filter(is_demo_context=True)

    if date_from:
        try:
            dt = datetime.strptime(date_from, "%Y-%m-%d")
            qs = qs.filter(event_timestamp__gte=timezone.make_aware(dt))
        except ValueError:
            pass

    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d")
            # Include the entire day
            dt = dt.replace(hour=23, minute=59, second=59)
            qs = qs.filter(event_timestamp__lte=timezone.make_aware(dt))
        except ValueError:
            pass

    if user_display:
        qs = qs.filter(user_display__icontains=user_display)

    if action:
        qs = qs.filter(action=action)

    if resource_type:
        qs = qs.filter(resource_type__icontains=resource_type)

    # Build filter query string for pagination links (exclude 'page')
    filter_params = []
    for key in ("date_from", "date_to", "user_display", "action", "resource_type", "demo_filter"):
        val = request.GET.get(key, "")
        if val:
            filter_params.append(f"{key}={val}")
    filter_query = "&".join(filter_params)

    # Paginate
    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    context = {
        "page": page,
        "filter_query": filter_query,
        "action_choices": AuditLog.ACTION_CHOICES,
        # Sticky filter values
        "date_from": date_from,
        "date_to": date_to,
        "user_display": user_display,
        "action_filter": action,
        "resource_type": resource_type,
        "demo_filter": demo_filter,
    }
    return render(request, "audit/log_list.html", context)


@login_required
def audit_log_export(request):
    """Export filtered audit log as CSV."""
    if not request.user.is_admin:
        return HttpResponseForbidden("Access denied. Admin privileges required.")

    qs = AuditLog.objects.using("audit").all()

    # Apply same filters as list view
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    user_display = request.GET.get("user_display", "")
    action = request.GET.get("action", "")
    resource_type = request.GET.get("resource_type", "")
    demo_filter = request.GET.get("demo_filter", "")

    if demo_filter == "real":
        qs = qs.filter(is_demo_context=False)
    elif demo_filter == "demo":
        qs = qs.filter(is_demo_context=True)

    if date_from:
        try:
            dt = datetime.strptime(date_from, "%Y-%m-%d")
            qs = qs.filter(event_timestamp__gte=timezone.make_aware(dt))
        except ValueError:
            pass

    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d")
            dt = dt.replace(hour=23, minute=59, second=59)
            qs = qs.filter(event_timestamp__lte=timezone.make_aware(dt))
        except ValueError:
            pass

    if user_display:
        qs = qs.filter(user_display__icontains=user_display)

    if action:
        qs = qs.filter(action=action)

    if resource_type:
        qs = qs.filter(resource_type__icontains=resource_type)

    # Build CSV response
    today = timezone.now().strftime("%Y-%m-%d")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="audit_log_{today}.csv"'

    writer = csv.writer(response)
    writer.writerow(sanitise_csv_row(["Timestamp", "User", "IP Address", "Action", "Resource Type", "Resource ID", "Program ID", "Demo Context"]))

    for entry in qs.iterator():
        writer.writerow(sanitise_csv_row([
            entry.event_timestamp.strftime("%Y-%m-%d %H:%M"),
            entry.user_display,
            entry.ip_address or "",
            entry.action,
            entry.resource_type,
            entry.resource_id or "",
            entry.program_id or "",
            "Yes" if entry.is_demo_context else "No",
        ]))

    # Log the export action
    filters_used = {k: v for k, v in {
        "date_from": date_from, "date_to": date_to,
        "user_display": user_display, "action": action,
        "resource_type": resource_type,
    }.items() if v}

    AuditLog.objects.using("audit").create(
        event_timestamp=timezone.now(),
        user_id=request.user.pk,
        user_display=getattr(request.user, "display_name", str(request.user)),
        action="export",
        resource_type="audit_log",
        is_demo_context=getattr(request.user, "is_demo", False),
        metadata={"filters": filters_used},
    )

    return response

"""PDF generation utilities using WeasyPrint.

WeasyPrint requires native GTK libraries. If not installed, PDF features
will be disabled but the rest of the application will work normally.
See docs/pdf-setup.md for installation instructions.
"""
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from apps.audit.models import AuditLog

# Conditional import: WeasyPrint requires GTK libraries that may not be available
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    _WEASYPRINT_ERROR = str(e)


def is_pdf_available():
    """Check if PDF generation is available."""
    return WEASYPRINT_AVAILABLE


def get_pdf_unavailable_reason():
    """Return the reason PDF generation is unavailable."""
    if WEASYPRINT_AVAILABLE:
        return None
    return _WEASYPRINT_ERROR


def render_pdf(template_name, context, filename="report.pdf"):
    """Render a Django template to a PDF HttpResponse.

    Raises RuntimeError if WeasyPrint is not available.
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            f"PDF generation requires WeasyPrint with GTK libraries. "
            f"Error: {_WEASYPRINT_ERROR}"
        )

    html_string = render_to_string(template_name, context)
    # Use STATIC_ROOT as base_url so WeasyPrint can resolve {% static %} paths
    base_url = getattr(settings, "STATIC_ROOT", None) or "."
    pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf()
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def audit_pdf_export(request, action, resource_type, metadata):
    """Create an audit log entry for a PDF export."""
    AuditLog.objects.using("audit").create(
        event_timestamp=timezone.now(),
        user_id=request.user.pk,
        user_display=request.user.display_name,
        action=action,
        resource_type=resource_type,
        is_demo_context=getattr(request.user, "is_demo", False),
        metadata=metadata,
    )

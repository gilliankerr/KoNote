"""Custom error handlers that render styled error pages."""

from django.template.response import TemplateResponse


def permission_denied_view(request, exception):
    """
    Custom 403 handler that renders a styled error page.

    Django calls this when a PermissionDenied exception is raised.
    The middleware handles its own 403s with _forbidden_response().
    """
    # Get the exception message if available
    message = str(exception) if exception else None

    return TemplateResponse(
        request,
        "403.html",
        {"exception": message},
        status=403,
    )

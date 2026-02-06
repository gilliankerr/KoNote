"""Audit logging middleware — logs state-changing requests and client views."""
import logging
import re

from django.utils import timezone

logger = logging.getLogger(__name__)

# HTTP methods that change state
AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# URL patterns for client record views (GET requests to log for compliance)
CLIENT_VIEW_PATTERNS = [
    re.compile(r"^/clients/(\d+)/?$"),  # /clients/123/
    re.compile(r"^/clients/(\d+)/"),     # /clients/123/anything
]


class AuditMiddleware:
    """
    Automatically log HTTP requests to the audit database.

    Logs:
    - All state-changing requests (POST/PUT/PATCH/DELETE)
    - Client record views (GET /clients/<id>) for compliance

    Captures: user, action, path, IP address, timestamp.
    Detailed field-level changes are logged via model signals in the audit app.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not hasattr(request, "user") or not request.user.is_authenticated:
            return response

        # Only log successful requests
        if response.status_code >= 400:
            return response

        # Log state-changing requests
        if request.method in AUDITABLE_METHODS:
            self._log_request(request, response, action=request.method.lower())

        # Log client record views for compliance (PIPEDA, healthcare regs)
        elif request.method == "GET" and self._is_client_view(request.path):
            self._log_request(request, response, action="view")

        return response

    def _is_client_view(self, path):
        """Check if path is a client record view."""
        for pattern in CLIENT_VIEW_PATTERNS:
            if pattern.match(path):
                return True
        return False

    def _log_request(self, request, response, action):
        """Write an audit log entry."""
        try:
            from apps.audit.models import AuditLog

            AuditLog.objects.using("audit").create(
                event_timestamp=timezone.now(),
                user_id=request.user.id,
                user_display=request.user.get_display_name(),
                ip_address=self._get_client_ip(request),
                action=action,
                resource_type=self._extract_resource_type(request.path),
                resource_id=self._extract_resource_id(request.path),
                is_demo_context=getattr(request.user, "is_demo", False),
                metadata={
                    "path": request.path,
                    "status_code": response.status_code,
                },
            )
        except Exception as e:
            # Audit logging should never break the application, but log the failure
            logger.error("Audit logging failed for %s %s: %s", request.method, request.path, e)

    def _get_client_ip(self, request):
        """Get client IP, respecting X-Forwarded-For from reverse proxy."""
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    def _extract_resource_type(self, path):
        """Extract resource type from URL path (e.g., /clients/5/ -> client)."""
        parts = [p for p in path.strip("/").split("/") if p]
        return parts[0] if parts else "unknown"

    def _extract_resource_id(self, path):
        """Extract numeric resource ID from URL path if present."""
        parts = path.strip("/").split("/")
        for part in parts:
            if part.isdigit():
                return int(part)
        return None

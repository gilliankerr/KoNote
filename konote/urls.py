"""URL configuration for KoNote2 Web."""
from django.contrib import admin
from django.urls import include, path

from apps.auth_app.views import switch_language
from konote.error_views import permission_denied_view

# Custom error handlers
handler403 = permission_denied_view

urlpatterns = [
    # Internationalization - language switching
    path("i18n/", include("django.conf.urls.i18n")),
    path("i18n/switch/", switch_language, name="switch_language"),
    path("auth/", include("apps.auth_app.urls")),
    path("clients/", include("apps.clients.urls")),
    path("programs/", include("apps.programs.urls")),
    path("plans/", include("apps.plans.urls")),
    path("admin/templates/", include("apps.plans.admin_urls")),
    path("notes/", include("apps.notes.urls")),
    path("events/", include("apps.events.urls")),
    path("reports/", include("apps.reports.urls")),
    path("admin/settings/note-templates/", include("apps.notes.admin_urls")),
    path("admin/settings/", include("apps.admin_settings.urls")),
    path("admin/users/", include("apps.auth_app.admin_urls")),
    path("admin/audit/", include("apps.audit.urls")),
    path("ai/", include("konote.ai_urls")),
    path("", include("apps.registration.urls")),
    path("", include("apps.clients.urls_home")),
    path("django-admin/", admin.site.urls),
]

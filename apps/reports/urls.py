from django.urls import path

from . import views
from . import pdf_views

app_name = "reports"
urlpatterns = [
    path("export/", views.export_form, name="export_form"),
    path("cmt-export/", views.cmt_export_form, name="cmt_export"),
    path("client-data-export/", views.client_data_export, name="client_data_export"),
    path("client/<int:client_id>/analysis/", views.client_analysis, name="client_analysis"),
    path("client/<int:client_id>/pdf/", pdf_views.client_progress_pdf, name="client_progress_pdf"),
    # Secure export links
    path("download/<uuid:link_id>/", views.download_export, name="download_export"),
    path("export-links/", views.manage_export_links, name="manage_export_links"),
    path("export-links/<uuid:link_id>/revoke/", views.revoke_export_link, name="revoke_export_link"),
]

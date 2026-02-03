from django.urls import path

from . import views
from . import pdf_views

app_name = "reports"
urlpatterns = [
    path("export/", views.export_form, name="export_form"),
    path("cmt-export/", views.cmt_export_form, name="cmt_export"),
    path("client/<int:client_id>/analysis/", views.client_analysis, name="client_analysis"),
    path("client/<int:client_id>/pdf/", pdf_views.client_progress_pdf, name="client_progress_pdf"),
]

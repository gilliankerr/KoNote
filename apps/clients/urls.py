from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="client_list"),
    path("create/", views.client_create, name="client_create"),
    path("search/", views.client_search, name="client_search"),
    path("<int:client_id>/", views.client_detail, name="client_detail"),
    path("<int:client_id>/edit/", views.client_edit, name="client_edit"),
    path("<int:client_id>/custom-fields/", views.client_save_custom_fields, name="client_save_custom_fields"),
    path("<int:client_id>/custom-fields/display/", views.client_custom_fields_display, name="client_custom_fields_display"),
    path("<int:client_id>/custom-fields/edit/", views.client_custom_fields_edit, name="client_custom_fields_edit"),
    # Consent recording (PRIV1)
    path("<int:client_id>/consent/display/", views.client_consent_display, name="client_consent_display"),
    path("<int:client_id>/consent/edit/", views.client_consent_edit, name="client_consent_edit"),
    path("<int:client_id>/consent/", views.client_consent_save, name="client_consent_save"),
    # Custom field admin (FIELD1)
    path("admin/fields/", views.custom_field_admin, name="custom_field_admin"),
    path("admin/fields/groups/create/", views.custom_field_group_create, name="custom_field_group_create"),
    path("admin/fields/groups/<int:group_id>/edit/", views.custom_field_group_edit, name="custom_field_group_edit"),
    path("admin/fields/create/", views.custom_field_def_create, name="custom_field_def_create"),
    path("admin/fields/<int:field_id>/edit/", views.custom_field_def_edit, name="custom_field_def_edit"),
]

from django.contrib import admin

from .models import (
    ClientDetailValue,
    ClientFile,
    ClientProgramEnrolment,
    CustomFieldDefinition,
    CustomFieldGroup,
)


@admin.register(ClientFile)
class ClientFileAdmin(admin.ModelAdmin):
    # Encrypted PII fields excluded — use property accessors in readonly
    list_display = ("id", "record_id", "status", "is_demo", "created_at")
    list_filter = ("status", "is_demo")
    search_fields = ("record_id",)
    readonly_fields = ("is_demo",)  # Security: is_demo set at creation only


@admin.register(ClientProgramEnrolment)
class ClientProgramEnrolmentAdmin(admin.ModelAdmin):
    list_display = ("client_file", "program", "enrolled_at", "status")
    list_filter = ("status",)


@admin.register(CustomFieldGroup)
class CustomFieldGroupAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order")


@admin.register(CustomFieldDefinition)
class CustomFieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "input_type", "group", "is_required", "is_sensitive")
    list_filter = ("input_type", "is_required", "is_sensitive")


@admin.register(ClientDetailValue)
class ClientDetailValueAdmin(admin.ModelAdmin):
    list_display = ("client_file", "field_def", "id")

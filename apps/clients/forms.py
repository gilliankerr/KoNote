"""Client forms."""
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.programs.models import Program

from .models import ClientFile, CustomFieldDefinition, CustomFieldGroup


class ConsentRecordForm(forms.Form):
    """Form to record client consent for data collection (PIPEDA/PHIPA compliance)."""

    CONSENT_TYPE_CHOICES = [
        ("written", _("Written consent")),
        ("verbal", _("Verbal consent")),
        ("electronic", _("Electronic consent")),
    ]

    consent_type = forms.ChoiceField(
        choices=CONSENT_TYPE_CHOICES,
        label=_("Consent type"),
        initial="written",
    )
    consent_date = forms.DateField(
        label=_("Date consent was obtained"),
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=timezone.now,
    )
    notes = forms.CharField(
        required=False,
        label=_("Notes (optional)"),
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Any additional details about how consent was obtained..."}),
    )


class ClientFileForm(forms.Form):
    """Form for client PII — plain form since fields are encrypted properties."""

    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    middle_name = forms.CharField(max_length=255, required=False)
    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    record_id = forms.CharField(max_length=100, required=False)
    status = forms.ChoiceField(choices=ClientFile.STATUS_CHOICES)

    # Program enrolment checkboxes — populated dynamically
    programs = forms.ModelMultipleChoiceField(
        queryset=Program.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, available_programs=None, **kwargs):
        super().__init__(*args, **kwargs)
        if available_programs is not None:
            self.fields["programs"].queryset = available_programs


class CustomFieldGroupForm(forms.ModelForm):
    class Meta:
        model = CustomFieldGroup
        fields = ["title", "sort_order", "status"]


class CustomFieldValuesForm(forms.Form):
    """Dynamic form for saving custom field values on a client.

    Builds one field per active custom field definition, keyed as 'custom_{pk}'.
    """

    def __init__(self, *args, field_definitions=None, **kwargs):
        super().__init__(*args, **kwargs)
        if field_definitions:
            for field_def in field_definitions:
                field_key = f"custom_{field_def.pk}"
                if field_def.input_type == "checkbox":
                    self.fields[field_key] = forms.BooleanField(
                        required=False, label=field_def.name,
                    )
                elif field_def.input_type == "number":
                    self.fields[field_key] = forms.CharField(
                        required=field_def.is_required,
                        label=field_def.name,
                    )
                elif field_def.input_type == "select" and field_def.options_json:
                    choices = [("", _("— Select —"))] + [
                        (opt, opt) for opt in field_def.options_json
                    ]
                    self.fields[field_key] = forms.ChoiceField(
                        choices=choices,
                        required=field_def.is_required,
                        label=field_def.name,
                    )
                else:
                    self.fields[field_key] = forms.CharField(
                        required=field_def.is_required,
                        label=field_def.name,
                        widget=forms.Textarea(attrs={"rows": 2})
                        if field_def.input_type == "textarea"
                        else forms.TextInput(attrs={"placeholder": field_def.placeholder or ""}),
                    )


class CustomFieldDefinitionForm(forms.ModelForm):
    class Meta:
        model = CustomFieldDefinition
        fields = [
            "group", "name", "input_type", "placeholder", "is_required",
            "is_sensitive", "receptionist_access", "options_json", "sort_order", "status",
        ]
        widgets = {
            "options_json": forms.Textarea(attrs={"rows": 3, "placeholder": '["Option 1", "Option 2"]'}),
        }
        help_texts = {
            "receptionist_access": _("Set front desk access to 'View and edit' for contact info, emergency contacts, and safety alerts."),
        }

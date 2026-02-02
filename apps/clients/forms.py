"""Client forms."""
from django import forms

from apps.programs.models import Program

from .models import ClientFile, CustomFieldDefinition, CustomFieldGroup


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


class CustomFieldDefinitionForm(forms.ModelForm):
    class Meta:
        model = CustomFieldDefinition
        fields = ["group", "name", "input_type", "placeholder", "is_required", "is_sensitive", "options_json", "sort_order", "status"]
        widgets = {
            "options_json": forms.Textarea(attrs={"rows": 3, "placeholder": '["Option 1", "Option 2"]'}),
        }

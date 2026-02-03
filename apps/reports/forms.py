"""Forms for the reports app — metric export filtering."""
from django import forms

from apps.programs.models import Program
from apps.plans.models import MetricDefinition


class MetricExportForm(forms.Form):
    """Filter form for the aggregate metric CSV export."""

    program = forms.ModelChoiceField(
        queryset=Program.objects.filter(status="active"),
        required=True,
        label="Program",
        empty_label="— Select a programme —",
    )
    metrics = forms.ModelMultipleChoiceField(
        queryset=MetricDefinition.objects.filter(is_enabled=True, status="active"),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Metrics to include",
    )
    date_from = forms.DateField(
        required=True,
        label="Date from",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        required=True,
        label="Date to",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get("date_from")
        date_to = cleaned.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("'Date from' must be before 'Date to'.")
        return cleaned

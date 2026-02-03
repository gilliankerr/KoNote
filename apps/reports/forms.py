"""Forms for the reports app — metric export filtering and CMT reports."""
from django import forms

from apps.programs.models import Program
from apps.plans.models import MetricDefinition
from .demographics import get_demographic_field_choices
from .utils import get_fiscal_year_choices, get_fiscal_year_range, get_current_fiscal_year


class MetricExportForm(forms.Form):
    """Filter form for the aggregate metric CSV export."""

    program = forms.ModelChoiceField(
        queryset=Program.objects.filter(status="active"),
        required=True,
        label="Program",
        empty_label="— Select a programme —",
    )

    # Fiscal year quick-select (optional — overrides manual dates when selected)
    fiscal_year = forms.ChoiceField(
        required=False,
        label="Fiscal Year (April-March)",
        help_text="Select a fiscal year to auto-fill dates, or leave blank for custom range.",
    )

    metrics = forms.ModelMultipleChoiceField(
        queryset=MetricDefinition.objects.filter(is_enabled=True, status="active"),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Metrics to include",
    )
    date_from = forms.DateField(
        required=False,  # Made optional — fiscal_year can provide dates
        label="Date from",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    date_to = forms.DateField(
        required=False,  # Made optional — fiscal_year can provide dates
        label="Date to",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    # Demographic grouping (optional)
    group_by = forms.ChoiceField(
        required=False,
        label="Group by demographic",
        help_text="Optionally break down results by age range or a custom field.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Build fiscal year choices dynamically (includes blank option)
        fy_choices = [("", "— Custom date range —")] + get_fiscal_year_choices()
        self.fields["fiscal_year"].choices = fy_choices
        # Build demographic grouping choices dynamically
        self.fields["group_by"].choices = get_demographic_field_choices()

    FORMAT_CHOICES = [
        ("csv", "CSV (spreadsheet)"),
        ("pdf", "PDF (printable report)"),
    ]

    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial="csv",
        widget=forms.RadioSelect,
        label="Export format",
    )

    include_achievement_rate = forms.BooleanField(
        required=False,
        initial=False,
        label="Include achievement rate",
        help_text="Calculate and include outcome achievement statistics in the export.",
    )

    def clean(self):
        cleaned = super().clean()
        fiscal_year = cleaned.get("fiscal_year")
        date_from = cleaned.get("date_from")
        date_to = cleaned.get("date_to")

        # If fiscal year is selected, use those dates instead of manual entry
        if fiscal_year:
            try:
                fy_start_year = int(fiscal_year)
                date_from, date_to = get_fiscal_year_range(fy_start_year)
                cleaned["date_from"] = date_from
                cleaned["date_to"] = date_to
            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid fiscal year selection.")
        else:
            # Manual date entry — both fields required
            if not date_from:
                self.add_error("date_from", "This field is required when not using a fiscal year.")
            if not date_to:
                self.add_error("date_to", "This field is required when not using a fiscal year.")

        # Validate date order (after potentially setting from fiscal year)
        date_from = cleaned.get("date_from")
        date_to = cleaned.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("'Date from' must be before 'Date to'.")

        return cleaned


class CMTExportForm(forms.Form):
    """
    Form for United Way CMT (Community Monitoring Tool) export.

    This form is simpler than the full metric export form, as CMT reports
    have a fixed structure. Users select a programme and fiscal year,
    and the report is generated with all applicable data.
    """

    program = forms.ModelChoiceField(
        queryset=Program.objects.filter(status="active"),
        required=True,
        label="Programme",
        empty_label="— Select a programme —",
    )

    fiscal_year = forms.ChoiceField(
        required=True,
        label="Fiscal Year (April-March)",
        help_text="Select the fiscal year to report on.",
    )

    FORMAT_CHOICES = [
        ("csv", "CSV (spreadsheet)"),
        ("pdf", "PDF (printable report)"),
    ]

    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial="csv",
        widget=forms.RadioSelect,
        label="Export format",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Build fiscal year choices dynamically
        # For CMT, we require a fiscal year selection (no custom date range)
        self.fields["fiscal_year"].choices = get_fiscal_year_choices()
        # Default to current fiscal year
        self.fields["fiscal_year"].initial = str(get_current_fiscal_year())

    def clean(self):
        cleaned = super().clean()
        fiscal_year = cleaned.get("fiscal_year")

        if fiscal_year:
            try:
                fy_start_year = int(fiscal_year)
                date_from, date_to = get_fiscal_year_range(fy_start_year)
                cleaned["date_from"] = date_from
                cleaned["date_to"] = date_to
                # Create fiscal year label for display
                end_year_short = str(fy_start_year + 1)[-2:]
                cleaned["fiscal_year_label"] = f"FY {fy_start_year}-{end_year_short}"
            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid fiscal year selection.")
        else:
            raise forms.ValidationError("Please select a fiscal year.")

        return cleaned

"""Admin settings views: dashboard, terminology, features, instance settings."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from .forms import FeatureToggleForm, InstanceSettingsForm, TerminologyForm
from .models import DEFAULT_TERMS, FeatureToggle, InstanceSetting, TerminologyOverride


def admin_required(view_func):
    """Decorator: 403 if user is not an admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            return HttpResponseForbidden("Access denied. Admin privileges required.")
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# --- Dashboard ---

@login_required
@admin_required
def dashboard(request):
    return render(request, "admin_settings/dashboard.html")


# --- Terminology ---

@login_required
@admin_required
def terminology(request):
    # Build lookup of current overrides from database
    overrides = {
        obj.term_key: obj
        for obj in TerminologyOverride.objects.all()
    }

    if request.method == "POST":
        # Build current terms dicts for form initialisation
        current_terms_en = {}
        current_terms_fr = {}
        for key, defaults in DEFAULT_TERMS.items():
            default_en, _ = defaults
            if key in overrides:
                current_terms_en[key] = overrides[key].display_value
                current_terms_fr[key] = overrides[key].display_value_fr
            else:
                current_terms_en[key] = default_en

        form = TerminologyForm(
            request.POST,
            current_terms_en=current_terms_en,
            current_terms_fr=current_terms_fr,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Terminology updated.")
            return redirect("admin_settings:terminology")

    # Build table data: key, defaults, current values, is_overridden
    term_rows = []
    for key, defaults in DEFAULT_TERMS.items():
        default_en, default_fr = defaults
        override = overrides.get(key)
        term_rows.append({
            "key": key,
            "default_en": default_en,
            "default_fr": default_fr,
            "current_en": override.display_value if override else default_en,
            "current_fr": override.display_value_fr if override else "",
            "is_overridden": key in overrides,
        })

    return render(request, "admin_settings/terminology.html", {
        "term_rows": term_rows,
    })


@login_required
@admin_required
def terminology_reset(request, term_key):
    """Delete an override, reverting to default."""
    if request.method == "POST":
        TerminologyOverride.objects.filter(term_key=term_key).delete()
        messages.success(request, f"Reset '{term_key}' to default.")
    return redirect("admin_settings:terminology")


# --- Feature Toggles ---

DEFAULT_FEATURES = {
    "programs": "Programs module",
    "custom_fields": "Custom client fields",
    "alerts": "Metric alerts",
    "events": "Event tracking",
    "funder_reports": "Funder report exports",
    "require_client_consent": "Require client consent before notes (PIPEDA/PHIPA)",
}

# Features that default to enabled (most default to disabled)
FEATURES_DEFAULT_ENABLED = {"require_client_consent"}


@login_required
@admin_required
def features(request):
    if request.method == "POST":
        form = FeatureToggleForm(request.POST)
        if form.is_valid():
            feature_key = form.cleaned_data["feature_key"]
            action = form.cleaned_data["action"]
            FeatureToggle.objects.update_or_create(
                feature_key=feature_key,
                defaults={"is_enabled": action == "enable"},
            )
            state = "enabled" if action == "enable" else "disabled"
            messages.success(request, f"Feature '{feature_key}' {state}.")
            return redirect("admin_settings:features")

    # Build feature list with current state
    current_flags = FeatureToggle.get_all_flags()
    feature_rows = []
    for key, description in DEFAULT_FEATURES.items():
        # Some features default to enabled (e.g., consent requirement for PIPEDA)
        default_state = key in FEATURES_DEFAULT_ENABLED
        feature_rows.append({
            "key": key,
            "description": description,
            "is_enabled": current_flags.get(key, default_state),
        })

    return render(request, "admin_settings/features.html", {
        "feature_rows": feature_rows,
    })


# --- Instance Settings ---

@login_required
@admin_required
def instance_settings(request):
    current_settings = InstanceSetting.get_all()
    if request.method == "POST":
        form = InstanceSettingsForm(request.POST, current_settings=current_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated.")
            return redirect("admin_settings:instance_settings")
    else:
        form = InstanceSettingsForm(current_settings=current_settings)
    return render(request, "admin_settings/instance_settings.html", {"form": form})

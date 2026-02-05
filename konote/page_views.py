"""Views for static pages like help and privacy."""

from django.shortcuts import render


def help_view(request):
    """Render the help page."""
    return render(request, "pages/help.html")


def privacy_view(request):
    """Render the privacy policy page."""
    return render(request, "pages/privacy.html")

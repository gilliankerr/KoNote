"""Root URL — dashboard / client search."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import path


@login_required
def home(request):
    # Initial view shows empty search — results load via HTMX
    return render(request, "clients/home.html", {"results": [], "query": ""})


urlpatterns = [
    path("", home, name="home"),
]

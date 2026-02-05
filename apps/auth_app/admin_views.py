"""User management views — admin only."""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import UserCreateForm, UserEditForm
from .models import User


def admin_required(view_func):
    """Decorator: 403 if user is not an admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            return HttpResponseForbidden("Access denied. Admin privileges required.")
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@login_required
@admin_required
def user_list(request):
    users = User.objects.all().order_by("-is_admin", "display_name")
    return render(request, "auth_app/user_list.html", {"users": users})


@login_required
@admin_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created.")
            return redirect("auth_app:user_list")
    else:
        form = UserCreateForm()
    return render(request, "auth_app/user_form.html", {"form": form, "editing": False})


@login_required
@admin_required
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated.")
            return redirect("auth_app:user_list")
    else:
        form = UserEditForm(instance=user)
    return render(request, "auth_app/user_form.html", {
        "form": form, "editing": True, "edit_user": user,
    })


@login_required
@admin_required
def user_deactivate(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        if user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
        else:
            user.is_active = False
            user.save()
            messages.success(request, f"User '{user.display_name}' deactivated.")
    return redirect("auth_app:user_list")


@login_required
@admin_required
def impersonate_user(request, user_id):
    """
    Allow admin to log in as a demo user for testing purposes.

    CRITICAL SECURITY: Only demo users (is_demo=True) can be impersonated.
    Real users cannot be impersonated regardless of admin privileges.
    """
    target_user = get_object_or_404(User, pk=user_id)

    # CRITICAL SECURITY CHECK: Only allow impersonation of demo users
    if not target_user.is_demo:
        messages.error(
            request,
            "Cannot impersonate real users. Only demo accounts can be impersonated."
        )
        return redirect("auth_app:user_list")

    # Additional check: target must be active
    if not target_user.is_active:
        messages.error(request, "Cannot impersonate inactive users.")
        return redirect("auth_app:user_list")

    # Log the impersonation for audit trail
    _audit_impersonation(request, target_user)

    # Store original user info in session for potential "return to admin" feature
    original_user_id = request.user.id
    original_username = request.user.username

    # Perform logout then login as demo user
    logout(request)
    login(request, target_user)

    # Update last login timestamp
    target_user.last_login_at = timezone.now()
    target_user.save(update_fields=["last_login_at"])

    messages.success(
        request,
        f"You are now logged in as {target_user.get_display_name()} (demo account). "
        f"Impersonated by admin '{original_username}'."
    )
    return redirect("/")


def _audit_impersonation(request, target_user):
    """Record impersonation event in audit log."""
    try:
        from apps.audit.models import AuditLog

        AuditLog.objects.using("audit").create(
            event_timestamp=timezone.now(),
            user_id=request.user.id,
            user_display=request.user.get_display_name(),
            ip_address=request.META.get("REMOTE_ADDR", ""),
            action="login",  # Using 'login' as closest match from ACTION_CHOICES
            resource_type="impersonation",
            resource_id=target_user.id,
            metadata={
                "impersonated_user_id": target_user.id,
                "impersonated_username": target_user.username,
                "impersonated_display_name": target_user.get_display_name(),
                "admin_user_id": request.user.id,
                "admin_username": request.user.username,
            },
        )
    except Exception:
        # Don't fail the impersonation if audit logging fails
        pass

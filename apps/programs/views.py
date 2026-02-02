"""Program CRUD views — admin only."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.auth_app.models import User

from .forms import ProgramForm, UserProgramRoleForm
from .models import Program, UserProgramRole


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
def program_list(request):
    programs = Program.objects.all()
    # Annotate with user count
    program_data = []
    for program in programs:
        user_count = UserProgramRole.objects.filter(program=program, status="active").count()
        program_data.append({"program": program, "user_count": user_count})
    return render(request, "programs/list.html", {"program_data": program_data})


@login_required
@admin_required
def program_create(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Program created.")
            return redirect("programs:program_list")
    else:
        form = ProgramForm()
    return render(request, "programs/form.html", {"form": form, "editing": False})


@login_required
@admin_required
def program_edit(request, program_id):
    program = get_object_or_404(Program, pk=program_id)
    if request.method == "POST":
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, "Program updated.")
            return redirect("programs:program_detail", program_id=program.pk)
    else:
        form = ProgramForm(instance=program)
    return render(request, "programs/form.html", {"form": form, "editing": True, "program": program})


@login_required
@admin_required
def program_detail(request, program_id):
    program = get_object_or_404(Program, pk=program_id)
    roles = UserProgramRole.objects.filter(program=program).select_related("user").order_by("status", "user__display_name")
    role_form = UserProgramRoleForm(program=program)
    return render(request, "programs/detail.html", {
        "program": program,
        "roles": roles,
        "role_form": role_form,
    })


@login_required
@admin_required
def program_add_role(request, program_id):
    """HTMX: add a user to a program."""
    program = get_object_or_404(Program, pk=program_id)
    form = UserProgramRoleForm(request.POST, program=program)
    if form.is_valid():
        user = form.cleaned_data["user"]
        role = form.cleaned_data["role"]
        obj, created = UserProgramRole.objects.update_or_create(
            user=user, program=program,
            defaults={"role": role, "status": "active"},
        )
        if not created:
            messages.success(request, f"{user.display_name} role updated.")
        else:
            messages.success(request, f"{user.display_name} added.")
    # Return full role list partial
    roles = UserProgramRole.objects.filter(program=program).select_related("user").order_by("status", "user__display_name")
    return render(request, "programs/_role_list.html", {"roles": roles, "program": program})


@login_required
@admin_required
def program_remove_role(request, program_id, role_id):
    """HTMX: remove a user from a program (set status to removed)."""
    role = get_object_or_404(UserProgramRole, pk=role_id, program_id=program_id)
    role.status = "removed"
    role.save()
    messages.success(request, f"{role.user.display_name} removed.")
    roles = UserProgramRole.objects.filter(program_id=program_id).select_related("user").order_by("status", "user__display_name")
    return render(request, "programs/_role_list.html", {"roles": roles, "program": role.program})

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404
from users.models import User
from developers.models import Project
from .models import AssignedTask, ProjectAssignment, Notification


def is_manager(user):
    return user.is_staff


@login_required
@user_passes_test(is_manager)
@require_POST
def api_create_assigned_task(request):
    data = json.loads(request.body)
    title = data.get("title", "").strip()
    assignee_id = data.get("assignee_id")
    project_id = data.get("project_id") or None
    if not title or not assignee_id:
        return JsonResponse({"error": "title и assignee_id обязательны"}, status=400)
    assignee = get_object_or_404(User, pk=assignee_id, is_staff=False)
    project = None
    if project_id:
        project = get_object_or_404(Project, pk=project_id, owner=assignee)
    task = AssignedTask.objects.create(
        title=title,
        description=data.get("description", ""),
        creator=request.user,
        assignee=assignee,
        project=project,
    )
    Notification.objects.create(
        user=assignee,
        from_user=request.user,
        type="assigned_task",
        title="Новая задача",
        message=f"Вам назначена задача: {title}",
        related_id=task.id,
    )
    return JsonResponse({"success": True, "task_id": task.id})


@login_required
@user_passes_test(is_manager)
@require_POST
def api_create_project_assignment(request):
    """Создаёт НАЗНАЧЕНИЕ проекта (не готовый проект). Проект появится у разработчика после принятия."""
    data = json.loads(request.body)
    name = data.get("name", "").strip()
    assignee_id = data.get("assignee_id")
    if not name or not assignee_id:
        return JsonResponse({"error": "name и assignee_id обязательны"}, status=400)
    assignee = get_object_or_404(User, pk=assignee_id, is_staff=False)
    project = Project.objects.create(
        name=name,
        owner=request.user,  # временный владелец – менеджер
        hourly_rate=float(data.get("hourly_rate", 0)),
    )
    assignment = ProjectAssignment.objects.create(
        project=project, user=assignee, status="pending"
    )
    Notification.objects.create(
        user=assignee,
        from_user=request.user,
        type="project_assignment",
        title="Новый проект",
        message=f"Вам назначен проект: {name}",
        related_id=assignment.id,
    )
    return JsonResponse({"success": True, "assignment_id": assignment.id})


@login_required
@user_passes_test(is_manager)
@require_GET
def api_user_projects(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    projects = Project.objects.filter(owner=user).values("id", "name")
    return JsonResponse(list(projects), safe=False)

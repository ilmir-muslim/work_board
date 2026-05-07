# managers/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from developers.models import Project, Task
from users.models import User
from .models import AssignedTask, ProjectAssignment, Notification, AssignmentAttachment
from .forms import AssignedTaskForm, ProjectAssignmentForm


def is_manager(user):
    """Проверка, что пользователь — менеджер (is_staff)."""
    return user.is_authenticated and user.is_staff


# ---------- Разработчики ----------
@login_required
@user_passes_test(is_manager)
def developer_list(request):
    """Список всех разработчиков."""
    developers = User.objects.filter(is_staff=False)
    return render(request, "managers/developer_list.html", {"developers": developers})


@login_required
@user_passes_test(is_manager)
def developer_projects(request, user_id):
    """Проекты конкретного разработчика."""
    developer = get_object_or_404(User, pk=user_id, is_staff=False)
    projects = Project.objects.filter(owner=developer)
    return render(
        request,
        "managers/developer_projects.html",
        {
            "developer": developer,
            "projects": projects,
        },
    )


@login_required
@user_passes_test(is_manager)
def developer_project_detail(request, user_id, project_id):
    """Детали проекта разработчика."""
    developer = get_object_or_404(User, pk=user_id)
    project = get_object_or_404(Project, pk=project_id, owner=developer)
    tasks = Task.objects.filter(project=project).order_by("-created_at")
    assigned_tasks = AssignedTask.objects.filter(project=project, assignee=developer)
    return render(
        request,
        "managers/developer_project_detail.html",
        {
            "developer": developer,
            "project": project,
            "tasks": tasks,
            "assigned_tasks": assigned_tasks,
        },
    )


# ---------- Назначенные задачи ----------
@login_required
@user_passes_test(is_manager)
def assigned_task_list(request):
    """Все назначенные задачи (менеджер видит все)."""
    tasks = AssignedTask.objects.select_related(
        "creator", "assignee", "project"
    ).order_by("-created_at")
    return render(request, "managers/assigned_task_list.html", {"tasks": tasks})


@login_required
@user_passes_test(is_manager)
def assigned_task_create(request):
    """Страница создания назначенной задачи (обычная форма)."""
    if request.method == "POST":
        form = AssignedTaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.creator = request.user
            task.save()
            # Сохраняем прикреплённые файлы
            for file in request.FILES.getlist("attachments"):
                AssignmentAttachment.objects.create(
                    assigned_task=task, file=file, original_filename=file.name
                )
            # Уведомление
            Notification.objects.create(
                user=task.assignee,
                from_user=request.user,
                type="assigned_task",
                title="Новая задача",
                message=f"Вам назначена задача: {task.title}",
                related_id=task.id,
            )
            messages.success(request, "Задача успешно назначена")
            return redirect("managers:developer_list")
    else:
        form = AssignedTaskForm()
    return render(
        request,
        "managers/assigned_task_form.html",
        {
            "form": form,
            "title": "Назначить задачу",
        },
    )


@login_required
@user_passes_test(is_manager)
def assigned_task_detail(request, task_id):
    """Детальный просмотр назначенной задачи."""
    task = get_object_or_404(AssignedTask, pk=task_id)
    return render(request, "managers/assigned_task_detail.html", {"task": task})


# ---------- Назначение проекта ----------
@login_required
@user_passes_test(is_manager)
def project_assignment_create(request):
    """Страница создания назначения проекта (создаёт временный проект и назначение)."""
    if request.method == "POST":
        form = ProjectAssignmentForm(
            request.POST, request.FILES, current_user=request.user
        )
        if form.is_valid():
            assignment = form.save()
            # Сохраняем прикреплённые файлы
            for file in request.FILES.getlist("attachments"):
                AssignmentAttachment.objects.create(
                    project_assignment=assignment,
                    file=file,
                    original_filename=file.name,
                )
            # Уведомление
            Notification.objects.create(
                user=assignment.user,
                from_user=request.user,
                type="project_assignment",
                title="Новый проект",
                message=f"Вам назначен проект: {assignment.project.name}",
                related_id=assignment.id,
            )
            messages.success(request, "Проект успешно назначен")
            return redirect("managers:developer_list")
    else:
        form = ProjectAssignmentForm(current_user=request.user)
    return render(
        request,
        "managers/project_assignment_form.html",
        {
            "form": form,
            "title": "Назначить проект",
        },
    )


# ---------- Уведомления ----------
@login_required
@user_passes_test(is_manager)
def notification_list(request):
    """Уведомления менеджера."""
    notifications = request.user.notifications.order_by("-created_at")
    return render(
        request, "managers/notifications.html", {"notifications": notifications}
    )

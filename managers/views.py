import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction

from developers.models import Project, Task
from users.models import User
from .models import AssignedTask, ProjectAssignment, Notification
from .forms import AssignedTaskForm, ProjectAssignmentForm


# ---------- Назначенные задачи (только для персонала) ----------
@staff_member_required
def assigned_task_list(request):
    """Список задач, созданных текущим менеджером."""
    tasks = (
        AssignedTask.objects.filter(creator=request.user)
        .select_related("assignee", "project")
        .order_by("-created_at")
    )
    return render(request, "managers/assigned_task_list.html", {"tasks": tasks})


@staff_member_required
def assigned_task_create(request):
    """Создание новой назначенной задачи для нескольких пользователей."""
    if request.method == "POST":
        form = AssignedTaskForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            project = form.cleaned_data["project"]
            assignees = form.cleaned_data["assignees"]
            group_id = uuid.uuid4()

            for user in assignees:
                AssignedTask.objects.create(
                    title=title,
                    description=description,
                    creator=request.user,
                    assignee=user,
                    project=project,
                    group_id=group_id,
                    status="pending",
                )
            return redirect("managers:assigned_task_list")
    else:
        form = AssignedTaskForm()
    form.fields["project"].queryset = Project.objects.filter(owner=request.user)
    return render(
        request,
        "managers/assigned_task_form.html",
        {"form": form, "title": "Создать назначенную задачу"},
    )


@staff_member_required
def assigned_task_update(request, pk):
    """Редактирование назначенной задачи (только своей)."""
    task = get_object_or_404(AssignedTask, pk=pk, creator=request.user)
    if request.method == "POST":
        form = AssignedTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("managers:assigned_task_list")
    else:
        form = AssignedTaskForm(instance=task)
    form.fields["project"].queryset = Project.objects.filter(owner=request.user)
    # Убираем поле assignees при редактировании (если оно есть в форме)
    if "assignees" in form.fields:
        del form.fields["assignees"]
    return render(
        request,
        "managers/assigned_task_form.html",
        {"form": form, "title": "Редактировать задачу"},
    )


@staff_member_required
def assigned_task_delete(request, pk):
    """Удаление назначенной задачи."""
    task = get_object_or_404(AssignedTask, pk=pk, creator=request.user)
    if request.method == "POST":
        task.delete()
        return redirect("managers:assigned_task_list")
    return render(request, "managers/assigned_task_confirm_delete.html", {"task": task})


# ---------- Просмотр назначенных задач для обычного пользователя ----------
@login_required
def assigned_to_me_list(request):
    """Список задач, назначенных текущему пользователю."""
    tasks = AssignedTask.objects.filter(assignee=request.user).order_by("-created_at")
    return render(request, "managers/assigned_to_me_list.html", {"tasks": tasks})


@login_required
def accept_assigned_task(request, pk):
    """Принятие назначенной задачи пользователем (создание копии)."""
    assigned = get_object_or_404(
        AssignedTask, pk=pk, assignee=request.user, status="pending"
    )

    if request.method == "POST":
        with transaction.atomic():
            # Создаём копию проекта, если есть оригинальный проект
            new_project = None
            if assigned.project:
                new_project = Project.objects.create(
                    name=assigned.project.name,
                    owner=request.user,
                    hourly_rate=assigned.project.hourly_rate,
                )
            else:
                # Если проекта нет, создаём проект с названием задачи
                new_project = Project.objects.create(
                    name=assigned.title, owner=request.user, hourly_rate=0.0
                )

            # Создаём задачу в личных задачах
            new_task = Task.objects.create(
                title=assigned.title,
                project=new_project,
                owner=request.user,
                assigned_task=assigned,
            )

            # Обновляем статус назначенной задачи
            assigned.status = "accepted"
            assigned.accepted_at = timezone.now()
            assigned.save()

            # Отклоняем остальные задачи в той же группе
            if assigned.group_id:
                AssignedTask.objects.filter(group_id=assigned.group_id).exclude(
                    pk=assigned.pk
                ).update(status="rejected")

            # Создаём уведомление для создателя
            Notification.objects.create(
                user=assigned.creator,
                from_user=request.user,
                type="task_accepted",
                title=f"Задача принята: {assigned.title}",
                message=f"Пользователь {request.user.username} принял задачу.",
                related_id=assigned.pk,
            )

        return redirect("developers:task_detail", pk=new_task.pk)

    return render(request, "managers/accept_assigned_task.html", {"assigned": assigned})


# ---------- Назначения проектов ----------
@staff_member_required
def project_assignment_list(request):
    """Список назначений проектов, созданных текущим менеджером."""
    # Получаем все проекты менеджера и их назначения
    projects = Project.objects.filter(owner=request.user)
    assignments = (
        ProjectAssignment.objects.filter(project__in=projects)
        .select_related("project", "user")
        .order_by("-created_at")
    )
    return render(
        request, "managers/project_assignment_list.html", {"assignments": assignments}
    )


@staff_member_required
def project_assignment_create(request):
    """Создание назначения проекта для нескольких пользователей."""
    if request.method == "POST":
        form = ProjectAssignmentForm(request.POST)
        if form.is_valid():
            project = form.cleaned_data["project"]
            users = form.cleaned_data["users"]
            group_id = uuid.uuid4()
            for user in users:
                ProjectAssignment.objects.create(
                    project=project, user=user, group_id=group_id, status="pending"
                )
            return redirect("managers:project_assignment_list")
    else:
        form = ProjectAssignmentForm()
    form.fields["project"].queryset = Project.objects.filter(owner=request.user)
    return render(
        request,
        "managers/project_assignment_form.html",
        {"form": form, "title": "Назначить проект"},
    )


@login_required
def project_assignments_to_me(request):
    """Список назначений проектов для текущего пользователя."""
    assignments = (
        ProjectAssignment.objects.filter(user=request.user)
        .select_related("project")
        .order_by("-created_at")
    )
    return render(
        request, "managers/project_assignments_to_me.html", {"assignments": assignments}
    )


@login_required
def accept_project_assignment(request, pk):
    """Принятие назначения проекта пользователем."""
    assignment = get_object_or_404(
        ProjectAssignment, pk=pk, user=request.user, status="pending"
    )

    if request.method == "POST":
        with transaction.atomic():
            # Копируем проект
            new_project = Project.objects.create(
                name=assignment.project.name,
                owner=request.user,
                hourly_rate=assignment.project.hourly_rate,
            )

            # Обновляем статус назначения
            assignment.status = "accepted"
            assignment.accepted_at = timezone.now()
            assignment.save()

            # Отклоняем остальные в группе
            if assignment.group_id:
                ProjectAssignment.objects.filter(group_id=assignment.group_id).exclude(
                    pk=assignment.pk
                ).update(status="rejected")

            # Уведомление создателю проекта
            Notification.objects.create(
                user=assignment.project.owner,
                from_user=request.user,
                type="project_accepted",
                title=f"Проект принят: {assignment.project.name}",
                message=f"Пользователь {request.user.username} принял проект.",
                related_id=assignment.pk,
            )

        return redirect("developers:project_list")

    return render(
        request, "managers/accept_project_assignment.html", {"assignment": assignment}
    )


# ---------- Уведомления ----------
@login_required
def notification_list(request):
    """Список уведомлений текущего пользователя."""
    notifications = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    return render(
        request, "managers/notification_list.html", {"notifications": notifications}
    )


@login_required
def mark_notification_read(request, pk):
    """Отметить уведомление как прочитанное."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect("managers:notification_list")


@login_required
def notification_delete(request, pk):
    """Удалить уведомление."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if request.method == "POST":
        notification.delete()
    return redirect("managers:notification_list")

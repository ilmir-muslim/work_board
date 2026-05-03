from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import F
from datetime import timedelta

from .models import (
    Project,
    Task,
    SubTask,
    TaskComment,
    SubTaskComment,
    DailyWorkSession,
)
from .forms import ProjectForm, TaskForm, SubTaskForm, CommentForm


# ---------- Проекты ----------
@login_required
def project_list(request):
    """Список проектов текущего пользователя."""
    projects = Project.objects.filter(owner=request.user)
    return render(request, "developers/project_list.html", {"projects": projects})


@login_required
def project_create(request):
    """Создание нового проекта."""
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            if not project.hourly_rate:
                project.hourly_rate = request.user.default_hourly_rate
            project.save()
            return redirect("developers:project_list")
    else:
        form = ProjectForm()
    return render(
        request,
        "developers/project_form.html",
        {"form": form, "title": "Создать проект"},
    )


@login_required
def project_update(request, pk):
    """Редактирование проекта."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("developers:project_list")
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        "developers/project_form.html",
        {"form": form, "title": "Редактировать проект"},
    )


@login_required
def project_delete(request, pk):
    """Удаление проекта."""
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == "POST":
        project.delete()
        return redirect("developers:project_list")
    return render(
        request, "developers/project_confirm_delete.html", {"project": project}
    )


# ---------- Задачи ----------
@login_required
def task_list(request):
    """Список всех задач пользователя (без деталей)."""
    tasks = (
        Task.objects.filter(owner=request.user)
        .select_related("project")
        .order_by("-created_at")
    )
    return render(request, "developers/task_list.html", {"tasks": tasks})


@login_required
def task_detail(request, pk):
    """Детальный просмотр задачи с подзадачами и комментариями."""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    sub_tasks = task.sub_tasks.all()
    comments = task.comments.all()
    return render(
        request,
        "developers/task_detail.html",
        {
            "task": task,
            "sub_tasks": sub_tasks,
            "comments": comments,
        },
    )


@login_required
def task_create(request):
    """Создание новой задачи."""
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            return redirect("developers:task_detail", pk=task.pk)
    else:
        form = TaskForm()
    form.fields["project"].queryset = Project.objects.filter(owner=request.user)
    return render(
        request, "developers/task_form.html", {"form": form, "title": "Создать задачу"}
    )


@login_required
def task_update(request, pk):
    """Редактирование задачи."""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save()
            # Если задача помечена как завершённая, ставим completed_at
            if updated_task.is_completed and not updated_task.completed_at:
                updated_task.completed_at = timezone.now()
                updated_task.save()
            return redirect("developers:task_detail", pk=task.pk)
    else:
        form = TaskForm(instance=task)
    form.fields["project"].queryset = Project.objects.filter(owner=request.user)
    return render(
        request,
        "developers/task_form.html",
        {"form": form, "title": "Редактировать задачу"},
    )


@login_required
def task_delete(request, pk):
    """Удаление задачи."""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == "POST":
        task.delete()
        return redirect("developers:task_list")
    return render(request, "developers/task_confirm_delete.html", {"task": task})


# ---------- Таймеры ----------
@login_required
def start_timer(request, task_id):
    """Запустить таймер для задачи (останавливает все остальные задачи пользователя)."""
    task = get_object_or_404(Task, pk=task_id, owner=request.user)

    # Останавливаем все другие запущенные задачи пользователя
    running_tasks = Task.objects.filter(
        owner=request.user, is_timer_running=True
    ).exclude(pk=task_id)
    for t in running_tasks:
        if t.last_start_time:
            elapsed = (timezone.now() - t.last_start_time).total_seconds()
            t.total_time = (t.total_time or 0) + elapsed
        t.is_timer_running = False
        t.last_start_time = None
        t.save()

    # Если текущая задача уже запущена – ничего не делаем
    if task.is_timer_running:
        return redirect("developers:task_detail", pk=task_id)

    # Запускаем текущую задачу
    task.is_timer_running = True
    task.last_start_time = timezone.now()
    task.save()

    # Обновляем или создаём дневную сессию
    today = timezone.now().date()
    session, _ = DailyWorkSession.objects.get_or_create(user=request.user, date=today)
    if not session.is_timer_running:
        session.is_timer_running = True
        session.last_start_time = timezone.now()
        session.save()

    return redirect("developers:task_detail", pk=task_id)


@login_required
def pause_timer(request, task_id):
    """Остановить таймер для конкретной задачи."""
    task = get_object_or_404(Task, pk=task_id, owner=request.user)

    if not task.is_timer_running:
        return redirect("developers:task_detail", pk=task_id)

    # Добавляем прошедшее время
    if task.last_start_time:
        elapsed = (timezone.now() - task.last_start_time).total_seconds()
        task.total_time = (task.total_time or 0) + elapsed
    task.is_timer_running = False
    task.last_start_time = None
    task.save()

    # Проверяем, есть ли ещё запущенные задачи у пользователя
    if not Task.objects.filter(owner=request.user, is_timer_running=True).exists():
        # Останавливаем дневную сессию
        today = timezone.now().date()
        try:
            session = DailyWorkSession.objects.get(user=request.user, date=today)
            if session.is_timer_running and session.last_start_time:
                elapsed = (timezone.now() - session.last_start_time).total_seconds()
                session.total_time += elapsed
                session.is_timer_running = False
                session.last_start_time = None
                session.save()
        except DailyWorkSession.DoesNotExist:
            pass

    return redirect("developers:task_detail", pk=task_id)


@login_required
def stop_all_timers(request):
    """Остановить все таймеры пользователя (задачи и дневную сессию)."""
    # Останавливаем все задачи
    running_tasks = Task.objects.filter(owner=request.user, is_timer_running=True)
    for task in running_tasks:
        if task.last_start_time:
            elapsed = (timezone.now() - task.last_start_time).total_seconds()
            task.total_time = (task.total_time or 0) + elapsed
        task.is_timer_running = False
        task.last_start_time = None
    Task.objects.bulk_update(
        running_tasks, ["total_time", "is_timer_running", "last_start_time"]
    )

    # Останавливаем дневную сессию
    today = timezone.now().date()
    try:
        session = DailyWorkSession.objects.get(user=request.user, date=today)
        if session.is_timer_running and session.last_start_time:
            elapsed = (timezone.now() - session.last_start_time).total_seconds()
            session.total_time += elapsed
            session.is_timer_running = False
            session.last_start_time = None
            session.save()
    except DailyWorkSession.DoesNotExist:
        pass

    return redirect("developers:task_list")


# ---------- Подзадачи ----------
@login_required
def sub_task_create(request, task_id):
    """Создание подзадачи для задачи."""
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    if request.method == "POST":
        form = SubTaskForm(request.POST)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.task = task
            sub.save()
            return redirect("developers:task_detail", pk=task_id)
    else:
        form = SubTaskForm()
    return render(
        request,
        "developers/subtask_form.html",
        {"form": form, "task": task, "title": "Создать подзадачу"},
    )


@login_required
def sub_task_update(request, pk):
    """Редактирование подзадачи."""
    sub = get_object_or_404(SubTask, pk=pk, task__owner=request.user)
    if request.method == "POST":
        form = SubTaskForm(request.POST, instance=sub)
        if form.is_valid():
            updated_sub = form.save()
            if updated_sub.is_completed and not updated_sub.completed_at:
                updated_sub.completed_at = timezone.now()
                updated_sub.save()
            return redirect("developers:task_detail", pk=sub.task_id)
    else:
        form = SubTaskForm(instance=sub)
    return render(
        request,
        "developers/subtask_form.html",
        {"form": form, "task": sub.task, "title": "Редактировать подзадачу"},
    )


@login_required
def sub_task_delete(request, pk):
    """Удаление подзадачи."""
    sub = get_object_or_404(SubTask, pk=pk, task__owner=request.user)
    task_id = sub.task_id
    if request.method == "POST":
        sub.delete()
        return redirect("developers:task_detail", pk=task_id)
    return render(request, "developers/subtask_confirm_delete.html", {"sub": sub})


# ---------- Комментарии к задачам ----------
@login_required
def task_comment_create(request, task_id):
    """Создание комментария к задаче."""
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.save()
            return redirect("developers:task_detail", pk=task_id)
    else:
        form = CommentForm()
    return render(
        request,
        "developers/comment_form.html",
        {"form": form, "task": task, "title": "Добавить комментарий"},
    )


@login_required
def task_comment_delete(request, pk):
    """Удаление комментария к задаче."""
    comment = get_object_or_404(TaskComment, pk=pk, task__owner=request.user)
    task_id = comment.task_id
    if request.method == "POST":
        comment.delete()
        return redirect("developers:task_detail", pk=task_id)
    return render(
        request, "developers/comment_confirm_delete.html", {"comment": comment}
    )


# ---------- Комментарии к подзадачам ----------
@login_required
def sub_task_comment_create(request, sub_task_id):
    """Создание комментария к подзадаче."""
    sub = get_object_or_404(SubTask, pk=sub_task_id, task__owner=request.user)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.sub_task = sub
            comment.save()
            return redirect("developers:task_detail", pk=sub.task_id)
    else:
        form = CommentForm()
    return render(
        request,
        "developers/subtask_comment_form.html",
        {"form": form, "sub": sub, "title": "Добавить комментарий к подзадаче"},
    )


@login_required
def sub_task_comment_delete(request, pk):
    """Удаление комментария к подзадаче."""
    comment = get_object_or_404(
        SubTaskComment, pk=pk, sub_task__task__owner=request.user
    )
    task_id = comment.sub_task.task_id
    if request.method == "POST":
        comment.delete()
        return redirect("developers:task_detail", pk=task_id)
    return render(
        request, "developers/subtask_comment_confirm_delete.html", {"comment": comment}
    )


# ---------- Ежедневная статистика ----------
@login_required
def daily_stats(request, days=30):
    """Статистика по дням за последние N дней."""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days - 1)
    sessions = DailyWorkSession.objects.filter(
        user=request.user, date__gte=start_date
    ).order_by("date")

    stats_dict = {sess.date: sess.total_with_current for sess in sessions}

    result = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        result.append(
            {
                "date": day,
                "total_seconds": stats_dict.get(day, 0.0),
            }
        )

    today = result[-1] if result else {"date": end_date, "total_seconds": 0.0}
    week = result[-7:] if len(result) >= 7 else result
    month = result

    return render(
        request,
        "developers/daily_stats.html",
        {
            "today": today,
            "week": week,
            "month": month,
            "days": days,
        },
    )


# ---------- Заработок ----------
@login_required
def earnings_summary(request):
    """Сводка по заработку (по проектам и в среднем в месяц)."""
    user = request.user
    projects = Project.objects.filter(owner=user)
    total_earned = 0.0
    for proj in projects:
        total_earned += proj.earned_amount

    now = timezone.now()
    months_since = (now.year - user.date_joined.year) * 12 + (
        now.month - user.date_joined.month
    )
    if months_since < 1:
        months_since = 1
    average_monthly = total_earned / months_since

    return render(
        request,
        "developers/earnings.html",
        {
            "total_earned": total_earned,
            "months_since": months_since,
            "average_monthly": average_monthly,
        },
    )


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    tasks = Task.objects.filter(project=project, owner=request.user).order_by(
        "-created_at"
    )

    completed_tasks_count = tasks.filter(is_completed=True).count()
    has_active_timers = tasks.filter(is_timer_running=True).exists()
    other_timer_running = (
        Task.objects.filter(owner=request.user, is_timer_running=True)
        .exclude(project=project)
        .exists()
    )

    # Подсчёт подзадач
    total_subtasks = 0
    completed_subtasks = 0
    for task in tasks:
        subs = task.sub_tasks.all()
        total_subtasks += subs.count()
        completed_subtasks += subs.filter(is_completed=True).count()

    total_items = (
        completed_tasks_count + total_subtasks
    )  # общее кол-во элементов для прогресса
    completed_items = completed_tasks_count + completed_subtasks
    overall_completion = (
        int((completed_items / total_items * 100)) if total_items > 0 else 0
    )

    active_tab = request.GET.get("tab", "timer")

    context = {
        "project": project,
        "tasks": tasks,
        "completed_tasks_count": completed_tasks_count,
        "total_subtasks": total_subtasks,
        "completed_subtasks": completed_subtasks,
        "overall_completion": overall_completion,
        "timer_tasks": tasks,
        "project_tasks": tasks,
        "active_tab": active_tab,
        "has_active_timers": has_active_timers,
        "other_timer_running": other_timer_running,
    }
    return render(request, "developers/project_detail.html", context)


@login_required
def daily_tasks(request):
    """Страница «Ежедневные задачи» (задачи без проекта)."""
    tasks = Task.objects.filter(owner=request.user, project__isnull=True)
    completed_count = tasks.filter(is_completed=True).count()
    total_count = tasks.count()
    completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0

    context = {
        "daily_tasks": tasks,
        "completed_tasks_count": completed_count,
        "completion_rate": round(completion_rate),
        "total_subtasks": 0,
        "completed_subtasks": 0,
    }
    return render(request, "developers/daily_tasks.html", context)

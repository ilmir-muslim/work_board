import json
from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from .models import (
    DailyWorkSession,
    Project,
    Task,
    SubTask,
    TaskComment,
    SubTaskComment,
)


@login_required
@require_POST
def api_create_project(request):
    data = json.loads(request.body)
    name = data.get("name")
    if not name:
        return JsonResponse({"error": "Name required"}, status=400)
    project = Project.objects.create(
        name=name, owner=request.user, hourly_rate=request.user.default_hourly_rate
    )
    return JsonResponse({"id": project.id, "name": project.name})


@login_required
@require_POST
def api_start_timer(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)

    # Остановить все другие таймеры пользователя
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

    if not task.is_timer_running:
        task.is_timer_running = True
        task.last_start_time = timezone.now()
        task.save()

        # Дневная сессия
        today = timezone.now().date()
        session, created = DailyWorkSession.objects.get_or_create(
            user=request.user, date=today
        )
        if not session.is_timer_running:
            session.is_timer_running = True
            session.last_start_time = timezone.now()
            session.save()

    return JsonResponse(
        {
            "success": True,
            "total_time": task.total_time_with_current,
            "is_timer_running": task.is_timer_running,
        }
    )


@login_required
@require_POST
def api_pause_timer(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    if task.is_timer_running and task.last_start_time:
        elapsed = (timezone.now() - task.last_start_time).total_seconds()
        task.total_time = (task.total_time or 0) + elapsed
    task.is_timer_running = False
    task.last_start_time = None
    task.save()

    # Если больше нет запущенных задач, остановить дневную сессию
    if not Task.objects.filter(owner=request.user, is_timer_running=True).exists():
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

    return JsonResponse(
        {
            "success": True,
            "total_time": task.total_time_with_current,
            "is_timer_running": False,
        }
    )


@login_required
@require_POST
def api_stop_all_timers(request):
    tasks = Task.objects.filter(owner=request.user, is_timer_running=True)
    for task in tasks:
        if task.last_start_time:
            elapsed = (timezone.now() - task.last_start_time).total_seconds()
            task.total_time = (task.total_time or 0) + elapsed
        task.is_timer_running = False
        task.last_start_time = None
    Task.objects.bulk_update(
        tasks, ["total_time", "is_timer_running", "last_start_time"]
    )

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

    return JsonResponse({"success": True})


@login_required
@require_POST
def api_create_task(request):
    data = json.loads(request.body)
    title = data.get("title", "").strip()
    project_id = data.get("project_id", None)
    if not title:
        return JsonResponse({"error": "title required"}, status=400)
    task = Task.objects.create(
        title=title,
        owner=request.user,
        project_id=project_id if project_id else None,
        priority=data.get("priority", 2),
        due_date=data.get("due_date", None),
    )
    return JsonResponse(
        {
            "id": task.id,
            "title": task.title,
            "is_timer_running": task.is_timer_running,
            "total_time": task.total_time,
        }
    )


@login_required
@require_GET
def api_get_task_current_time(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    total = task.total_time_with_current
    hours = int(total // 3600)
    minutes = int((total % 3600) // 60)
    seconds = int(total % 60)
    return JsonResponse(
        {
            "total_time": total,
            "total_time_formatted": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "is_timer_running": task.is_timer_running,
        }
    )


@login_required
@require_POST
def api_delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    task.delete()
    return JsonResponse({"success": True})


@login_required
@require_POST
def api_update_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    data = json.loads(request.body)
    if "is_completed" in data:
        task.is_completed = data["is_completed"]
        if task.is_completed:
            task.completed_at = timezone.now()
    if "title" in data:
        task.title = data["title"]
    if "priority" in data:
        task.priority = data["priority"]
    if "due_date" in data:
        task.due_date = data["due_date"] if data["due_date"] else None
    task.save()
    return JsonResponse({"success": True})


# Подзадачи
@login_required
@require_POST
def api_create_subtask(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    data = json.loads(request.body)
    title = data.get("title", "").strip()
    if not title:
        return JsonResponse({"error": "title required"}, status=400)
    subtask = SubTask.objects.create(task=task, title=title)
    return JsonResponse({"id": subtask.id, "title": subtask.title})


@login_required
@require_POST
def api_update_subtask(request, subtask_id):
    subtask = get_object_or_404(SubTask, pk=subtask_id, task__owner=request.user)
    data = json.loads(request.body)
    if "title" in data:
        subtask.title = data["title"]
    if "is_completed" in data:
        subtask.is_completed = data["is_completed"]
        if subtask.is_completed:
            subtask.completed_at = timezone.now()
    subtask.save()
    return JsonResponse({"success": True})


@login_required
@require_POST
def api_delete_subtask(request, subtask_id):
    subtask = get_object_or_404(SubTask, pk=subtask_id, task__owner=request.user)
    subtask.delete()
    return JsonResponse({"success": True})


# Комментарии к задачам
@login_required
@require_POST
def api_create_task_comment(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    data = json.loads(request.body)
    content = data.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "content required"}, status=400)
    comment = TaskComment.objects.create(task=task, content=content)
    return JsonResponse({"id": comment.id, "content": comment.content})


@login_required
@require_POST
def api_delete_task_comment(request, comment_id):
    comment = get_object_or_404(TaskComment, pk=comment_id, task__owner=request.user)
    comment.delete()
    return JsonResponse({"success": True})


# Комментарии к подзадачам
@login_required
@require_POST
def api_create_subtask_comment(request, subtask_id):
    subtask = get_object_or_404(SubTask, pk=subtask_id, task__owner=request.user)
    data = json.loads(request.body)
    content = data.get("content", "").strip()
    if not content:
        return JsonResponse({"error": "content required"}, status=400)
    comment = SubTaskComment.objects.create(sub_task=subtask, content=content)
    return JsonResponse({"id": comment.id, "content": comment.content})


@login_required
@require_POST
def api_delete_subtask_comment(request, comment_id):
    comment = get_object_or_404(
        SubTaskComment, pk=comment_id, sub_task__task__owner=request.user
    )
    comment.delete()
    return JsonResponse({"success": True})


# Проекты
@login_required
@require_POST
def api_update_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    data = json.loads(request.body)
    if "name" in data:
        project.name = data["name"]
    if "hourly_rate" in data:
        # Очищаем от возможного суффикса "₽/ч" и пробелов
        raw = data["hourly_rate"]
        if isinstance(raw, str):
            raw = raw.replace("₽/ч", "").replace("₽", "").replace("/ч", "").strip()
        project.hourly_rate = float(raw)
    project.save()
    return JsonResponse({"success": True})


@login_required
@require_POST
def api_delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    project.delete()
    return JsonResponse({"success": True})


@login_required
@require_POST
def api_transfer_previous_week_tasks(request):
    # Перенос незавершённых задач с прошлой недели на эту
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # понедельник этой недели
    end_of_prev_week = start_of_week - timedelta(days=1)
    start_of_prev_week = end_of_prev_week - timedelta(days=6)
    tasks = Task.objects.filter(
        owner=request.user,
        project__isnull=True,
        is_completed=False,
        due_date__isnull=False,
        due_date__date__gte=start_of_prev_week,
        due_date__date__lte=end_of_prev_week,
    )
    count = tasks.count()
    for task in tasks:
        task.due_date = task.due_date + timedelta(days=7)
        task.save()
    return JsonResponse({"success": True, "transferred": count})


@login_required
@require_GET
def api_earnings_widget(request):
    from core.context_processors import earnings_summary as proc

    data = proc(request)
    return JsonResponse(data)


@login_required
@require_GET
def api_daily_stats_widget(request):
    today = timezone.now().date()
    try:
        session = DailyWorkSession.objects.get(user=request.user, date=today)
        current_seconds = session.total_with_current
        is_timer_running = session.is_timer_running
    except DailyWorkSession.DoesNotExist:
        current_seconds = 0
        is_timer_running = False

    end_date = today
    start_date = end_date - timedelta(days=6)
    week_sessions = DailyWorkSession.objects.filter(
        user=request.user, date__range=[start_date, end_date]
    )
    week_data = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        sess = week_sessions.filter(date=day).first()
        week_data.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "total_seconds": int(sess.total_with_current) if sess else 0,
            }
        )
    max_week_seconds = max((d["total_seconds"] for d in week_data), default=0)
    week_total = sum(d["total_seconds"] for d in week_data)

    return JsonResponse(
        {
            "current_daily_seconds": int(current_seconds),
            "is_daily_timer_running": is_timer_running,
            "week_stats": week_data,
            "week_total": week_total,
            "max_week_seconds": max_week_seconds,
        }
    )

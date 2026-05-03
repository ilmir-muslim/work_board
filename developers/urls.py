from django.urls import path
from developers.api import (
    api_create_project,
    api_start_timer,
    api_pause_timer,
    api_stop_all_timers,
    api_create_task,
    api_get_task_current_time,
    api_delete_task,
    api_update_task,
    api_create_subtask,
    api_update_subtask,
    api_delete_subtask,
    api_create_task_comment,
    api_delete_task_comment,
    api_create_subtask_comment,
    api_delete_subtask_comment,
    api_update_project,
    api_delete_project,
    api_transfer_previous_week_tasks,
)
from . import views

app_name = "developers"

urlpatterns = [
    # Проекты
    path("projects/", views.project_list, name="project_list"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/create/", views.project_create, name="project_create"),
    path("projects/<int:pk>/update/", views.project_update, name="project_update"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),
    # Задачи
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/<int:pk>/", views.task_detail, name="task_detail"),
    path("tasks/create/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/update/", views.task_update, name="task_update"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
    # Таймеры (через обычные views)
    path("timer/start/<int:task_id>/", views.start_timer, name="start_timer"),
    path("timer/pause/<int:task_id>/", views.pause_timer, name="pause_timer"),
    path("timer/stop-all/", views.stop_all_timers, name="stop_all_timers"),
    # Подзадачи
    path(
        "tasks/<int:task_id>/subtasks/create/",
        views.sub_task_create,
        name="sub_task_create",
    ),
    path("subtasks/<int:pk>/update/", views.sub_task_update, name="sub_task_update"),
    path("subtasks/<int:pk>/delete/", views.sub_task_delete, name="sub_task_delete"),
    # Комментарии к задачам
    path(
        "tasks/<int:task_id>/comments/create/",
        views.task_comment_create,
        name="task_comment_create",
    ),
    path(
        "comments/<int:pk>/delete/",
        views.task_comment_delete,
        name="task_comment_delete",
    ),
    # Комментарии к подзадачам
    path(
        "subtasks/<int:sub_task_id>/comments/create/",
        views.sub_task_comment_create,
        name="sub_task_comment_create",
    ),
    path(
        "subtask-comments/<int:pk>/delete/",
        views.sub_task_comment_delete,
        name="sub_task_comment_delete",
    ),
    # Статистика
    path("stats/daily/", views.daily_stats, name="daily_stats"),
    path("earnings/", views.earnings_summary, name="earnings"),
    # Ежедневные задачи
    path("daily-tasks/", views.daily_tasks, name="daily_tasks"),
    # API
    path("api/projects/create/", api_create_project, name="api_create_project"),
    path("api/timer/start/<int:task_id>/", api_start_timer, name="api_start_timer"),
    path("api/timer/pause/<int:task_id>/", api_pause_timer, name="api_pause_timer"),
    path("api/timer/stop-all/", api_stop_all_timers, name="api_stop_all_timers"),
    path("api/tasks/create/", api_create_task, name="api_create_task"),
    path("api/tasks/<int:task_id>/update/", api_update_task, name="api_update_task"),
    path("api/tasks/<int:task_id>/delete/", api_delete_task, name="api_delete_task"),
    path(
        "api/task-current-time/<int:task_id>/",
        api_get_task_current_time,
        name="api_task_current_time",
    ),
    # API подзадач
    path(
        "api/tasks/<int:task_id>/subtasks/create/",
        api_create_subtask,
        name="api_create_subtask",
    ),
    path(
        "api/subtasks/<int:subtask_id>/update/",
        api_update_subtask,
        name="api_update_subtask",
    ),
    path(
        "api/subtasks/<int:subtask_id>/delete/",
        api_delete_subtask,
        name="api_delete_subtask",
    ),
    # API комментариев
    path(
        "api/tasks/<int:task_id>/comments/create/",
        api_create_task_comment,
        name="api_create_task_comment",
    ),
    path(
        "api/task-comments/<int:comment_id>/delete/",
        api_delete_task_comment,
        name="api_delete_task_comment",
    ),
    path(
        "api/subtasks/<int:subtask_id>/comments/create/",
        api_create_subtask_comment,
        name="api_create_subtask_comment",
    ),
    path(
        "api/subtask-comments/<int:comment_id>/delete/",
        api_delete_subtask_comment,
        name="api_delete_subtask_comment",
    ),
    # API проектов
    path(
        "api/projects/<int:project_id>/update/",
        api_update_project,
        name="api_update_project",
    ),
    path(
        "api/projects/<int:project_id>/delete/",
        api_delete_project,
        name="api_delete_project",
    ),
    # Перенос незавершённых задач с прошлой недели
    path(
        "api/tasks/transfer-previous-week/",
        api_transfer_previous_week_tasks,
        name="api_transfer_previous_week",
    ),
]

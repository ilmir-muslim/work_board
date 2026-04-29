from django.urls import path

from developers.api import api_create_project
from . import views

app_name = "developers"

urlpatterns = [
    # Проекты
    path("projects/", views.project_list, name="project_list"),
    path("projects/create/", views.project_create, name="project_create"),
    path("projects/<int:pk>/update/", views.project_update, name="project_update"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),
    # Задачи
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/<int:pk>/", views.task_detail, name="task_detail"),
    path("tasks/create/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/update/", views.task_update, name="task_update"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
    # Таймеры
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
    path(
        "api/projects/create/", api_create_project, name="api_create_project"
    ),
]

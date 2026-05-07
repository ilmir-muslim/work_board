# managers/urls.py
from django.urls import path
from managers.api import (
    api_create_assigned_task,
    api_create_project_assignment,  # <-- правильное имя
    api_user_projects,
)
from . import views

app_name = "managers"

urlpatterns = [
    # Разработчики
    path("", views.developer_list, name="developer_list"),
    path(
        "developers/<int:user_id>/projects/",
        views.developer_projects,
        name="developer_projects",
    ),
    path(
        "developers/<int:user_id>/projects/<int:project_id>/",
        views.developer_project_detail,
        name="developer_project_detail",
    ),
    # Назначенные задачи
    path("assigned-tasks/", views.assigned_task_list, name="assigned_task_list"),
    path(
        "assigned-tasks/create/",
        views.assigned_task_create,
        name="assigned_task_create",
    ),
    path(
        "assigned-tasks/<int:task_id>/",
        views.assigned_task_detail,
        name="assigned_task_detail",
    ),
    # Назначение проектов (обычная форма)
    path(
        "project-assignments/create/",
        views.project_assignment_create,
        name="project_assignment_create",
    ),
    # Уведомления
    path("notifications/", views.notification_list, name="notification_list"),
    # API
    path(
        "api/tasks/create/", api_create_assigned_task, name="api_create_assigned_task"
    ),
    path(
        "api/projects/create/",
        api_create_project_assignment,
        name="api_create_project_assignment",
    ),
    path(
        "api/user-projects/<int:user_id>/", api_user_projects, name="api_user_projects"
    ),
]

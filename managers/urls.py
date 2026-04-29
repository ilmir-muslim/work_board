from django.urls import path
from . import views

app_name = "managers"

urlpatterns = [
    # Назначенные задачи
    path("assigned-tasks/", views.assigned_task_list, name="assigned_task_list"),
    path(
        "assigned-tasks/create/",
        views.assigned_task_create,
        name="assigned_task_create",
    ),
    path(
        "assigned-tasks/<int:pk>/update/",
        views.assigned_task_update,
        name="assigned_task_update",
    ),
    path(
        "assigned-tasks/<int:pk>/delete/",
        views.assigned_task_delete,
        name="assigned_task_delete",
    ),
    path(
        "assigned-tasks/<int:pk>/accept/",
        views.accept_assigned_task,
        name="accept_assigned_task",
    ),
    # Назначения проектов
    path(
        "project-assignments/create/",
        views.project_assignment_create,
        name="project_assignment_create",
    ),
    path(
        "project-assignments/<int:pk>/accept/",
        views.accept_project_assignment,
        name="accept_project_assignment",
    ),
    # Уведомления
    path("notifications/", views.notification_list, name="notification_list"),
    path(
        "notifications/<int:pk>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
]

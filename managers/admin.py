# managers/admin.py
from django.contrib import admin
from .models import AssignedTask, ProjectAssignment, Notification, AssignmentAttachment


@admin.register(AssignedTask)
class AssignedTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "creator", "assignee", "status", "project", "created_at")
    list_filter = ("status", "creator", "assignee")
    search_fields = ("title", "description")


@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "status", "created_at")
    list_filter = ("status", "user")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "title", "is_read", "created_at")
    list_filter = ("is_read", "type")


@admin.register(AssignmentAttachment)
class AssignmentAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "assigned_task",
        "project_assignment",
        "original_filename",
        "uploaded_at",
    )
    search_fields = ("original_filename",)

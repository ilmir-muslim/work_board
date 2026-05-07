# developers/admin.py
from django.contrib import admin
from .models import (
    Project,
    Task,
    SubTask,
    TaskComment,
    SubTaskComment,
    DailyWorkSession,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "hourly_rate", "created_at")
    search_fields = ("name", "owner__username")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "project",
        "is_completed",
        "priority",
        "total_time",
    )
    list_filter = ("is_completed", "owner", "project")


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "task", "is_completed")


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ("task", "content_short", "created_at")

    def content_short(self, obj):
        return obj.content[:50]


@admin.register(SubTaskComment)
class SubTaskCommentAdmin(admin.ModelAdmin):
    pass


@admin.register(DailyWorkSession)
class DailyWorkSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "total_time", "is_timer_running")

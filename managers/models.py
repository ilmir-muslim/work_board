import uuid
from django.db import models
from django.conf import settings


class AssignedTask(models.Model):
    STATUS_CHOICES = (
        ("pending", "Ожидает"),
        ("accepted", "Принята"),
        ("rejected", "Отклонена"),
        ("completed", "Выполнена"),
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_assigned_tasks",
        verbose_name="Создатель",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_tasks",
        verbose_name="Исполнитель",
    )
    project = models.ForeignKey(
        "developers.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Проект",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    group_id = models.UUIDField(
        default=uuid.uuid4, editable=False, db_index=True, verbose_name="ID группы"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Назначенная задача"
        verbose_name_plural = "Назначенные задачи"

    def __str__(self):
        return f"{self.title} -> {self.assignee}"


class ProjectAssignment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Ожидает"),
        ("accepted", "Принят"),
        ("rejected", "Отклонён"),
    )
    project = models.ForeignKey(
        "developers.Project",
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Проект",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_assignments",
        verbose_name="Пользователь",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    group_id = models.UUIDField(
        default=uuid.uuid4, editable=False, db_index=True, verbose_name="ID группы"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Назначение проекта"
        verbose_name_plural = "Назначения проектов"

    def __str__(self):
        return f"{self.project} -> {self.user}"


class Notification(models.Model):
    TYPE_CHOICES = (
        ("task_accepted", "Задача принята"),
        ("task_completed", "Задача выполнена"),
        ("project_accepted", "Проект принят"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Получатель",
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
        verbose_name="От кого",
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="Тип")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    message = models.TextField(verbose_name="Сообщение")
    related_id = models.IntegerField(
        null=True, blank=True, verbose_name="ID связанной сущности"
    )
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return f"{self.user}: {self.title}"

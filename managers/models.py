# managers/models.py
import uuid
from django.db import models
from django.conf import settings


class AssignedTask(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("accepted", "Принята"),
        ("rejected", "Отклонена"),
        ("completed", "Завершена"),
    ]

    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_assigned_tasks",
        verbose_name="Создатель (менеджер)",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_tasks",
        verbose_name="Исполнитель (разработчик)",
    )
    project = models.ForeignKey(
        "developers.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name="Проект разработчика",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус"
    )
    group_id = models.UUIDField(
        default=uuid.uuid4, editable=False, verbose_name="ID группы"
    )
    is_completed = models.BooleanField(default=False, verbose_name="Завершена")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Принята")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Завершена")

    class Meta:
        verbose_name = "Назначенная задача"
        verbose_name_plural = "Назначенные задачи"

    def __str__(self):
        return f"{self.title} → {self.assignee}"


class ProjectAssignment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает"),
        ("accepted", "Принят"),
        ("rejected", "Отклонён"),
    ]

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
        verbose_name="Разработчик",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Статус"
    )
    group_id = models.UUIDField(
        default=uuid.uuid4, editable=False, verbose_name="ID группы"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Принято")

    class Meta:
        verbose_name = "Назначение проекта"
        verbose_name_plural = "Назначения проектов"

    def __str__(self):
        return f"{self.project} → {self.user}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Получатель",
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
        verbose_name="Отправитель",
    )
    type = models.CharField(max_length=50, verbose_name="Тип")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    message = models.TextField(blank=True, verbose_name="Сообщение")
    related_id = models.IntegerField(null=True, blank=True, verbose_name="Связанный ID")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def __str__(self):
        return f"Для {self.user}: {self.title}"


class AssignmentAttachment(models.Model):
    assigned_task = models.ForeignKey(
        AssignedTask,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
        verbose_name="Назначенная задача",
    )
    project_assignment = models.ForeignKey(
        ProjectAssignment,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
        verbose_name="Назначение проекта",
    )
    file = models.FileField(upload_to="assignments/%Y/%m/%d/", verbose_name="Файл")
    original_filename = models.CharField(
        max_length=255, blank=True, verbose_name="Оригинальное имя"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Загружен")

    class Meta:
        verbose_name = "Прикреплённый файл"
        verbose_name_plural = "Прикреплённые файлы"

    def __str__(self):
        return f"Файл для {self.assigned_task or self.project_assignment}"

    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = self.file.name.split("/")[-1]
        super().save(*args, **kwargs)

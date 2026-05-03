from django.db import models
from django.conf import settings
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Владелец",
    )
    hourly_rate = models.FloatField(default=0.0, verbose_name="Часовая ставка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    def __str__(self):
        return self.name

    @property
    def total_time(self):
        """Общее время по всем задачам проекта (в секундах) с учётом текущих запущенных."""
        total = 0
        for task in self.tasks.all():
            total += task.total_time_with_current
        return total

    @property
    def earned_amount(self):
        """Заработанная сумма = total_time * hourly_rate / 3600"""
        return self.total_time * self.hourly_rate / 3600

    @property
    def formatted_total_time(self):
        """Возвращает общее время в формате ЧЧ:ММ:СС"""
        total_seconds = int(self.total_time)  # total_time уже float
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class Task(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Проект",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_tasks",
        verbose_name="Владелец",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    is_completed = models.BooleanField(default=False, verbose_name="Завершена")
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Завершена в"
    )
    priority = models.IntegerField(default=1, verbose_name="Приоритет")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Срок")

    total_time = models.FloatField(default=0.0, verbose_name="Всего времени (сек)")
    is_timer_running = models.BooleanField(default=False, verbose_name="Таймер запущен")
    last_start_time = models.DateTimeField(
        null=True, blank=True, verbose_name="Последний старт"
    )

    assigned_task = models.ForeignKey(
        "managers.AssignedTask",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Связанная назначенная задача",
    )

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self):
        return self.title

    @property
    def total_time_with_current(self):
        """Общее время с учётом текущей запущенной сессии."""
        t = self.total_time or 0
        if self.is_timer_running and self.last_start_time:
            t += (timezone.now() - self.last_start_time).total_seconds()
        return t

    @property
    def formatted_total_time(self):
        """Сохранённое время (без текущей сессии) в ЧЧ:ММ:СС"""
        t = int(self.total_time or 0)
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def formatted_total_time_with_current(self):
        """Полное время с учётом запущенного таймера в ЧЧ:ММ:СС"""
        t = int(self.total_time_with_current)
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

class SubTask(models.Model):
    title = models.CharField(max_length=500, verbose_name="Название")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="sub_tasks")
    is_completed = models.BooleanField(default=False, verbose_name="Завершена")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Подзадача"
        verbose_name_plural = "Подзадачи"

    def __str__(self):
        return self.title


class TaskComment(models.Model):
    content = models.TextField(verbose_name="Комментарий")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий к задаче"
        verbose_name_plural = "Комментарии к задачам"

    def __str__(self):
        return f"Комментарий к {self.task}"


class SubTaskComment(models.Model):
    content = models.TextField(verbose_name="Комментарий")
    sub_task = models.ForeignKey(
        SubTask, on_delete=models.CASCADE, related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий к подзадаче"
        verbose_name_plural = "Комментарии к подзадачам"


class DailyWorkSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_sessions",
        verbose_name="Пользователь",
    )
    date = models.DateField(verbose_name="Дата")
    total_time = models.FloatField(default=0.0, verbose_name="Всего секунд")
    is_timer_running = models.BooleanField(default=False, verbose_name="Таймер запущен")
    last_start_time = models.DateTimeField(
        null=True, blank=True, verbose_name="Последний старт"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "date")
        verbose_name = "Дневная сессия"
        verbose_name_plural = "Дневные сессии"

    def __str__(self):
        return f"{self.user} – {self.date}"

    @property
    def total_with_current(self):
        t = self.total_time
        if self.is_timer_running and self.last_start_time:
            t += (timezone.now() - self.last_start_time).total_seconds()
        return t

import sqlite3
import uuid
from datetime import datetime, timezone, date
from django.core.management.base import BaseCommand
from users.models import User
from developers.models import (
    Project,
    Task,
    SubTask,
    TaskComment,
    SubTaskComment,
    DailyWorkSession,
)
from managers.models import AssignedTask, ProjectAssignment, Notification


def parse_datetime(val):
    if val is None:
        return None
    try:
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = "Импорт данных из старой SQLite базы (FastAPI/SQLAlchemy)"

    def add_arguments(self, parser):
        parser.add_argument(
            "old_db_path", type=str, help="Путь к файлу старой базы SQLite"
        )

    def handle(self, *args, **options):
        old_db = options["old_db_path"]
        conn = sqlite3.connect(old_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # ---------- Пользователь ----------
        old_user = cursor.execute("SELECT * FROM users WHERE id = 1").fetchone()
        if not old_user:
            self.stderr.write("Пользователь id=1 не найден в старой базе")
            return

        django_user, created = User.objects.get_or_create(
            username=old_user["username"],
            defaults={
                "default_hourly_rate": old_user["default_hourly_rate"] or 0.0,
                "password": "pbkdf2_sha256$...",
            },
        )
        if not created:
            django_user.default_hourly_rate = old_user["default_hourly_rate"] or 0.0
            django_user.save()

        # ---------- Проекты ----------
        project_map = {}
        for op in cursor.execute("SELECT * FROM projects"):
            p = Project.objects.create(
                name=op["name"],
                owner=django_user,
                hourly_rate=op["hourly_rate"],
            )
            if op["created_at"]:
                dt = parse_datetime(op["created_at"])
                if dt:
                    Project.objects.filter(pk=p.pk).update(created_at=dt)
            project_map[op["id"]] = p
        self.stdout.write(f"Проекты: {len(project_map)}")

        # ---------- Назначенные задачи ----------
        assigned_map = {}
        for oa in cursor.execute("SELECT * FROM assigned_tasks"):
            project = project_map.get(oa["project_id"])
            gid = oa["group_id"]
            try:
                gid = uuid.UUID(gid) if gid else uuid.uuid4()
            except (ValueError, AttributeError):
                gid = uuid.uuid4()
            a = AssignedTask.objects.create(
                title=oa["title"],
                description=oa["description"] or "",
                creator=django_user,
                assignee=django_user,
                project=project,
                status=oa["status"] or "pending",
                group_id=gid,
                is_completed=bool(oa["is_completed"]),
            )
            if oa["created_at"]:
                dt = parse_datetime(oa["created_at"])
                if dt:
                    AssignedTask.objects.filter(pk=a.pk).update(created_at=dt)
            if oa["accepted_at"]:
                a.accepted_at = parse_datetime(oa["accepted_at"])
                a.save()
            if oa["completed_at"]:
                a.completed_at = parse_datetime(oa["completed_at"])
                a.save()
            assigned_map[oa["id"]] = a
        self.stdout.write(f"Назначенные задачи: {len(assigned_map)}")

        # ---------- Задачи ----------
        task_map = {}
        for ot in cursor.execute("SELECT * FROM tasks"):
            project = project_map.get(ot["project_id"])
            t = Task.objects.create(
                title=ot["title"],
                owner=django_user,
                project=project,
                is_completed=bool(ot["is_completed"]),
                priority=ot["priority"] or 1,
                total_time=ot["total_time"] or 0.0,
                is_timer_running=bool(ot["is_timer_running"]),
            )
            if ot["completed_at"]:
                t.completed_at = parse_datetime(ot["completed_at"])
            if ot["due_date"]:
                t.due_date = parse_datetime(ot["due_date"])
            if ot["last_start_time"]:
                t.last_start_time = parse_datetime(ot["last_start_time"])
            t.save()
            if ot["created_at"]:
                dt = parse_datetime(ot["created_at"])
                if dt:
                    Task.objects.filter(pk=t.pk).update(created_at=dt)
            task_map[ot["id"]] = t

            # Связь с assigned_task
            if ot["assigned_task_id"] and ot["assigned_task_id"] in assigned_map:
                t.assigned_task = assigned_map[ot["assigned_task_id"]]
                t.save()
        self.stdout.write(f"Задачи: {len(task_map)}")

        # ---------- Подзадачи ----------
        subtask_map = {}
        for osub in cursor.execute("SELECT * FROM sub_tasks"):
            parent_task = task_map.get(osub["task_id"])
            if not parent_task:
                continue
            s = SubTask.objects.create(
                task=parent_task,
                title=osub["title"],
                is_completed=bool(osub["is_completed"]),
            )
            if osub["completed_at"]:
                s.completed_at = parse_datetime(osub["completed_at"])
                s.save()
            if osub["created_at"]:
                dt = parse_datetime(osub["created_at"])
                if dt:
                    SubTask.objects.filter(pk=s.pk).update(created_at=dt)
            subtask_map[osub["id"]] = s
        self.stdout.write(f"Подзадачи: {len(subtask_map)}")

        # ---------- Комментарии к задачам ----------
        for otc in cursor.execute("SELECT * FROM task_comments"):
            task = task_map.get(otc["task_id"])
            if task:
                c = TaskComment.objects.create(task=task, content=otc["content"])
                if otc["created_at"]:
                    dt = parse_datetime(otc["created_at"])
                    if dt:
                        TaskComment.objects.filter(pk=c.pk).update(created_at=dt)

        # ---------- Комментарии к подзадачам ----------
        for osc in cursor.execute("SELECT * FROM sub_task_comments"):
            sub = subtask_map.get(osc["sub_task_id"])
            if sub:
                c = SubTaskComment.objects.create(sub_task=sub, content=osc["content"])
                if osc["created_at"]:
                    dt = parse_datetime(osc["created_at"])
                    if dt:
                        SubTaskComment.objects.filter(pk=c.pk).update(created_at=dt)

        # ---------- Ежедневные сессии ----------
        for osess in cursor.execute("SELECT * FROM daily_work_sessions"):
            date_val = osess["date"]
            try:
                if isinstance(date_val, str):
                    d = datetime.strptime(date_val[:10], "%Y-%m-%d").date()
                else:
                    d = date.fromtimestamp(date_val)  # на всякий случай
            except (ValueError, TypeError):
                continue
            defaults = {
                "total_time": osess["total_time"] or 0.0,
                "is_timer_running": bool(osess["is_timer_running"]),
            }
            sess, _ = DailyWorkSession.objects.get_or_create(
                user=django_user, date=d, defaults=defaults
            )
            if osess["last_start_time"]:
                dt = parse_datetime(osess["last_start_time"])
                if dt:
                    sess.last_start_time = dt
                    sess.save()
        self.stdout.write("Ежедневные сессии импортированы")

        # ---------- Назначения проектов ----------
        for opa in cursor.execute("SELECT * FROM project_assignments"):
            project = project_map.get(opa["project_id"])
            if not project:
                continue
            gid = opa["group_id"]
            try:
                gid = uuid.UUID(gid) if gid else uuid.uuid4()
            except (ValueError, AttributeError):
                gid = uuid.uuid4()
            pa = ProjectAssignment.objects.create(
                project=project,
                user=django_user,
                status=opa["status"] or "pending",
                group_id=gid,
            )
            if opa["created_at"]:
                dt = parse_datetime(opa["created_at"])
                if dt:
                    ProjectAssignment.objects.filter(pk=pa.pk).update(created_at=dt)
            if opa["accepted_at"]:
                pa.accepted_at = parse_datetime(opa["accepted_at"])
                pa.save()
        self.stdout.write("Назначения проектов импортированы")

        # ---------- Уведомления ----------
        for onot in cursor.execute("SELECT * FROM notifications"):
            Notification.objects.create(
                user=django_user,
                from_user=django_user,
                type=onot["type"],
                title=onot["title"],
                message=onot["message"],
                related_id=onot["related_id"],
                is_read=bool(onot["is_read"]),
            )
        self.stdout.write("Уведомления импортированы")

        conn.close()
        self.stdout.write(self.style.SUCCESS("Импорт завершён!"))

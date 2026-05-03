from developers.models import DailyWorkSession, Project
from django.utils import timezone
from datetime import timedelta


def earnings_summary(request):
    if not request.user.is_authenticated:
        return {}
    user = request.user
    projects = Project.objects.filter(owner=user)
    total_earned = sum(p.earned_amount for p in projects)
    now = timezone.now()
    months_since = (now.year - user.date_joined.year) * 12 + (
        now.month - user.date_joined.month
    ) or 1
    average_monthly = total_earned / months_since
    return {
        "total_earned": total_earned,
        "average_monthly": average_monthly,
        "months_since": months_since,
    }


def daily_stats(request):
    if not request.user.is_authenticated:
        return {}
    today = timezone.now().date()
    try:
        session = DailyWorkSession.objects.get(user=request.user, date=today)
        current_seconds = session.total_with_current
        is_timer_running = session.is_timer_running
    except DailyWorkSession.DoesNotExist:
        current_seconds = 0
        is_timer_running = False

    end_date = today
    start_date = end_date - timedelta(days=6)
    week_sessions = DailyWorkSession.objects.filter(
        user=request.user, date__range=[start_date, end_date]
    )
    week_data = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        sess = week_sessions.filter(date=day).first()
        week_data.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "total_seconds": sess.total_with_current if sess else 0,
            }
        )
    max_week_seconds = max((d["total_seconds"] for d in week_data), default=0)
    week_total = sum(d["total_seconds"] for d in week_data)

    # Форматирование времени в ЧЧ:ММ:СС
    def fmt(sec):
        h, rem = divmod(int(sec), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    return {
        "current_daily_seconds": current_seconds,
        "current_daily_formatted": fmt(current_seconds),
        "is_daily_timer_running": is_timer_running,
        "week_stats": week_data,
        "week_total": week_total,
        "week_total_formatted": fmt(week_total),
        "max_week_seconds": max_week_seconds,
    }

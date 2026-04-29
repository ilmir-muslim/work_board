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
    # Текущая сессия
    today = timezone.now().date()
    try:
        session = DailyWorkSession.objects.get(user=request.user, date=today)
        current_seconds = session.total_with_current
    except DailyWorkSession.DoesNotExist:
        current_seconds = 0

    # Последние 7 дней
    end_date = timezone.now().date()
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

    # Последние 30 дней
    start_date_30 = end_date - timedelta(days=29)
    month_sessions = DailyWorkSession.objects.filter(
        user=request.user, date__range=[start_date_30, end_date]
    )
    month_data = []
    for i in range(30):
        day = start_date_30 + timedelta(days=i)
        sess = month_sessions.filter(date=day).first()
        month_data.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "total_seconds": sess.total_with_current if sess else 0,
            }
        )

    return {
        "current_daily_seconds": current_seconds,
        "week_stats": week_data,
        "month_stats": month_data,
    }

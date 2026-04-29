from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_redirect(request):
    """Перенаправляет пользователя на его главную страницу в зависимости от роли."""
    if request.user.is_staff:
        return redirect("managers:assigned_task_list")
    else:
        return redirect("developers:project_list")

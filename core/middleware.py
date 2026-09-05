from django.contrib.auth import login
from django.conf import settings
from users.models import User


class AutoLoginMiddleware:
    """
    Автоматически логинит пользователя ilmir, если включен флаг AUTO_LOGIN_LOCAL
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            getattr(settings, "AUTO_LOGIN_LOCAL", False)
            and not request.user.is_authenticated
        ):
            # Ищем конкретно твоего пользователя
            user = User.objects.filter(username="ilmir").first()
            if user:
                login(request, user)
        return self.get_response(request)

from django.contrib import admin
from django.urls import path, include
from core.views import dashboard_redirect

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("developers/", include("developers.urls")),
    path("managers/", include("managers.urls")),
    path("", dashboard_redirect, name="dashboard"),
]

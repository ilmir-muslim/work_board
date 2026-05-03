from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from users.forms import CustomUserCreationForm


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})


@login_required
def profile(request):
    return render(request, "users/profile.html", {"user": request.user})


@login_required
def update_rate(request):
    if request.method == "POST":
        rate = request.POST.get("default_hourly_rate")
        if rate:
            request.user.default_hourly_rate = float(rate)
            request.user.save()
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Метод не поддерживается"}, status=405)

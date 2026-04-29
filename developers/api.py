from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Project, Task
import json


@login_required
@require_POST
def api_create_project(request):
    data = json.loads(request.body)
    name = data.get("name")
    if not name:
        return JsonResponse({"error": "Name required"}, status=400)
    project = Project.objects.create(
        name=name, owner=request.user, hourly_rate=request.user.default_hourly_rate
    )
    return JsonResponse({"id": project.id, "name": project.name})

from django import forms
from .models import Project, Task, SubTask, TaskComment, SubTaskComment


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "hourly_rate"]


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "project", "priority", "due_date"]
        widgets = {
            "due_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ["title", "is_completed"]


class CommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ["content"]

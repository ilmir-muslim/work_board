from django import forms
from .models import AssignedTask, ProjectAssignment
from users.models import User


class AssignedTaskForm(forms.ModelForm):
    assignees = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Исполнители",
    )

    class Meta:
        model = AssignedTask
        fields = ["title", "description", "project", "assignees"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields.pop("assignees")


class ProjectAssignmentForm(forms.Form):
    project = forms.ModelChoiceField(queryset=None, label="Проект")
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Пользователи",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

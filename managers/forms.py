# managers/forms.py
from django import forms
from .models import AssignedTask, ProjectAssignment
from users.models import User
from developers.models import Project


class AssignedTaskForm(forms.ModelForm):
    attachments = forms.FileField(required=False, label="Прикрепить файл")

    class Meta:
        model = AssignedTask
        fields = ["title", "description", "assignee", "project"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "assignee": forms.Select(attrs={"class": "form-control"}),
            "project": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].queryset = User.objects.filter(is_staff=False)
        self.fields["project"].queryset = Project.objects.all()
        self.fields["project"].required = False


class ProjectAssignmentForm(forms.ModelForm):
    name = forms.CharField(max_length=255, label="Название проекта")
    hourly_rate = forms.FloatField(min_value=0, initial=0, label="Ставка")
    assignee = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False), label="Исполнитель"
    )
    attachments = forms.FileField(required=False, label="Прикрепить файл")

    class Meta:
        model = ProjectAssignment
        fields = []

    def save(self, commit=True):
        project = Project.objects.create(
            name=self.cleaned_data["name"],
            owner=self.current_user,
            hourly_rate=self.cleaned_data["hourly_rate"],
        )
        assignment = ProjectAssignment(
            project=project, user=self.cleaned_data["assignee"], status="pending"
        )
        if commit:
            assignment.save()
        return assignment

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)

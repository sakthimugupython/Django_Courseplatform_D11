from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Course, StudentProgress, StudentProfile

ROLE_CHOICES = (
    ("student", "Student"),
    ("instructor", "Instructor"),
)


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2", "role")


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("title", "description", "is_published")


class EnrollStudentForm(forms.Form):
    username = forms.CharField(max_length=150, help_text="Username of the student to enroll")


class ProgressForm(forms.ModelForm):
    class Meta:
        model = StudentProgress
        fields = ("progress_percent",)
        widgets = {
            "progress_percent": forms.NumberInput(attrs={"min": 0, "max": 100})
        }

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    bio = models.TextField(_('Bio'), blank=True)

    def __str__(self) -> str:
        return f"StudentProfile({self.user.username})"


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    bio = models.TextField(_('Bio'), blank=True)

    def __str__(self) -> str:
        return f"InstructorProfile({self.user.username})"


class StudentProgress(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='progress_items')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='progress_entries', null=True, blank=True)
    course_name = models.CharField(max_length=255)
    progress_percent = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Student progress'
        unique_together = (('student', 'course'),)

    def __str__(self) -> str:
        name = self.course.title if self.course_id else self.course_name
        return f"{self.student.user.username} - {name}: {self.progress_percent}%"


class Course(models.Model):
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title

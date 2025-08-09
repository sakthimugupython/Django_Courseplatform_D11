from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import StudentProfile, StudentProgress


@receiver(post_delete, sender=StudentProfile)
def cleanup_student_progress(sender, instance: StudentProfile, **kwargs):
    # Ensure all progress entries are removed if a student profile is deleted
    StudentProgress.objects.filter(student=instance).delete()

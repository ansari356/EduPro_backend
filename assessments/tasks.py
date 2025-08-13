from celery import shared_task
from django.utils import timezone
from .models import StudentAssessmentAttempt

@shared_task
def expire_old_attempts():
    now = timezone.now()
    attempts = StudentAssessmentAttempt.objects.filter(
        status=StudentAssessmentAttempt.AttemptStatus.IN_PROGRESS
    )

    for attempt in attempts:
        if attempt.is_expired:
            attempt.expire_attempt()

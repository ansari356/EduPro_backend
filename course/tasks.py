from celery import shared_task
from django.utils import timezone
from .models import Coupon , CourseEnrollment , Lesson
from datetime import timedelta
from .utilis import upload_to_vdocipher, get_vdocipher_video_details

import logging
import os
from django.core.files.base import ContentFile

@shared_task
def check_expired_coupons():
    # Get all active coupons
    active_coupons = Coupon.objects.filter(is_active=True)
    
    for coupon in active_coupons:
        if coupon.expiration_date and coupon.expiration_date <= timezone.now():
            coupon.is_active = False
            coupon.save(update_fields=['is_active'])
    
    return "Expired coupons checked and updated"

@shared_task
def check_expired_enrollments():

    # Get all active enrollments
    active_enrollments = CourseEnrollment.objects.filter(is_active=True)
    for enrollment in active_enrollments:
        if enrollment.ended_date and enrollment.ended_date <= timezone.now():
            enrollment.status = CourseEnrollment.EnrollmentStatus.EXPIRED
            enrollment.is_active = False
            enrollment.save(update_fields=['is_active', 'status'])
    
    return "Expired enrollments checked and updated"



logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def upload_video_to_vdocipher_task(self, lesson_id, video_data, video_name):
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        video_file = ContentFile(bytes(video_data), name=video_name)
        
        video_id = upload_to_vdocipher(video_file, lesson.title)
        
        lesson.video_id = video_id
        lesson.save(update_fields=['video_id'])
        
    except Lesson.DoesNotExist:
        logger.error(f"Lesson with id {lesson_id} not found.")
    except Exception as e:
        logger.error(f"Error uploading video for lesson {lesson_id}: {e}")
        self.retry(exc=e)

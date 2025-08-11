from celery import shared_task
from django.utils import timezone
from .models import Coupon , CourseEnrollment , Lesson
from datetime import timedelta
from .utilis import upload_to_vdocipher, get_vdocipher_video_details

import logging
import os
import shutil
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

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
def upload_video_to_vdocipher_task(self, lesson_id, temp_video_path, video_name, temp_dir_path):
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        lesson.video_processing_status = Lesson.VideoProcessingStatus.QUEUED
        lesson.save(update_fields=['video_processing_status'])
        
        full_video_path = default_storage.path(temp_video_path)
        video_id = upload_to_vdocipher(full_video_path, video_name, lesson.title)
        
        lesson.video_id = video_id
        lesson.video_processing_status = Lesson.VideoProcessingStatus.READY
        lesson.save(update_fields=['video_id', 'video_processing_status'])
        
    except Lesson.DoesNotExist:
        logger.error(f"Lesson with id {lesson_id} not found.")
    except Exception as e:
        logger.error(f"Error uploading video for lesson {lesson_id}: {e}")
        lesson.video_processing_status = Lesson.VideoProcessingStatus.FAILED
        lesson.save(update_fields=['video_processing_status'])
        self.retry(exc=e)
    finally:
        # Clean up the entire unique temporary directory
        if temp_dir_path and default_storage.exists(temp_dir_path):
            full_temp_dir_path = default_storage.path(temp_dir_path)
            shutil.rmtree(full_temp_dir_path)

from celery import shared_task
from django.utils import timezone
from .models import Coupon , CourseEnrollment , Lesson
from datetime import timedelta
from .utilis import get_vdocipher_video_details, delete_vdocipher_video

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

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def delete_video_from_vdocipher_task(self, video_id):
    """
    Celery task to delete a video from VdoCipher with retry logic.
    """
    try:
        logger.info(f"Attempting to delete video {video_id} from VdoCipher.")
        delete_vdocipher_video(video_id)
    except Exception as e:
        logger.error(f"Failed to delete video {video_id} from VdoCipher. Retrying... Error: {e}")
        self.retry(exc=e)

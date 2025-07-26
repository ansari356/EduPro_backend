from celery import shared_task
from django.utils import timezone
from .models import Coupon , CourseEnrollment
from datetime import timedelta

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

# @shared_task
# def create_coupon_with_expiration(coupon_id):
#     try:
#         coupon = Coupon.objects.get(id=coupon_id)
#         # Set expiration date to 30 days from creation
#         coupon.expiration_date =  coupon.date + timedelta(days=30)
#         coupon.save()
#     except Coupon.DoesNotExist:
#         return "Coupon not found"
#     return "Coupon expiration date set successfully"
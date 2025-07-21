from django.db import models
from userAuth.models import  StudentProfile , TeacherProfile
import uuid
from django.utils.text import slugify
from django.utils import timezone

# Create your models here.

class CourseCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=30, unique=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=100)
    description = models.TextField()
    trailer_video = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_published= models.BooleanField(default=True)
    is_free  = models.BooleanField(default=False)
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE, related_name='courses')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_enrollments = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, null=True, blank=True)
    total_durations = models.PositiveIntegerField(default=0)

    
    def __str__(self):
        return self.title

    
    
    


class CourseEnrollment(models.Model):
    class EnrollmentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date =  models.DateTimeField(auto_now_add=True)
    ended_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=EnrollmentStatus.choices, default=EnrollmentStatus.PENDING)
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    class Meta:
        unique_together = ('student', 'course')  
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['enrollment_date']),
        ]
    
    
    def __str__(self):
        return f'{self.student.user.first_name} enrolled in {self.course.title}'



class Coupon(models.Model):
    class CouponType(models.TextChoices):
        FULL_ACCSESSED = 'full_accessed', 'Full Accessed'
        LIMITED_ACCESS = 'limited_access', 'Limited Access'
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    used_by = models.ManyToManyField(StudentProfile, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=250,unique=True)
    status = models.CharField(max_length=20, choices=CouponType.choices, default=CouponType.FULL_ACCSESSED)
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    expiration_date = models.DateTimeField(blank=True, null=True)
    discount = models.IntegerField(default=0 , null=True, blank=True)
    is_active= models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code
    
from django.db import models
from userAuth.models import  StudentProfile , TeacherProfile
import uuid
from django.utils.text import slugify
from django.utils import timezone
from django.db.models.functions import Coalesce
from PIL import Image

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
    
    

class CourseModule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='course_modules/images/', null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_lessons = models.PositiveIntegerField(default=0)
    total_duration = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def update_totals(self):
        from django.db.models import Sum, Count
        
        totals = self.lessons.aggregate(
            total_lessons=Count('id'),
            total_duration=Coalesce(Sum('duration'), 0)
        )
        
        self.total_lessons = totals['total_lessons'] or 0
        self.total_duration = totals['total_duration'] or 0
        self.save(update_fields=['total_lessons', 'total_duration'])
        
    
    @property
    def teacher(self):
        return self.course.teacher

    @property
    def lessons(self):
        return self.lessons
    
    class Meta:
        ordering = ['order']
        unique_together = ('course', 'order')
    
    
    
    
class Lesson(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=True)
    is_free = models.BooleanField(default=False)
    duration = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Content fields
    video = models.FileField(upload_to='lessons/videos/', blank=True, null=True)
    document = models.FileField(upload_to='lessons/documents/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='lessons/thumbnails/', blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.thumbnail:
            img = Image.open(self.thumbnail.path)

            max_size = (400, 300)   
            img.thumbnail(max_size)  

            img.save(self.thumbnail.path)
            
            self.module.update_totals()
        
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.module.update_totals()
        
    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        
        if self.thumbnail:
            img = Image.open(self.thumbnail.path)

            max_size = (400, 300)   
            img.thumbnail(max_size)  

            img.save(self.thumbnail.path)
            
            self.module.update_totals()
    
    class Meta:
        ordering = ['order']
        unique_together = ('module', 'order')
        
    @property
    def teacher(self):
        return self.module.course.teacher
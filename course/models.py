from django.db import models
from userAuth.models import  StudentProfile , TeacherProfile
import uuid
from django.utils.text import slugify
from django.utils import timezone

# Create your models here.

class CourseCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=30, unique=True)
    description= models.CharField(max_length=250, blank=True, null=True)
    slug = models.SlugField()
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Course(models.Model):
    class CourseStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=100)
    description = models.TextField()
    trailer_video = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=CourseStatus.choices, default=CourseStatus.PUBLISHED)
    is_free  = models.BooleanField(default=False)
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE, related_name='courses')
    slug = models.SlugField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now())
    total_enrollments = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, null=True, blank=True)
    total_durations = models.PositiveIntegerField(default=0)

    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_id = str(uuid.uuid4())[:8]
            self.slug = f"{base_slug}-{unique_id}"
        super().save(*args, **kwargs)
    
    
    


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
    enrollment_date = models.DateTimeField(default=timezone.now())
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
    class CuponType(models.TextChoices):
        FULL_ACCSESSED = 'full_accessed', 'Full Accessed'
        LIMITED_ACCESS = 'limited_access', 'Limited Access'
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    used_by = models.ManyToManyField(StudentProfile, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=250,unique=True)
    status = models.CharField(max_length=20, choices=CuponType.choices, default=CuponType.FULL_ACCSESSED)
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    expiration_date = models.DateTimeField(blank=True, null=True)
    discount = models.IntegerField(default=0 , null=True, blank=True)
    is_active= models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.code
    
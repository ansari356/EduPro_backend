from datetime import timedelta
from django.db import models
from userAuth.models import  StudentProfile , TeacherProfile,TeacherStudentProfile
import uuid
from django.utils import timezone
from .utilis import genrate_coupon_code,create_lesson_progress_for_access
from django.db.models.functions import Coalesce
from PIL import Image
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum,Count
from django.db import models, transaction
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
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE, related_name='courses',null=True,blank=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_enrollments = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, null=True, blank=True)
    total_durations = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    
    def __str__(self):
        return self.title

    def update_totals(self):
        totals=self.modules.aggregate(
            total_lessons=Sum('total_lessons'),
            total_duration=Sum('total_duration')
        )
        
        self.total_lessons = totals['total_lessons'] or 0
        self.total_durations = totals['total_duration'] or 0
        self.save(update_fields=['total_lessons', 'total_durations'])
    
    


class CourseEnrollment(models.Model):
    class EnrollmentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'
    
    class AccessType(models.TextChoices):
        FULL_ACCESS = 'full_access', 'Full Access'
        NO_ACCESS = 'no_access', 'No Access'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date =  models.DateTimeField(auto_now_add=True)
    ended_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=EnrollmentStatus.choices, default=EnrollmentStatus.PENDING)
    access_type = models.CharField(max_length=20, choices=AccessType.choices, default=AccessType.NO_ACCESS)
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

    def save(self, *args, **kwargs):
        creating = self._state.adding
        if not self.ended_date:
            self.ended_date = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
        
        if creating and self.access_type==self.AccessType.FULL_ACCESS and self.is_active:
            create_lesson_progress_for_access(student=self.student,course=self.course)

class Coupon(models.Model):
    class CouponType(models.TextChoices):
        FULL_ACCSESSED = 'full_accessed', 'Full Accessed'
        LIMITED_ACCESS = 'limited_access', 'Limited Access'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='coupons')
    # course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=15, blank=True,unique=True)
    status = models.CharField(max_length=20, choices=CouponType.choices, default=CouponType.FULL_ACCSESSED)
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    expiration_date = models.DateTimeField(blank=True, null=True)
    price = models.IntegerField(default=0 , null=True, blank=True)
    is_active= models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code
    
    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                code = genrate_coupon_code(10)
                if not Coupon.objects.filter(code=code).exists():
                    self.code = code
                    break
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
        
    class Meta:
        unique_together = ('code', 'teacher')
        indexes = [
            models.Index(fields=['code']),
        ]


class CouponUsage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='coupon_usages')
    used_at = models.DateTimeField(auto_now_add=True)
    course= models.ForeignKey(Course, on_delete=models.SET_NULL, related_name='couponCourse_usages', null=True, blank=True)
    module = models.ForeignKey('CourseModule', on_delete=models.SET_NULL, related_name='couponModule_usages', null=True, blank=True)
    class Meta:
        unique_together = ('coupon', 'student')
        
    def __str__(self):
        return f"{self.student} used {self.coupon.code}"
    

class CourseModule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
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
        
        self.course.update_totals()

    @property
    def teacher(self):
        return self.course.teacher
    
    class Meta:
        ordering = ['order']
        # unique_together = ('course', 'order')

    def save(self, *args, **kwargs) :
        is_new = self._state.adding
        with transaction.atomic():
            if is_new:
                # new creation
                # if not order value
                if self.order is None:
                    last_module_order=CourseModule.objects.filter(course=self.course).aggregate(models.Max('order'))['order__max']
                    self.order=1 if last_module_order is None else last_module_order+1
                # if user enter order value
                else:
                # if user enter order value
                    if CourseModule.objects.filter(course=self.course, order=self.order).exists():
                        CourseModule.objects.filter(course=self.course, order__gte=self.order).update(order=models.F('order') + 1)
                # in order update
            else:
                old_order=CourseModule.objects.get(pk=self.pk).order
                
                if self.order != old_order:
                    if self.order < old_order:
                        CourseModule.objects.filter(
                            course=self.course,
                            order__gte=self.order,
                            order__lt=old_order
                        ).update(order=models.F('order') + 1)

                    else:
                        CourseModule.objects.filter(
                            course=self.course,
                            order__lte=self.order,
                            order__gt=old_order
                        ).update(order=models.F('order') - 1)
        super().save(*args, **kwargs)
        
class ModuleEnrollment(models.Model):
    class EnrollmentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='module_enrollments')
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date =  models.DateTimeField(auto_now_add=True)
    ended_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=EnrollmentStatus.choices, default=EnrollmentStatus.PENDING)
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    class Meta:
        unique_together = ('student', 'module')  
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['enrollment_date']),
        ]
    
    
    def __str__(self):
        return f'{self.student.user.first_name} enrolled in {self.module.title}'

    def save(self, *args, **kwargs):
        creating=self._state.adding
        if not self.ended_date:
            self.ended_date = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
        if creating and self.status==self.EnrollmentStatus.ACTIVE and self.is_active:
            create_lesson_progress_for_access(student=self.student,module=self.module)
    
class Lesson(models.Model):
    class VideoProcessingStatus(models.TextChoices):
        PRE_UPLOAD = 'pre-upload', 'Pre-Upload'
        QUEUED = 'queued', 'Queued'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, null=True)
    is_published = models.BooleanField(default=True)
    is_free = models.BooleanField(default=False)
    duration = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    video_id = models.CharField(max_length=100, blank=True, null=True)
    video_processing_status = models.CharField(
        max_length=20,
        choices=VideoProcessingStatus.choices,
        default=VideoProcessingStatus.PRE_UPLOAD
    )

    # Content fields
    video = models.FileField(upload_to='lessons/videos/', blank=True, null=True)
    document = models.FileField(upload_to='lessons/documents/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='lessons/thumbnails/', blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        creating=self._state.adding
        with transaction.atomic():
            if creating:
                if self.order is None:
                    last_lesson_order=Lesson.objects.filter(module=self.module).aggregate(models.Max('order'))['order__max']
                    self.order=1 if last_lesson_order is None else last_lesson_order+1

                else:
                    if Lesson.objects.filter(module=self.module,order=self.order).exists():
                        Lesson.objects.filter(module=self.module,order__gte=self.order).update(order=models.F('order') + 1)
            else:
                old_order=Lesson.objects.get(pk=self.pk).order
                
                if self.order != old_order:
                    if self.order < old_order:
                        Lesson.objects.filter(
                            module=self.module,
                            order__gte=self.order,
                            order__lt=old_order
                        ).update(order=models.F('order')+1)
            
                    else:
                        Lesson.objects.filter(
                            module=self.module,
                            order__lte=self.order,
                            order__gt=old_order
                        ).update(order=models.F('order') - 1)
        
        super().save(*args, **kwargs)
        
        if self.module:
            self.module.update_totals()

        
        if self.thumbnail:
            if self.thumbnail:
                img = Image.open(self.thumbnail.path)
                max_size = (400, 300)
                img.thumbnail(max_size)
                img.save(self.thumbnail.path)
            
        if creating:
            from .models import StudentLessonProgress, CourseEnrollment, ModuleEnrollment

            course_students = CourseEnrollment.objects.filter(
                course=self.module.course,
                status=CourseEnrollment.EnrollmentStatus.ACTIVE,
                is_active=True,
                access_type=CourseEnrollment.AccessType.FULL_ACCESS,
            ).values_list("student", flat=True)

            module_students = ModuleEnrollment.objects.filter(
                module=self.module,
                status=ModuleEnrollment.EnrollmentStatus.ACTIVE,
                is_active=True,
            ).values_list("student", flat=True)

            student_ids = set(course_students) | set(module_students)

            StudentLessonProgress.objects.bulk_create(
                [StudentLessonProgress(student_id=sid, lesson=self) for sid in student_ids],
                ignore_conflicts=True
            )
            
            
    def delete(self, *args, **kwargs):
        
        if self.video:
            self.video.delete(save=False)
        if self.document:
            self.document.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        
        super().delete(*args, **kwargs)
        self.module.update_totals()
        
    
    class Meta:
        ordering = ['order']
        # unique_together = ('module', 'order')
        
    @property
    def teacher(self):
        return self.module.course.teacher

class StudentLessonProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    student=models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name='lessons_progress')
    lesson=models.ForeignKey('Lesson', on_delete=models.CASCADE,related_name='students_progress')
    is_completed=models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.user.username} - {self.lesson.title} - {self.is_completed}"
    
    class Meta:
        unique_together = ('student', 'lesson') 
        
    
class Rating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True , max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')
        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.student.user.first_name} rated {self.course.title} - {self.rating}"

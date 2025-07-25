from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils.text import slugify
# Create your models here.

class User(AbstractUser):
    class userType(models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30,)
    username = models.CharField(max_length=20)
    phone = models.CharField(max_length=15,unique=True)
    parent_phone = models.CharField(max_length=15, blank=True , null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    user_type = models.CharField(max_length=20,choices=userType.choices, default=userType.TEACHER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True,blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.user_type})'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.username}')
        super(User, self).save(*args, **kwargs)
    
    
   
        
        
        




class StudentProfile(models.Model):
    user  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,unique=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    number_of_courses = models.PositiveIntegerField(default=0)
    number_of_completed_courses = models.PositiveIntegerField(default=0)
    gender = models.CharField(max_length=10,null=True, blank=True)
    
    def __str__(self):
        return f'Student Profile of {self.user.first_name} {self.user.last_name}'
    
    
    def save(self, *args, **kwargs):
        if not self.full_name:
            if self.user.user_type == User.userType.STUDENT:
                self.full_name = f'{self.user.first_name} {self.user.last_name}'
                
        if not self.profile_picture:
            if self.user.user_type == User.userType.STUDENT:
                self.profile_picture = self.user.avatar
        super(StudentProfile, self).save(*args, **kwargs)
    
    @property
    def teachers(self):
        return self.user.teachers.all()
 
           
class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,unique=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    number_of_courses = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    experiance = models.TextField(blank=True, null=True)
    number_of_students = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0 ,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    gender = models.CharField(max_length=10,null=True, blank=True)
    students = models.ManyToManyField(User, blank=True, limit_choices_to={'user_type': 'student'}, related_name='teachers')
    def __str__(self):
        return f'Teacher Profile of {self.user.first_name} {self.user.last_name}'
    
    
        
    
    def save(self, *args, **kwargs):
        if not self.full_name:
            if self.user.user_type == User.userType.TEACHER:
                self.full_name = f'{self.user.first_name} {self.user.last_name}'
        
        if not self.profile_picture:
            if self.user.user_type == User.userType.TEACHER:
                self.profile_picture = self.user.avatar
                
        
        if self.user.user_type == User.userType.TEACHER:
            self.number_of_students = self.students.count()
            
        
        super(TeacherProfile, self).save(*args, **kwargs)
        
        
        

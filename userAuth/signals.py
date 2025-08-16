from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, StudentProfile, TeacherProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == User.userType.STUDENT:
            StudentProfile.objects.create(user=instance)
        elif instance.user_type == User.userType.TEACHER:
            TeacherProfile.objects.create(user=instance)
            
            

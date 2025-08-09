from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.db.models import F
from .models import Course , CourseEnrollment, Lesson




@receiver(post_delete, sender=Course)
def update_course_count_on_delete(sender, instance, **kwargs):
    teacher = instance.teacher
    if teacher.number_of_courses == 0:
        return
    teacher.number_of_courses = F('number_of_courses') - 1
    teacher.save(update_fields=['number_of_courses'])

@receiver(post_save, sender=Course)
def update_course_count_on_create(sender, instance, created, **kwargs):
    if created:
        teacher = instance.teacher
       
        teacher.number_of_courses = F('number_of_courses') + 1
        teacher.save(update_fields=['number_of_courses'])


@receiver(post_save, sender=CourseEnrollment)
def update_course_enrollment_count(sender, instance, **kwargs):
    course = instance.course
    course.total_enrollments = F('total_enrollments') + 1
    course.save(update_fields=['total_enrollments'])
    
    
@receiver(post_delete, sender=CourseEnrollment)
def update_course_enrollment_count(sender, instance, **kwargs):
    course = instance.course
    if course.total_enrollments == 0:
        return
    course.total_enrollments = F('total_enrollments') - 1
    course.save(update_fields=['total_enrollments'])


@receiver(post_save, sender=Lesson)
def update_number_of_lessons(sender, instance, **kwargs):
    course = instance.module.course
    course.total_lessons = F('total_lessons') + 1
    course.save(update_fields=['total_lessons'])
    
@receiver(post_delete, sender=Lesson)
def update_number_of_lessons(sender, instance, **kwargs):
    course = instance.module.course
    if course.total_lessons == 0:
        return
    course.total_lessons = F('total_lessons') - 1
    course.save(update_fields=['total_lessons'])
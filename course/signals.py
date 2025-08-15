from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.db.models import F, Avg
from .models import Course , CourseEnrollment, Lesson, Rating
from .tasks import delete_video_from_vdocipher_task
import logging

logger = logging.getLogger(__name__)



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
def update_number_of_lessons_and_delete_video(sender, instance, **kwargs):
    # Update lesson count
    course = instance.module.course
    if course.total_lessons > 0:
        course.total_lessons = F('total_lessons') - 1
        course.save(update_fields=['total_lessons'])
    
    # Delete video from VdoCipher
    if instance.video_id:
        logger.info(f"Lesson {instance.id} with video_id {instance.video_id} was deleted. "
                    f"Triggering background task to delete from VdoCipher.")
        delete_video_from_vdocipher_task.delay(instance.video_id)

@receiver(post_save, sender=Rating)
def update_course_rating_on_save(sender, instance, **kwargs):
    course = instance.course
    ratings = Rating.objects.filter(course=course)
    course.total_reviews = ratings.count()
    course.average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    course.save(update_fields=['total_reviews', 'average_rating'])

@receiver(post_delete, sender=Rating)
def update_course_rating_on_delete(sender, instance, **kwargs):
    course = instance.course
    ratings = Rating.objects.filter(course=course)
    course.total_reviews = ratings.count()
    course.average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    course.save(update_fields=['total_reviews', 'average_rating'])


@receiver(post_save, sender=Course)
def update_teacher_rating(sender, instance, **kwargs):
    teacher = instance.teacher
    courses = Course.objects.filter(teacher=teacher).exclude(average_rating=0)
    
    if courses.exists():
        teacher.rating = courses.aggregate(Avg('average_rating'))['average_rating__avg']
    else:
        teacher.rating = 0
        
    teacher.save(update_fields=['rating'])

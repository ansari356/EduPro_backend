from rest_framework import permissions
from .models import CourseEnrollment, CourseModule,Lesson,Course
from userAuth.models import User, StudentProfile, TeacherProfile
from django.shortcuts import get_object_or_404

class IsLessonAccessible(permissions.BasePermission):
    """
    Permission to check if user can access specific lesson
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        lesson_id = view.kwargs.get('id')
        if not lesson_id:
            return False
            
        try:
            lesson = Lesson.objects.select_related('module__course__teacher').get(id=lesson_id)
            course = lesson.module.course
            user = request.user

            if user.user_type == User.userType.TEACHER and hasattr(user, 'teacher_profile') and course.teacher == user.teacher_profile:
                return True
            
            if user.user_type == User.userType.STUDENT and hasattr(user, 'student_profile'):
                return CourseEnrollment.objects.filter(
                    student=user.student_profile,
                    course=course,
                    is_active=True,
                ).exists()
            
            return False
            
        except Lesson.DoesNotExist:
            return False
                
        
class IsModuleAccessible(permissions.BasePermission):
    """
    Allow access if user is the teacher of the course,
    or a student enrolled in it.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        module_id = view.kwargs.get('module_id')
        if not module_id:
            return False

        try:
            module = CourseModule.objects.select_related('course__teacher').get(id=module_id)
            course = module.course
            user = request.user

            if user.user_type == User.userType.TEACHER and hasattr(user, 'teacher_profile') and course.teacher == user.teacher_profile:
                return True

            if user.user_type == User.userType.STUDENT and hasattr(user, 'student_profile'):
                return CourseEnrollment.objects.filter(
                    student=user.student_profile,
                    course=course,
                    is_active=True,
                    status__in=['active', 'completed']
                ).exists()

            return False

        except CourseModule.DoesNotExist:
            return False
        
        
class IsModuleOwner(permissions.BasePermission):
    """
    Allows access only to the teacher who owns the course of the given module or lesson.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated or user.user_type != User.userType.TEACHER or not hasattr(user, 'teacher_profile'):
            return False

        module_id = view.kwargs.get('module_id')
        lesson_id = view.kwargs.get('id')

        try:
            if module_id:
                return CourseModule.objects.filter(id=module_id, course__teacher=user.teacher_profile).exists()
            if lesson_id:
                return Lesson.objects.filter(id=lesson_id, module__course__teacher=user.teacher_profile).exists()
        except (CourseModule.DoesNotExist, Lesson.DoesNotExist):
            return False

        return False
    
class IsCourseOwner(permissions.BasePermission):
    def has_permission(self,request, view):
        user = request.user
        if not user.is_authenticated or user.user_type != User.userType.TEACHER or not hasattr(user, 'teacher_profile'):
            return False
        
        course_id=view.kwargs.get('course_id')
        return Course.objects.filter(id=course_id, teacher=user.teacher_profile).exists()

class IsTeacher(permissions.BasePermission):

    message = "Only teachers are allowed to perform this action"

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == request.user.userType.TEACHER
        )
        
class IsStudent(permissions.BasePermission):

    message = "Only students are allowed to perform this action"

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == request.user.userType.STUDENT
        )

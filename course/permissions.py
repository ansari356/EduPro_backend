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
            lesson = Lesson.objects.get(id=lesson_id)
            module = lesson.module
            course = module.course
            
            # if teacher owns this course
            if (request.user.user_type == User.userType.TEACHER and 
                hasattr(request.user, 'teacher_profile') and
                course.teacher == request.user.teacher_profile):
                return True
            
            # if student enrolled in this course
            if (request.user.user_type == User.userType.STUDENT and 
                hasattr(request.user, 'student_profile')):
                enrollment = CourseEnrollment.objects.filter(
                    student=request.user.student_profile,
                    course=course,
                    is_active=True,
                ).exists()
                return enrollment
            
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
            module = CourseModule.objects.get(id=module_id)
            course = module.course
            user = request.user

           # is teacher of course
            if (user.user_type == User.userType.TEACHER and 
                hasattr(user, 'teacher_profile') and 
                course.teacher == user.teacher_profile):
                return True

           # is enrolled in course
            elif (user.user_type == User.userType.STUDENT and hasattr(user, 'student_profile')):
                enrollment = CourseEnrollment.objects.filter(
                    student=user.student_profile,
                    course=course,
                    is_active=True,
                    status__in=['active', 'completed']
                ).exists()
                return enrollment

            return False

        except CourseModule.DoesNotExist:
            return False
        
        
class IsModuleOwner(permissions.BasePermission):
    """
    Allows access only to the teacher who owns the course of the given module or lesson.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        
        user = request.user
        module_id = view.kwargs.get('module_id')
        lesson_id = view.kwargs.get('id')

        if user.user_type != User.userType.TEACHER or not hasattr(user, 'teacher_profile'):
            return False

        try:
            if module_id:
                module = CourseModule.objects.get(id=module_id)
                return module.course.teacher == user.teacher_profile

            elif lesson_id:
                lesson = Lesson.objects.get(id=lesson_id)
                return lesson.module.course.teacher == user.teacher_profile

        except (CourseModule.DoesNotExist, Lesson.DoesNotExist):
            return False

        return False
    
class IsCourseOwner(permissions.BasePermission):
    def has_permission(self,request, view):
        if not request.user.is_authenticated:
            return False
        
        user=request.user
        course_id=view.kwargs.get('course_id')
        course=get_object_or_404(Course,id=course_id)
        
        if user.user_type != User.userType.TEACHER or not hasattr(user, 'teacher_profile'):
            return False
        
        if course.teacher != user.teacher_profile:
            return False
        
        return True

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
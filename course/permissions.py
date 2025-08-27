from rest_framework import permissions
from .models import CourseEnrollment, CourseModule,Lesson,Course, ModuleEnrollment, Rating
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
            module = lesson.module
            user = request.user

            if user.user_type == User.userType.TEACHER and hasattr(user, 'teacher_profile') and course.teacher == user.teacher_profile:
                return True
            
            if user.user_type == User.userType.STUDENT and hasattr(user, 'student_profile'):
                
                
                if (course.is_free or course.price == 0) and course.is_published and lesson.is_published:
                    return True
                
                if (module.is_free or module.price == 0) and module.is_published and lesson.is_published:
                    return True
                
                has_full_access = CourseEnrollment.objects.filter(
                    student=user.student_profile,
                    course=course,
                    access_type=CourseEnrollment.AccessType.FULL_ACCESS,
                    is_active=True,
                ).exists()
                
                has_module_access = ModuleEnrollment.objects.filter(
                    student=user.student_profile,
                    module=lesson.module,
                    is_active=True,
                ).exists()

                return has_full_access or has_module_access
            
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
                
                if (course.is_free or course.price == 0) and course.is_published and module.is_published:
                    return True
                
                if (module.is_free or module.price == 0) and module.is_published:
                    return True
                
                has_full_access = CourseEnrollment.objects.filter(
                    student=user.student_profile,
                    course=course,
                    access_type=CourseEnrollment.AccessType.FULL_ACCESS,
                    is_active=True,
                ).exists()

                has_module_access = ModuleEnrollment.objects.filter(
                    student=user.student_profile,
                    module=module,
                    status=ModuleEnrollment.EnrollmentStatus.ACTIVE,
                    is_active=True,
                ).exists()

                return has_full_access or has_module_access

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

class CanRateCourse(permissions.BasePermission):
    """
    Permission to check if a student can rate a course.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not hasattr(request.user, 'student_profile'):
            return False

        if request.method == 'POST':
            course_id = view.kwargs.get('course_id')
            if not course_id:
                return False
            course = get_object_or_404(Course, id=course_id)
            
            # Check if the student has full access to the course or is enrolled in at least one module
            has_full_access = CourseEnrollment.objects.filter(
                student=request.user.student_profile,
                course=course,
                access_type=CourseEnrollment.AccessType.FULL_ACCESS,
                is_active=True
            ).exists()

            is_enrolled_in_module = ModuleEnrollment.objects.filter(
                student=request.user.student_profile,
                module__course=course,
                is_active=True
            ).exists()

            if not (has_full_access or is_enrolled_in_module):
                self.message = "You must have full access to the course or be enrolled in at least one module to rate it."
                return False

            # Check if the student has already rated the course
            has_rated = Rating.objects.filter(
                student=request.user.student_profile,
                course=course
            ).exists()
            if has_rated:
                self.message = "You have already rated this course."
                return False
        
        return True

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated or not hasattr(request.user, 'student_profile'):
            return False
        
        # Students can only modify their own ratings
        return obj.student == request.user.student_profile

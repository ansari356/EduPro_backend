from rest_framework.permissions import BasePermission
from course.models import CourseEnrollment, ModuleEnrollment
from assessments.models import Assessment
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied,NotFound
from assessments.models import StudentAssessmentAttempt,Question,QuestionOption


class IsStudentEnrolledAndAssessmentAvailable(BasePermission):
    message = "You don't have access to this assessment or it is not available."

    def has_permission(self, request, view):
        teacher_username = view.kwargs.get('teacher_username', None)

        student = getattr(request.user, 'student_profile', None)
        if not student:
            self.message = "User is not a student or student profile missing."
            return False

        assessment_id = view.kwargs.get('assessment_id') or request.data.get('assessment_id')
        if not assessment_id:
            self.message = "Assessment ID is required."
            return False

        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            self.message = "Assessment not found."
            return False

        if teacher_username and assessment.course and assessment.course.teacher.user.username != teacher_username:
            self.message = "Assessment does not belong to the specified teacher."
            return False

        now = timezone.now()

        if not assessment.is_published:
            self.message = "Assessment is not published yet."
            return False

        if assessment.available_from and now < assessment.available_from:
            self.message = "Assessment has not started yet."
            return False

        if assessment.available_until and now > assessment.available_until:
            self.message = "Assessment has ended."
            return False

        enrolled = False

        if assessment.course:
            enrolled = CourseEnrollment.objects.filter(
                student=student,
                course=assessment.course,
                is_active=True
            ).exists()

        elif assessment.module:
            enrolled = ModuleEnrollment.objects.filter(
                student=student,
                module=assessment.module,
                is_active=True
            ).exists()

        elif assessment.lesson:
            enrolled = ModuleEnrollment.objects.filter(
                student=student,
                module=assessment.lesson.module,
                is_active=True
            ).exists()

        if not enrolled:
            self.message = "You are not enrolled in the related course/module."
            return False

        return True



class CanSubmitAttempt(BasePermission):
    message = "You cannot submit this attempt."

    def has_permission(self, request, view):
        attempt_id = view.kwargs.get('attempt_id')
        student = getattr(request.user, 'student_profile', None)

        if not student:
            self.message = "User is not a student."
            return False

        attempt = get_object_or_404(
            StudentAssessmentAttempt,
            id=attempt_id,
            student=student
        )

        if attempt.status != StudentAssessmentAttempt.AttemptStatus.IN_PROGRESS:
            self.message = "This attempt is not in progress."
            return False

        if attempt.is_expired:
            attempt.expire_attempt()
            self.message = "Time limit exceeded. Attempt expired."
            return False
        
        assessment = attempt.assessment
        now = timezone.now()

        if assessment.available_from and now < assessment.available_from:
            self.message = "The assessment period has not started yet."
            return False

        if assessment.available_until and now > assessment.available_until:
            self.message = "The assessment period has already ended."
            return False

        if assessment.is_timed and assessment.time_limit and attempt.started_at:
            elapsed_minutes = (now - attempt.started_at).total_seconds() / 60
            if elapsed_minutes > assessment.time_limit:
                self.message = "Time limit exceeded."
                return False

        enrolled = False
        if assessment.course:
            enrolled = CourseEnrollment.objects.filter(
                student=student,
                course=assessment.course,
                is_active=True
            ).exists()

        elif assessment.module:
            enrolled = ModuleEnrollment.objects.filter(
                student=student,
                module=assessment.module,
                is_active=True
            ).exists()

        elif assessment.lesson:
            enrolled = ModuleEnrollment.objects.filter(
                student=student,
                module=assessment.lesson.module,
                is_active=True
            ).exists()

        if not enrolled:
            self.message = "You are not enrolled in the related course/module."
            return False

        return True
    
    

class IsTeacherAndAssessmentOwner(BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'teacher_profile'):
            raise PermissionDenied("You must be a teacher to access this resource.")
        return True

    def has_object_permission(self, request, view, obj):
        return obj.teacher == request.user.teacher_profile
    

class IsQuestionOwner(BasePermission):
   
    def has_permission(self, request, view):
        try:
            if 'question_id' in view.kwargs:
                question = Question.objects.select_related('assessment__teacher').get(
                    pk=view.kwargs['question_id']
                )
                return hasattr(request.user, 'teacher_profile') and question.assessment.teacher == request.user.teacher_profile
            
            if 'assessment_id' in view.kwargs:
                assessment = Assessment.objects.select_related('teacher').get(
                    pk=view.kwargs['assessment_id']
                )
                return hasattr(request.user, 'teacher_profile') and assessment.teacher == request.user.teacher_profile

        except Question.DoesNotExist:
            raise NotFound("Question not found.")
        except Assessment.DoesNotExist:
            raise NotFound("Assessment not found.")

        return False
    

class IsTeacherOfQuestionOption(BasePermission):

    def has_permission(self, request, view):
        if 'question_id' in view.kwargs:
            question = get_object_or_404(
                Question.objects.select_related('assessment__teacher'),
                pk=view.kwargs['question_id']
            )
            return (
                hasattr(request.user, 'teacher_profile') and
                question.assessment.teacher == request.user.teacher_profile
            )

        if 'option_id' in view.kwargs:
            option = get_object_or_404(
                QuestionOption.objects.select_related('question__assessment__teacher'),
                pk=view.kwargs['option_id']
            )
            return (
                hasattr(request.user, 'teacher_profile') and
                option.question.assessment.teacher == request.user.teacher_profile
            )

        return False
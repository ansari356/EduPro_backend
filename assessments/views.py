from django.shortcuts import render
from rest_framework import generics,status,permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.db import models
from userAuth.models import TeacherProfile
from django.utils import timezone
from assessments.serializers import AssessmentRetrieveSerializer

from rest_framework.permissions import IsAuthenticated
from course.permissions import IsStudent,IsTeacher
from .permissions import (IsStudentEnrolledAndAssessmentAvailable,CanSubmitAttempt,IsTeacherAndAssessmentOwner,
IsQuestionOwner,IsTeacherOfQuestionOption)
from .models import (Assessment, Question, QuestionOption, StudentAssessmentAttempt, StudentAnswer)
from .serializers import (
    AssessmentCreateSerializer, AssessmentUpdateSerializer, AssessmentListSerializer, AssessmentRetrieveSerializer,
    QuestionCreateSerializer, QuestionUpdateSerializer, QuestionListSerializer, QuestionRetrieveSerializer,
    QuestionOptionCreateSerializer, QuestionOptionUpdateSerializer, QuestionOptionListSerializer,
    StudentAssessmentAttemptCreateSerializer, StudentAssessmentAttemptSubmitSerializer,
    StudentAssessmentAttemptListSerializer, StudentAssessmentAttemptDetailSerializer,
    TeacherAnswerGradeSerializer, 
)
# Create your views here.


# teacher views

# teacher create assessment
class TeacherAssessmentListCreateView(generics.ListCreateAPIView):
    """
    GET: List all assessments for the teacher
    POST: Create new assessment
    """
    permission_classes = [IsAuthenticated, IsTeacherAndAssessmentOwner]
    def get_queryset(self):
        return Assessment.objects.filter(
            teacher=self.request.user.teacher_profile
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssessmentCreateSerializer
        return AssessmentListSerializer

class TeacherAssessmentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    
    """
    GET: Retrieve specific assessment
    PUT/PATCH: Update assessment
    DELETE: Delete assessment
    """
    
    permission_classes = [IsAuthenticated, IsTeacherAndAssessmentOwner]
    
    lookup_field = 'id'
    lookup_url_kwarg = 'assessment_id'
    
    def get_queryset(self):

        return Assessment.objects.filter(teacher=self.request.user.teacher_profile)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AssessmentUpdateSerializer
        return AssessmentRetrieveSerializer
    
class TeacherQuestionListCreateView(generics.ListCreateAPIView):
    """
    GET: List questions for specific assessment
    POST: Create new question for assessment
    """
    permission_classes = [IsAuthenticated, IsQuestionOwner]
    
    def get_queryset(self):
        assessment_id = self.kwargs.get('assessment_id')
        assessment = get_object_or_404(
            Assessment.objects.filter(teacher=self.request.user.teacher_profile),
            id=assessment_id
        )
        return Question.objects.filter(assessment=assessment).order_by('order')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuestionCreateSerializer
        return QuestionListSerializer
    
    def perform_create(self, serializer):
        assessment_id = self.kwargs.get('assessment_id')
        assessment = get_object_or_404(
            Assessment.objects.filter(teacher=self.request.user.teacher_profile),
            id=assessment_id
        )
        serializer.save(assessment=assessment)
        
class TeacherQuestionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve specific question
    PUT/PATCH: Update question
    DELETE: Delete question
    """
    permission_classes = [IsAuthenticated, IsQuestionOwner]
    
    def get_object(self):
        question = get_object_or_404(Question, pk=self.kwargs['question_id'])
        if question.assessment.teacher != self.request.user.teacher_profile:
            raise PermissionDenied("You do not have permission to access this question.")
        return question
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return QuestionUpdateSerializer
        return QuestionRetrieveSerializer


class TeacherQuestionOptionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTeacherOfQuestionOption]
    
    def get_queryset(self):
        return QuestionOption.objects.filter(
            question_id=self.kwargs['question_id']
        ).order_by('order')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuestionOptionCreateSerializer
        return QuestionOptionListSerializer
    
    def perform_create(self, serializer):
        question = get_object_or_404(
            Question,
            id=self.kwargs['question_id']
        )
        
        if question.question_type not in [Question.QuestionType.MULTIPLE_CHOICE, Question.QuestionType.TRUE_FALSE]:
            raise ValidationError("Only multiple choice and true/false questions can have options")
        
        serializer.save(question=question)

class TeacherQuestionOptionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsTeacherOfQuestionOption]
    
    def get_object(self):
        return get_object_or_404(QuestionOption, pk=self.kwargs['option_id'])
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return QuestionOptionUpdateSerializer
        return QuestionOptionListSerializer
    

# Student Views
class StudentAssessmentListView(generics.ListAPIView):
    serializer_class = AssessmentListSerializer
    
    def get_queryset(self):
        from course.models import CourseEnrollment, ModuleEnrollment
        
        teacher_username = self.kwargs.get('teacher_username')
        
        student = self.request.user.student_profile
        teacher = get_object_or_404(TeacherProfile,user__username=teacher_username)
        
        enrolled_courses = CourseEnrollment.objects.filter(
            student=student, 
            is_active=True
        ).values_list('course', flat=True)

        enrolled_modules = ModuleEnrollment.objects.filter(
            student=student,
            is_active=True
        ).values_list('module', flat=True)
        
        assessments = Assessment.objects.filter(
            (
                models.Q(course__teacher=teacher) & models.Q(course__in=enrolled_courses)
            ) |
            (
                models.Q(module__course__teacher=teacher) & models.Q(module__in=enrolled_modules)
            ) |
            (
                models.Q(lesson__module__course__teacher=teacher) & models.Q(lesson__module__in=enrolled_modules)
            )
        ).distinct().order_by('-created_at')

        return assessments

    
class StudentStartAssessmentView(generics.CreateAPIView):
    serializer_class = StudentAssessmentAttemptCreateSerializer
    permission_classes = [IsAuthenticated, IsStudentEnrolledAndAssessmentAvailable]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['assessment'] = self.kwargs['assessment_id']

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        attempt = self.perform_create(serializer)

        assessment_data = AssessmentRetrieveSerializer(attempt.assessment).data

        return Response({
            'attempt_id': attempt.id,
            'message': 'Assessment started successfully',
            'assessment': assessment_data,
            'time_limit': attempt.assessment.time_limit if attempt.assessment.is_timed else None,
            'total_questions': attempt.assessment.total_questions,
            'available_from': attempt.assessment.available_from,
            'available_until': attempt.assessment.available_until
        }, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save()
        
class StudentSubmitAssessmentView(generics.UpdateAPIView):
    
    serializer_class = StudentAssessmentAttemptSubmitSerializer
    permission_classes = [IsAuthenticated, CanSubmitAttempt]
    
    def get_object(self):
        attempt_id = self.kwargs.get('attempt_id')
        return get_object_or_404(
            StudentAssessmentAttempt,
            id=attempt_id,
            student=self.request.user.student_profile
        )
    
    def update(self, request, *args, **kwargs):
        attempt = self.get_object()
        serializer = self.get_serializer(attempt, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_attempt = serializer.save()

        return Response({
            'message': 'Assessment submitted successfully',
            'attempt_id': updated_attempt.id
        }, status=status.HTTP_200_OK)
        
# to show result of specific attemp
class StudentAssessmentAttemptDetailView(generics.RetrieveAPIView):
    serializer_class = StudentAssessmentAttemptDetailSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_object(self):
        attempt_id = self.kwargs.get('attempt_id')
        student = self.request.user.student_profile

        attempt = get_object_or_404(
            StudentAssessmentAttempt,
            id=attempt_id,
            student=student
        )

        if attempt.status == StudentAssessmentAttempt.AttemptStatus.IN_PROGRESS:
            raise PermissionDenied("Cannot view details of an in-progress attempt.")

        return attempt

    def retrieve(self, request, *args, **kwargs):
        attempt = self.get_object()

        # Check if all answers are graded
        ungraded_exists = attempt.answers.filter(
            Q(
                question__question_type__in=[
                    Question.QuestionType.SHORT_ANSWER,
                    Question.QuestionType.ESSAY,
                    Question.QuestionType.FILL_BLANK
                ],
                manual_graded=False
            ) |
            Q(
                question__question_type__in=[
                    Question.QuestionType.MULTIPLE_CHOICE,
                    Question.QuestionType.TRUE_FALSE
                ],
                auto_graded=False
            )
        ).exists()

        if ungraded_exists:
            return Response({
                "message": "Please wait until all questions are graded."
            }, status=status.HTTP_202_ACCEPTED)

        # All graded return serializer
        serializer = self.get_serializer(attempt)
        return Response(serializer.data, status=status.HTTP_200_OK)

# to show all attemps
class StudentAssessmentAttemptListView(generics.ListAPIView):
    serializer_class = StudentAssessmentAttemptListSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        student = self.request.user.student_profile
        teacher_username = self.kwargs.get('teacher_username')
        teacher = get_object_or_404(TeacherProfile, user__username=teacher_username)

        queryset = StudentAssessmentAttempt.objects.filter(
            Q(student=student) &
            (
                Q(assessment__course__teacher=teacher) |
                Q(assessment__module__course__teacher=teacher) |
                Q(assessment__lesson__module__course__teacher=teacher)
            )
        ).order_by('-started_at')

        attempts_with_ungraded = []
        for attempt in queryset:
            ungraded_exists = attempt.answers.filter(
                Q(
                    question__question_type__in=[
                        'short_answer', 'essay', 'fill_blank'
                    ],
                    manual_graded=False
                ) |
                Q(
                    question__question_type__in=[
                        'multiple_choice', 'true_false'
                    ],
                    auto_graded=False
                )
            ).exists()

            if not ungraded_exists:
                attempts_with_ungraded.append(attempt.id)

        return queryset.filter(id__in=attempts_with_ungraded)       
        

# Teacher Grading Views
class TeacherPendingGradingListView(generics.ListAPIView):
    """
    GET: List all answers that need manual grading by the teacher
    Filter by assessment type and question type
    """
    serializer_class = TeacherAnswerGradeSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def get_queryset(self):
        teacher = self.request.user.teacher_profile
        
        # Get manual grading question types
        manual_grading_types = [
            Question.QuestionType.SHORT_ANSWER,
            Question.QuestionType.ESSAY,
            Question.QuestionType.FILL_BLANK
        ]
        
        queryset = StudentAnswer.objects.filter(
            question__assessment__teacher=teacher,
            question__question_type__in=manual_grading_types,
            manual_graded=False,
            attempt__status__in=[
                StudentAssessmentAttempt.AttemptStatus.SUBMITTED,
            ]
        ).select_related(
            'attempt__student__user',
            'question__assessment',
            'question'
        ).order_by('attempt__ended_at')
        
        # Optional filters
        assessment_id = self.request.query_params.get('assessment_id')
        if assessment_id:
            queryset = queryset.filter(question__assessment_id=assessment_id)
            
        assessment_type = self.request.query_params.get('assessment_type')
        if assessment_type:
            queryset = queryset.filter(question__assessment__assessment_type=assessment_type)
            
        question_type = self.request.query_params.get('question_type')
        if question_type and question_type in manual_grading_types:
            queryset = queryset.filter(question__question_type=question_type)
            
        return queryset


class TeacherGradeAnswerView(generics.UpdateAPIView):
    """
    PUT/PATCH: Grade a specific answer
    """
    serializer_class = TeacherAnswerGradeSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def get_object(self):
        answer_id = self.kwargs.get('answer_id')
        teacher = self.request.user.teacher_profile
        
        answer = get_object_or_404(
            StudentAnswer.objects.select_related('question__assessment', 'attempt'),
            id=answer_id,
            question__assessment__teacher=teacher
        )
        
        # Check if this question type requires manual grading
        manual_grading_types = [
            Question.QuestionType.SHORT_ANSWER,
            Question.QuestionType.ESSAY,
            Question.QuestionType.FILL_BLANK
        ]
        
        if answer.question.question_type not in manual_grading_types:
            raise PermissionDenied("This question type doesn't require manual grading.")
            
        if answer.manual_graded:
            raise ValidationError("This answer has already been graded.")
            
        return answer














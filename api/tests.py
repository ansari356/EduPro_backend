from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from userAuth.models import User, TeacherProfile, StudentProfile
from course.models import Course, CourseModule, Lesson, CourseEnrollment, ModuleEnrollment
from assessments.models import (
    Assessment, Question, QuestionOption, 
    StudentAssessmentAttempt, StudentAnswer
)

# Dummy data setup
class BaseTestSetup(APITestCase):
    def setUp(self):
        # Create users
        self.teacher_user = User.objects.create_user(
            username='teacher1', 
            password='password123',
            user_type='teacher'
        )
        self.student_user = User.objects.create_user(
            username='student1', 
            password='password123',
            user_type='student'
        )
        self.other_teacher_user = User.objects.create_user(
            username='teacher2', 
            password='password123',
            user_type='teacher'
        )

        # Create profiles
        self.teacher_profile = TeacherProfile.objects.get(user=self.teacher_user)
        self.student_profile = StudentProfile.objects.get(user=self.student_user)
        self.other_teacher_profile = TeacherProfile.objects.get(user=self.other_teacher_user)

        # Create course structure
        self.course = Course.objects.create(
            title="Django Course", 
            teacher=self.teacher_profile
        )
        self.module = CourseModule.objects.create(
            title="Models", 
            course=self.course
        )
        self.lesson = Lesson.objects.create(
            title="Assessment Models", 
            module=self.module
        )

        # Enroll student
        CourseEnrollment.objects.create(
            student=self.student_profile, 
            course=self.course
        )
        ModuleEnrollment.objects.create(
            student=self.student_profile,
            module=self.module
        )

        # Create an assessment
        self.assessment = Assessment.objects.create(
            title="Lesson Quiz 1",
            assessment_type=Assessment.AssessmentType.QUIZ,
            teacher=self.teacher_profile,
            lesson=self.lesson,
            is_published=True,
            passing_score=70
        )
        
        # Create questions for the assessment
        self.question1 = Question.objects.create(
            assessment=self.assessment,
            question_text="What is the capital of France?",
            question_type=Question.QuestionType.MULTIPLE_CHOICE,
            mark=10
        )
        self.question2 = Question.objects.create(
            assessment=self.assessment,
            question_text="Django is a framework.",
            question_type=Question.QuestionType.TRUE_FALSE,
            mark=5
        )
        self.question3 = Question.objects.create(
            assessment=self.assessment,
            question_text="What is a model?",
            question_type=Question.QuestionType.ESSAY,
            mark=20
        )
        
        # Create options for the first question
        self.option1_correct = QuestionOption.objects.create(
            question=self.question1,
            option_text="Paris",
            is_correct=True
        )
        self.option1_wrong = QuestionOption.objects.create(
            question=self.question1,
            option_text="London",
            is_correct=False
        )
        
        # Create attempt for student
        self.student_attempt = StudentAssessmentAttempt.objects.create(
            student=self.student_profile,
            assessment=self.assessment
        )

# ---
## Model Tests

class TestAssessmentModel(BaseTestSetup):
    
    def test_assessment_clean_method_valid(self):
        # Test valid quiz
        quiz = Assessment(
            title="Valid Quiz", assessment_type=Assessment.AssessmentType.QUIZ, 
            teacher=self.teacher_profile, lesson=self.lesson
        )
        quiz.full_clean()
        
        # Test valid assignment
        assignment = Assessment(
            title="Valid Assignment", assessment_type=Assessment.AssessmentType.ASSIGNMENT,
            teacher=self.teacher_profile, module=self.module
        )
        assignment.full_clean()
        
        # Test valid course exam
        exam = Assessment(
            title="Valid Exam", assessment_type=Assessment.AssessmentType.COURSE_EXAM,
            teacher=self.teacher_profile, course=self.course
        )
        exam.full_clean()

    def test_assessment_clean_method_invalid(self):
        # Quiz with no lesson
        quiz_invalid = Assessment(
            title="Invalid Quiz", assessment_type=Assessment.AssessmentType.QUIZ,
            teacher=self.teacher_profile
        )
        with self.assertRaises(ValidationError):
            quiz_invalid.full_clean()
            
        # Quiz with a course
        quiz_invalid_fk = Assessment(
            title="Invalid Quiz", assessment_type=Assessment.AssessmentType.QUIZ,
            teacher=self.teacher_profile, lesson=self.lesson, course=self.course
        )
        with self.assertRaises(ValidationError):
            quiz_invalid_fk.full_clean()

    def test_is_available_method(self):
        # Test a published and available assessment
        self.assessment.is_published = True
        self.assessment.available_from = timezone.now() - timedelta(days=1)
        self.assessment.available_until = timezone.now() + timedelta(days=1)
        self.assertTrue(self.assessment.is_available())

        # Test an unpublished assessment
        self.assessment.is_published = False
        self.assertFalse(self.assessment.is_available())

        # Test an assessment before its start date
        self.assessment.is_published = True
        self.assessment.available_from = timezone.now() + timedelta(days=1)
        self.assertFalse(self.assessment.is_available())

        # Test an expired assessment
        self.assessment.is_published = True
        self.assessment.available_from = timezone.now() - timedelta(days=2)
        self.assessment.available_until = timezone.now() - timedelta(days=1)
        self.assertFalse(self.assessment.is_available())
        
    def test_update_totals(self):
        self.assessment.update_totals()
        self.assertEqual(self.assessment.total_questions, 3)
        self.assertEqual(self.assessment.total_marks, 35)

    def test_delete_question_updates_totals(self):
        self.question1.delete()
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.total_questions, 2)
        self.assertEqual(self.assessment.total_marks, 25)

class TestQuestionModel(BaseTestSetup):
    def test_save_method_auto_orders_new_question(self):
        new_question = Question.objects.create(
            assessment=self.assessment,
            question_text="New question.",
            question_type=Question.QuestionType.SHORT_ANSWER,
            mark=5,
            order=None
        )
        self.assertEqual(new_question.order, 4)

    def test_save_method_reorders_existing_questions(self):
        # Change order of question 3 to 1
        self.question3.order = 1
        self.question3.save()
        
        # Check if question 1 and 2 orders are shifted
        self.question1.refresh_from_db()
        self.question2.refresh_from_db()
        self.assertEqual(self.question3.order, 1)
        self.assertEqual(self.question1.order, 2)
        self.assertEqual(self.question2.order, 3)
        self.assertEqual(self.assessment.questions.count(), 3)
        
    def test_delete_question_reorders_questions(self):
        # Delete question 1 (order 1)
        self.question1.delete()
        
        # Check if other questions are reordered correctly
        self.question2.refresh_from_db()
        self.question3.refresh_from_db()
        
        self.assertEqual(self.question2.order, 1)
        self.assertEqual(self.question3.order, 2)
        
        self.assertEqual(self.assessment.questions.count(), 2)

class TestStudentAttemptModel(BaseTestSetup):
    def setUp(self):
        super().setUp()
        self.assessment.is_published = True
        self.assessment.available_from = timezone.now() - timedelta(hours=1)
        self.assessment.available_until = timezone.now() + timedelta(hours=1)
        self.assessment.is_timed = True
        self.assessment.time_limit = 10
        self.assessment.max_attempts = 2
        self.assessment.save()
        
    def test_clean_method_max_attempts(self):
        # Create first attempt (allowed)
        StudentAssessmentAttempt.objects.create(
            student=self.student_profile,
            assessment=self.assessment,
            attempt_number=1
        )
        
        # Try to create a third attempt
        with self.assertRaises(ValidationError) as cm:
            StudentAssessmentAttempt.objects.create(
                student=self.student_profile,
                assessment=self.assessment,
                attempt_number=3
            )
        self.assertIn("You exceeded the maximum attempts", str(cm.exception))
        
    def test_is_expired(self):
        # Not expired if attempt is not in progress
        self.student_attempt.status = StudentAssessmentAttempt.AttemptStatus.SUBMITTED
        self.assertFalse(self.student_attempt.is_expired)
        
        # Expired due to time limit
        self.student_attempt.status = StudentAssessmentAttempt.AttemptStatus.IN_PROGRESS
        self.student_attempt.started_at = timezone.now() - timedelta(minutes=15)
        self.assertTrue(self.student_attempt.is_expired)
        
        # Not expired if within time limit
        self.student_attempt.started_at = timezone.now() - timedelta(minutes=5)
        self.assertFalse(self.student_attempt.is_expired)
        
        # Expired due to assessment end date
        self.assessment.is_timed = False
        self.assessment.available_until = timezone.now() - timedelta(minutes=5)
        self.assessment.save()
        self.assertTrue(self.student_attempt.is_expired)
    
    def test_calculate_final_score(self):
        # Create correct student answer for question 1 (MCQ)
        StudentAnswer.objects.create(
            attempt=self.student_attempt,
            question=self.question1,
            selected_option=self.option1_correct,
        )
        
        # Create correct student answer for question 2 (T/F)
        StudentAnswer.objects.create(
            attempt=self.student_attempt,
            question=self.question2,
            selected_option=QuestionOption.objects.create(
                question=self.question2, 
                option_text='True', 
                is_correct=True
            ),
        )
        
        # Create answer for question 3 (Essay) which is not auto-gradable
        StudentAnswer.objects.create(
            attempt=self.student_attempt,
            question=self.question3,
            text_answer="My essay answer"
        )
        
        # Initially, score should be 0 as not all answers are graded
        self.student_attempt.calculate_final_score()
        self.student_attempt.refresh_from_db()
        self.assertEqual(self.student_attempt.score, 0)
        self.assertEqual(self.student_attempt.status, StudentAssessmentAttempt.AttemptStatus.SUBMITTED)
        
        # Manually grade the essay question
        essay_answer = self.student_attempt.answers.get(question=self.question3)
        essay_answer.marks_awarded = 15
        essay_answer.manual_graded = True
        essay_answer.save()
        
        # Recalculate score after all answers are graded
        self.student_attempt.calculate_final_score()
        self.student_attempt.refresh_from_db()
        self.assertEqual(self.student_attempt.score, 25.00)
        self.assertEqual(self.student_attempt.status, StudentAssessmentAttempt.AttemptStatus.GRADED)
        self.assertEqual(self.student_attempt.percentage, round((25/35)*100, 2))
        self.assertFalse(self.student_attempt.is_passed)

# ---
## View Tests

class TestTeacherViews(BaseTestSetup):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.teacher_user)
        self.assessment_url = reverse('teacher-assessment-list-create')
        self.assessment_detail_url = reverse(
            'teacher-assessment-retrieve-update-destroy', 
            kwargs={'assessment_id': self.assessment.id}
        )
        self.question_url = reverse(
            'teacher-question-list-create', 
            kwargs={'assessment_id': self.assessment.id}
        )
        self.question_detail_url = reverse(
            'teacher-question-retrieve-update-destroy',
            kwargs={'assessment_id': self.assessment.id, 'question_id': self.question1.id}
        )

    def test_teacher_can_create_assessment(self):
        data = {
            'title': 'New Quiz',
            'assessment_type': 'quiz',
            'lesson': self.lesson.id,
            'is_published': False
        }
        response = self.client.post(self.assessment_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Assessment.objects.count(), 2)

    def test_teacher_cannot_create_invalid_assessment(self):
        # Missing lesson for quiz
        data = {
            'title': 'Invalid Quiz',
            'assessment_type': 'quiz',
            'is_published': False
        }
        response = self.client.post(self.assessment_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_teacher_can_update_assessment(self):
        data = {'title': 'Updated Title', 'is_published': True}
        response = self.client.patch(self.assessment_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.title, 'Updated Title')
        
    def test_teacher_can_delete_assessment(self):
        response = self.client.delete(self.assessment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Assessment.objects.count(), 0)

    def test_teacher_can_create_question(self):
        data = {
            'question_text': 'What is your favorite color?',
            'question_type': 'short_answer',
            'mark': 5.0
        }
        response = self.client.post(self.question_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.assessment.questions.count(), 4)
        
    def test_teacher_can_update_question(self):
        data = {'question_text': 'Updated question text?'}
        response = self.client.patch(self.question_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question1.refresh_from_db()
        self.assertEqual(self.question1.question_text, 'Updated question text?')

    def test_teacher_cannot_access_other_teacher_assessment(self):
        self.client.force_authenticate(user=self.other_teacher_user)
        response = self.client.get(self.assessment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class TestStudentViews(BaseTestSetup):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.student_user)
        self.assessment_list_url = reverse(
            'student-assessment-list', 
            kwargs={'teacher_username': self.teacher_user.username}
        )
        self.start_attempt_url = reverse(
            'student-start-assessment', 
            kwargs={'assessment_id': self.assessment.id}
        )
        
    def test_student_can_list_assessments_for_enrolled_courses(self):
        response = self.client.get(self.assessment_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_student_cannot_list_assessments_for_non_enrolled_courses(self):
        other_course = Course.objects.create(
            title="Python Course", 
            teacher=self.other_teacher_profile
        )
        other_assessment = Assessment.objects.create(
            title="Other Exam",
            assessment_type=Assessment.AssessmentType.COURSE_EXAM,
            teacher=self.other_teacher_profile,
            course=other_course,
            is_published=True
        )
        response = self.client.get(
            reverse('student-assessment-list', kwargs={'teacher_username': self.other_teacher_user.username})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_student_can_start_assessment(self):
        # Ensure there are no existing attempts
        StudentAssessmentAttempt.objects.all().delete()
        
        response = self.client.post(self.start_attempt_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StudentAssessmentAttempt.objects.count(), 1)
        self.assertEqual(response.data['message'], 'Assessment started successfully')
        
    def test_student_cannot_start_expired_assessment(self):
        self.assessment.available_until = timezone.now() - timedelta(minutes=1)
        self.assessment.save()
        response = self.client.post(self.start_attempt_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("The assessment has already ended.", str(response.data))
        
    def test_student_can_submit_attempt(self):
        submit_url = reverse(
            'student-submit-assessment', 
            kwargs={'attempt_id': self.student_attempt.id}
        )
        data = {
            'answers': [
                {
                    'question': str(self.question1.id),
                    'selected_option': str(self.option1_correct.id)
                },
                {
                    'question': str(self.question2.id),
                    'selected_option': str(
                        QuestionOption.objects.create(
                            question=self.question2, 
                            option_text='True', 
                            is_correct=True
                        ).id
                    )
                },
                {
                    'question': str(self.question3.id),
                    'text_answer': 'My text answer'
                }
            ]
        }
        
        response = self.client.patch(submit_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_attempt.refresh_from_db()
        self.assertEqual(self.student_attempt.status, StudentAssessmentAttempt.AttemptStatus.SUBMITTED)
        self.assertEqual(self.student_attempt.answers.count(), 3)
    
    def test_student_cannot_submit_graded_attempt(self):
        submit_url = reverse(
            'student-submit-assessment', 
            kwargs={'attempt_id': self.student_attempt.id}
        )
        self.student_attempt.status = StudentAssessmentAttempt.AttemptStatus.GRADED
        self.student_attempt.save()
        response = self.client.patch(submit_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_student_can_view_graded_attempt_detail(self):
        # Prepare a graded attempt
        self.student_attempt.status = StudentAssessmentAttempt.AttemptStatus.GRADED
        self.student_attempt.save()
        
        detail_url = reverse(
            'student-attempt-detail', 
            kwargs={'attempt_id': self.student_attempt.id}
        )
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'graded')

    def test_student_cannot_view_in_progress_attempt_detail(self):
        self.student_attempt.status = StudentAssessmentAttempt.AttemptStatus.IN_PROGRESS
        self.student_attempt.save()
        detail_url = reverse(
            'student-attempt-detail', 
            kwargs={'attempt_id': self.student_attempt.id}
        )
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
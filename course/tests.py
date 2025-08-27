from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from decimal import Decimal
import uuid
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import F
from django.db import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from userAuth.models import StudentProfile, TeacherProfile, User
from .models import (
    CourseCategory,
    Course,
    CourseEnrollment,
    Coupon,
    CourseModule,
    Lesson,
    StudentLessonProgress,
    Rating,
    CouponUsage,
)

# Mock data for testing
def create_mock_user(username, email, user_type):
    return User.objects.create(
        username=username,
        email=email,
        user_type=user_type
    )

def create_mock_teacher(user):
    return TeacherProfile.objects.create(user=user, bio="Teacher bio")

def create_mock_student(user):
    return StudentProfile.objects.create(user=user, bio="Student bio")

class CourseModelTest(TestCase):
    def setUp(self):
        # Prepare mock data for tests
        self.teacher_user = create_mock_user("teacher1", "teacher1@example.com", User.userType.TEACHER)
        self.teacher_profile = create_mock_teacher(self.teacher_user)
        self.course_category = CourseCategory.objects.create(name="Science")
        self.course = Course.objects.create(
            teacher=self.teacher_profile,
            title="Introduction to Physics",
            description="A great course",
            category=self.course_category,
            price=Decimal('50.00')
        )

    def test_course_update_totals(self):
        # Test the update_totals method on the Course model
        # 1. Create modules and lessons
        module1 = CourseModule.objects.create(course=self.course, title="Module 1", total_duration=60)
        lesson1 = Lesson.objects.create(module=module1, title="Lesson 1", duration=30)
        lesson2 = Lesson.objects.create(module=module1, title="Lesson 2", duration=30)

        module2 = CourseModule.objects.create(course=self.course, title="Module 2", total_duration=40)
        lesson3 = Lesson.objects.create(module=module2, title="Lesson 3", duration=40)
        
        # Manually update module totals to reflect a realistic state
        module1.update_totals()
        module2.update_totals()

        # 2. Call the update_totals method on the course
        self.course.update_totals()

        # 3. Assert that the course totals are correct
        self.assertEqual(self.course.total_lessons, 3)
        self.assertEqual(self.course.total_durations, 100)
    
    def test_course_is_published_default(self):
        # Test if is_published is True by default
        self.assertTrue(self.course.is_published)

class CourseEnrollmentModelTest(TestCase):
    def setUp(self):
        self.student_user = create_mock_user("student1", "student1@example.com", User.userType.STUDENT)
        self.student_profile = create_mock_student(self.student_user)
        self.teacher_user = create_mock_user("teacher1", "teacher1@example.com", User.userType.TEACHER)
        self.teacher_profile = create_mock_teacher(self.teacher_user)
        self.course = Course.objects.create(
            teacher=self.teacher_profile,
            title="Django Course",
            description="Learn Django",
            is_published=True
        )
        self.module = CourseModule.objects.create(course=self.course, title="Basics", order=1)
        self.lesson1 = Lesson.objects.create(module=self.module, title="Lesson 1", duration=10, is_published=True)
        self.lesson2 = Lesson.objects.create(module=self.module, title="Lesson 2", duration=20, is_published=True)
        self.enrollment = CourseEnrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            access_type=CourseEnrollment.AccessType.FULL_ACCESS
        )

    def test_calc_progress_with_completed_lessons(self):
        # Mark one lesson as completed
        StudentLessonProgress.objects.create(student=self.student_profile, lesson=self.lesson1, is_completed=True)
        
        # Calculate progress
        self.enrollment.calc_progress()
        
        # Assert the progress
        expected_progress = (1 / 2) * 100
        self.assertEqual(self.enrollment.progress, Decimal(f'{expected_progress:.2f}'))
        self.assertFalse(self.enrollment.is_completed)

    def test_calc_progress_with_no_lessons(self):
        # Delete all lessons to simulate a course with no lessons
        self.course.modules.all().delete()
        
        # Calculate progress
        self.enrollment.calc_progress()
        
        # Assert progress is 0
        self.assertEqual(self.enrollment.progress, Decimal('0.00'))
        self.assertFalse(self.enrollment.is_completed)

    @patch('my_app_name.models.create_lesson_progress_for_access')
    def test_create_lesson_progress_on_save(self, mock_create_lesson_progress):
        # Create a new enrollment and check if the helper function is called
        new_enrollment = CourseEnrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            access_type=CourseEnrollment.AccessType.FULL_ACCESS,
            is_active=True
        )
        mock_create_lesson_progress.assert_called_with(student=self.student_profile, course=self.course)

class CouponModelTest(TestCase):
    def setUp(self):
        self.teacher_user = create_mock_user("teacher1", "teacher1@example.com", User.userType.TEACHER)
        self.teacher_profile = create_mock_teacher(self.teacher_user)
        self.course = Course.objects.create(teacher=self.teacher_profile, title="Course")

    @patch('my_app_name.models.genrate_coupon_code', side_effect=['TESTCODE123', 'TESTCODE456'])
    def test_coupon_code_generation_on_save(self, mock_genrate_coupon_code):
        # Create a coupon without providing a code
        coupon = Coupon.objects.create(teacher=self.teacher_profile)
        self.assertEqual(coupon.code, 'TESTCODE123')
        
        # Create a second coupon
        coupon2 = Coupon.objects.create(teacher=self.teacher_profile)
        self.assertEqual(coupon2.code, 'TESTCODE456')

    def test_coupon_expiration_date_on_save(self):
        # Create a coupon without an expiration date
        coupon = Coupon.objects.create(teacher=self.teacher_profile)
        expected_date = timezone.now() + timedelta(days=30)
        
        # Assert the expiration date is set correctly (with a small margin for timing)
        self.assertAlmostEqual(coupon.expiration_date, expected_date, delta=timedelta(seconds=2))

class LessonModelTest(TestCase):
    def setUp(self):
        self.teacher_user = create_mock_user("teacher1", "teacher1@example.com", User.userType.TEACHER)
        self.teacher_profile = create_mock_teacher(self.teacher_user)
        self.course = Course.objects.create(teacher=self.teacher_profile, title="Course")
        self.module = CourseModule.objects.create(course=self.course, title="Module")

    @patch('my_app_name.models.Lesson.module.update_totals')
    def test_lesson_delete_updates_totals(self, mock_update_totals):
        lesson = Lesson.objects.create(module=self.module, title="Lesson 1", duration=10)
        self.assertEqual(self.module.lessons.count(), 1)
        
        lesson.delete()
        
        # Assert that the module's update_totals method was called
        mock_update_totals.assert_called_once()
        self.assertEqual(self.module.lessons.count(), 0)

    def test_lesson_order_on_creation(self):
        # First lesson should have order 1
        lesson1 = Lesson.objects.create(module=self.module, title="Lesson 1")
        self.assertEqual(lesson1.order, 1)

        # Second lesson should have order 2
        lesson2 = Lesson.objects.create(module=self.module, title="Lesson 2")
        self.assertEqual(lesson2.order, 2)

        # Create a lesson with a specific order, it should push others down
        lesson3 = Lesson.objects.create(module=self.module, title="Lesson 3", order=1)
        
        # Reload lesson1 to check if its order was updated
        lesson1.refresh_from_db()
        self.assertEqual(lesson3.order, 1)
        self.assertEqual(lesson1.order, 2)
        self.assertEqual(lesson2.order, 3)

    def test_lesson_order_on_update(self):
        lesson1 = Lesson.objects.create(module=self.module, title="L1", order=1)
        lesson2 = Lesson.objects.create(module=self.module, title="L2", order=2)
        lesson3 = Lesson.objects.create(module=self.module, title="L3", order=3)
        
        # Change order of lesson3 from 3 to 1
        lesson3.order = 1
        lesson3.save()
        
        lesson1.refresh_from_db()
        lesson2.refresh_from_db()
        lesson3.refresh_from_db()
        
        self.assertEqual(lesson3.order, 1)
        self.assertEqual(lesson1.order, 2)
        self.assertEqual(lesson2.order, 3)


class APIViewTest(APITestCase):
    def setUp(self):
        # Create users with different roles for permission testing
        self.admin_user = create_mock_user("admin1", "admin1@example.com", User.userType.ADMIN)
        self.teacher_user = create_mock_user("teacher1", "teacher1@example.com", User.userType.TEACHER)
        self.teacher_profile = create_mock_teacher(self.teacher_user)
        self.student_user = create_mock_user("student1", "student1@example.com", User.userType.STUDENT)
        self.student_profile = create_mock_student(self.student_user)

        # Create a course for the teacher
        self.category = CourseCategory.objects.create(name="Tech")
        self.course = Course.objects.create(
            teacher=self.teacher_profile,
            title="API Testing Course",
            description="Test course",
            category=self.category
        )

    # --- CourseCategory Views Tests ---

    def test_create_course_category_by_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            reverse('course:category-create'),
            {'name': 'New Category'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CourseCategory.objects.count(), 2)
        self.assertEqual(CourseCategory.objects.get(name='New Category').name, 'New Category')

    def test_create_course_category_by_non_admin(self):
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.post(
            reverse('course:category-create'),
            {'name': 'New Category'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Course Views Tests ---

    def test_teacher_can_create_course(self):
        self.client.force_authenticate(user=self.teacher_user)
        data = {
            "teacher": str(self.teacher_profile.id),
            "title": "New Course",
            "description": "New Description",
            "category": str(self.category.id),
            "price": "99.99"
        }
        response = self.client.post(
            reverse('course:course-create'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 2)

    def test_student_cannot_create_course(self):
        self.client.force_authenticate(user=self.student_user)
        data = {
            "teacher": str(self.teacher_profile.id),
            "title": "Invalid Course",
            "description": "Invalid Description",
            "category": str(self.category.id)
        }
        response = self.client.post(
            reverse('course:course-create'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Coupon Views Tests ---

    def test_teacher_can_create_coupon(self):
        self.client.force_authenticate(user=self.teacher_user)
        data = {
            "teacher": str(self.teacher_profile.id),
            "max_uses": 5,
            "status": "full_accessed"
        }
        response = self.client.post(
            reverse('course:coupon-create'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Coupon.objects.count(), 1)

    # --- Enrollment Views Tests ---

    def test_student_can_enroll_in_course_with_coupon(self):
        self.client.force_authenticate(user=self.student_user)
        # Assuming there is a coupon with a specific code
        coupon = Coupon.objects.create(teacher=self.teacher_profile, code="TESTCODE1", max_uses=1, price=0)
        
        data = {
            "course": str(self.course.id),
            "coupon_code": "TESTCODE1"
        }
        response = self.client.post(
            reverse('course:course-enroll'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CourseEnrollment.objects.filter(student=self.student_profile, course=self.course).exists())
        self.assertTrue(CouponUsage.objects.filter(student=self.student_profile, coupon=coupon).exists())

    def test_teacher_cannot_enroll(self):
        self.client.force_authenticate(user=self.teacher_user)
        data = {
            "course": str(self.course.id)
        }
        response = self.client.post(
            reverse('course:course-enroll'),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from userAuth.models import User, StudentProfile, TeacherProfile, TeacherStudentProfile
from course.models import CourseCategory, Course, CourseModule, Lesson, CourseEnrollment, Coupon, ModuleEnrollment
from assessments.models import Assessment, Question, QuestionOption, StudentAssessmentAttempt, StudentAnswer

class Command(BaseCommand):
    help = 'Creates demo data for EduPro backend APIs.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Creating demo data...'))

        # 1. Create Teachers
        self.stdout.write(self.style.SUCCESS('Creating teachers...'))
        teacher_users = []
        for i in range(1, 3):
            user, created = User.objects.get_or_create(
                username=f'teacher{i}',
                defaults={
                    'email': f'teacher{i}@example.com',
                    'first_name': f'Teacher{i}',
                    'last_name': 'User',
                    'phone': f'111222333{i}',
                    'password': make_password('password123'),
                    'user_type': User.userType.TEACHER,
                }
            )
            if created:
                TeacherProfile.objects.get_or_create(user=user)
                self.stdout.write(self.style.SUCCESS(f'Created teacher: {user.username}'))
            teacher_users.append(user)

        # 2. Create Students
        self.stdout.write(self.style.SUCCESS('Creating students...'))
        student_users = []
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                username=f'student{i}',
                defaults={
                    'email': f'student{i}@example.com',
                    'first_name': f'Student{i}',
                    'last_name': 'User',
                    'phone': f'999888777{i}',
                    'parent_phone': f'555444333{i}',
                    'password': make_password('password123'),
                    'user_type': User.userType.STUDENT,
                }
            )
            if created:
                StudentProfile.objects.get_or_create(user=user)
                self.stdout.write(self.style.SUCCESS(f'Created student: {user.username}'))
            student_users.append(user)

        # Associate students with teachers
        self.stdout.write(self.style.SUCCESS('Associating students with teachers...'))
        for student_user in student_users:
            teacher_profile = random.choice(teacher_users).teacher_profile
            TeacherStudentProfile.objects.get_or_create(
                teacher=teacher_profile,
                student=student_user.student_profile
            )
            self.stdout.write(self.style.SUCCESS(f'Associated {student_user.username} with {teacher_profile.user.username}'))

        # 3. Create Course Categories
        self.stdout.write(self.style.SUCCESS('Creating course categories...'))
        categories = []
        category_names = ['Programming', 'Design', 'Marketing', 'Science', 'Arts']
        for name in category_names:
            category, created = CourseCategory.objects.get_or_create(
                name=name,
                defaults={'icon': None} # You might want to add actual icons
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            categories.append(category)

        # 4. Create Courses
        self.stdout.write(self.style.SUCCESS('Creating courses...'))
        courses = []
        for i in range(1, 5):
            teacher_profile = random.choice(teacher_users).teacher_profile
            category = random.choice(categories)
            course, created = Course.objects.get_or_create(
                title=f'Course {i} by {teacher_profile.user.username}',
                defaults={
                    'description': f'This is a demo course number {i}.',
                    'teacher': teacher_profile,
                    'category': category,
                    'price': random.uniform(0, 100) if i % 2 == 0 else 0, # Half free, half paid
                    'is_free': i % 2 != 0,
                    'is_published': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created course: {course.title}'))
            courses.append(course)

        # 5. Create Course Modules
        self.stdout.write(self.style.SUCCESS('Creating course modules...'))
        modules = []
        for course in courses:
            for i in range(1, 4):
                module, created = CourseModule.objects.get_or_create(
                    course=course,
                    title=f'Module {i} for {course.title}',
                    defaults={
                        'description': f'Description for module {i}.',
                        'order': i,
                        'is_published': True,
                        'is_free': course.is_free or (i % 2 == 0), # Some modules might be free even in paid courses
                        'price': course.price / 3 if not course.is_free and i % 2 != 0 else 0,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created module: {module.title}'))
                modules.append(module)

        # 6. Create Lessons
        self.stdout.write(self.style.SUCCESS('Creating lessons...'))
        lessons = []
        for module in modules:
            for i in range(1, 4):
                lesson, created = Lesson.objects.get_or_create(
                    module=module,
                    title=f'Lesson {i} in {module.title}',
                    defaults={
                        'description': f'Content for lesson {i}.',
                        'order': i,
                        'is_published': True,
                        'is_free': module.is_free or (i % 2 == 0),
                        'duration': random.randint(300, 1800), # 5 to 30 minutes
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created lesson: {lesson.title}'))
                lessons.append(lesson)

        # 7. Create Course Enrollments
        self.stdout.write(self.style.SUCCESS('Creating course enrollments...'))
        for student_user in student_users:
            student_profile = student_user.student_profile
            for _ in range(random.randint(1, 3)): # Each student enrolls in 1-3 courses
                course = random.choice(courses)
                # Ensure student is associated with the course's teacher
                if not TeacherStudentProfile.objects.filter(
                    student=student_profile,
                    teacher=course.teacher
                ).exists():
                    TeacherStudentProfile.objects.create(
                        student=student_profile,
                        teacher=course.teacher
                    )

                enrollment, created = CourseEnrollment.objects.get_or_create(
                    student=student_profile,
                    course=course,
                    defaults={
                        'status': CourseEnrollment.EnrollmentStatus.COMPLETED,
                        'is_active': True,
                        'access_type': CourseEnrollment.AccessType.FULL_ACCESS,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Enrolled {student_user.username} in {course.title}'))

        # 8. Create Module Enrollments
        self.stdout.write(self.style.SUCCESS('Creating module enrollments...'))
        for student_user in student_users:
            student_profile = student_user.student_profile
            for _ in range(random.randint(0, 2)): # Each student enrolls in 0-2 modules directly
                module = random.choice(modules)
                # Ensure student is associated with the module's course's teacher
                if not TeacherStudentProfile.objects.filter(
                    student=student_profile,
                    teacher=module.course.teacher
                ).exists():
                    TeacherStudentProfile.objects.create(
                        student=student_profile,
                        teacher=module.course.teacher
                    )

                enrollment, created = ModuleEnrollment.objects.get_or_create(
                    student=student_profile,
                    module=module,
                    defaults={
                        'status': ModuleEnrollment.EnrollmentStatus.ACTIVE,
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Enrolled {student_user.username} in module {module.title}'))

        # 9. Create Coupons
        self.stdout.write(self.style.SUCCESS('Creating coupons...'))
        for teacher_user in teacher_users:
            teacher_profile = teacher_user.teacher_profile
            for i in range(1, 3):
                coupon, created = Coupon.objects.get_or_create(
                    teacher=teacher_profile,
                    code=f'DEMO{teacher_user.username.upper()}{i}',
                    defaults={
                        'price': random.uniform(10, 50),
                        'expiration_date': timezone.now() + timezone.timedelta(days=random.randint(10, 60)),
                        'is_active': True,
                        'max_uses': random.randint(5, 20),
                        'status': random.choice([Coupon.CouponType.FULL_ACCSESSED, Coupon.CouponType.LIMITED_ACCESS]),
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created coupon: {coupon.code}'))

        # 10. Create Assessments, Questions, and Options
        self.stdout.write(self.style.SUCCESS('Creating assessments, questions, and options...'))
        assessments = []
        questions = []

        # Create a quiz for some lessons
        for lesson in random.sample(lessons, k=min(len(lessons), 3)):
            assessment, created = Assessment.objects.get_or_create(
                lesson=lesson,
                assessment_type=Assessment.AssessmentType.QUIZ,
                defaults={
                    'title': f'Quiz for {lesson.title}',
                    'teacher': lesson.module.course.teacher,
                    'is_published': True,
                    'passing_score': 70.00,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Quiz: {assessment.title}'))
            assessments.append(assessment)

        # Create an assignment for some modules
        for module in random.sample(modules, k=min(len(modules), 2)):
            assessment, created = Assessment.objects.get_or_create(
                module=module,
                assessment_type=Assessment.AssessmentType.ASSIGNMENT,
                defaults={
                    'title': f'Assignment for {module.title}',
                    'teacher': module.course.teacher,
                    'is_published': True,
                    'max_attempts': 2,
                    'passing_score': 60.00,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Assignment: {assessment.title}'))
            assessments.append(assessment)

        # Create questions for each assessment
        for assessment in assessments:
            for i in range(1, 4):
                question, created = Question.objects.get_or_create(
                    assessment=assessment,
                    order=i,
                    defaults={
                        'question_text': f'This is question {i} for {assessment.title}. What is the answer?',
                        'question_type': Question.QuestionType.MULTIPLE_CHOICE,
                        'mark': 10.00,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created Question: {question.question_text[:30]}...'))
                    # Create options for the multiple choice question
                    for j in range(1, 5):
                        QuestionOption.objects.create(
                            question=question,
                            option_text=f'Option {j}',
                            is_correct=(j == 1), # Make the first option correct
                            order=j
                        )
                questions.append(question)

        # 11. Create Student Assessment Attempts and Answers
        self.stdout.write(self.style.SUCCESS('Creating student assessment attempts...'))
        for student_user in student_users:
            student_profile = student_user.student_profile
            for assessment in random.sample(assessments, k=min(len(assessments), 2)):
                attempt, created = StudentAssessmentAttempt.objects.get_or_create(
                    student=student_profile,
                    assessment=assessment,
                    attempt_number=1,
                    defaults={
                        'status': StudentAssessmentAttempt.AttemptStatus.SUBMITTED,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created attempt for {student_user.username} on {assessment.title}'))
                    # Create answers for the attempt
                    for question in assessment.questions.all():
                        if question.question_type == Question.QuestionType.MULTIPLE_CHOICE:
                            correct_option = question.options.filter(is_correct=True).first()
                            StudentAnswer.objects.create(
                                attempt=attempt,
                                question=question,
                                selected_option=correct_option,
                            )

        self.stdout.write(self.style.SUCCESS('Demo data creation complete!'))

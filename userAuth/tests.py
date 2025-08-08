from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User


class RegisterAPIViewTestCase(APITestCase):
    def test_register_user_successfully(self):
        """
        Ensure a new user can be created successfully.
        """
        url = reverse('teacher_register')
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'phone': '1234567890',
            'user_type': 'teacher',
            'first_name': 'test',
            'last_name': 'user'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'User created successfully')

    def test_register_user_with_mismatched_passwords(self):
        """
        Ensure user registration fails with mismatched passwords.
        """
        url = reverse('teacher_register')
        data = {
            'email': 'test2@example.com',
            'username': 'testuser2',
            'password1': 'testpassword123',
            'password2': 'differentpassword',
            'phone': '1234567891',
            'user_type': 'teacher',
            'first_name': 'test',
            'last_name': 'user'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertIn('password', response.data)

    def test_register_user_with_existing_email(self):
        """
        Ensure user registration fails with an existing email.
        """
        User.objects.create_user(
            email='test@example.com',
            username='existinguser',
            password='password123',
            phone='1112223333',
            user_type='teacher',
            first_name='existing',
            last_name='user'
        )
        url = reverse('teacher_register')
        data = {
            'email': 'test@example.com',
            'username': 'newuser',
            'password1': 'newpassword123',
            'password2': 'newpassword123',
            'phone': '0987654321',
            'user_type': 'teacher',
            'first_name': 'new',
            'last_name': 'user'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertIn('email', response.data)


class RegisterStudentAPIViewTestCase(APITestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            username='teacheruser',
            password='teacherpassword',
            phone='1112223333',
            user_type='teacher',
            first_name='teacher',
            last_name='user'
        )

    def test_register_student_successfully(self):
        """
        Ensure a new student can be created and associated with a teacher successfully.
        """
        url = reverse('student_register', kwargs={'teacher_username': self.teacher_user.username})
        data = {
            'email': 'student@example.com',
            'username': 'studentuser',
            'password1': 'studentpassword123',
            'password2': 'studentpassword123',
            'phone': '9876543210',
            'parent_phone': '1231231234',
            'first_name': 'student',
            'last_name': 'user'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)  # Teacher and new student
        student_user = User.objects.get(username='studentuser')
        self.assertEqual(student_user.user_type, 'student')
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Student created successfully')

    def test_register_student_with_nonexistent_teacher(self):
        """
        Ensure student registration fails with a nonexistent teacher username.
        """
        url = reverse('student_register', kwargs={'teacher_username': 'nonexistentteacher'})
        data = {
            'email': 'student2@example.com',
            'username': 'studentuser2',
            'password1': 'studentpassword123',
            'password2': 'studentpassword123',
            'phone': '9876543211',
            'parent_phone': '1231231235',
            'first_name': 'student2',
            'last_name': 'user2'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertIn('teacher', response.data)


class AuthenticatedJoinTeacherAPIViewTestCase(APITestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            username='teacheruser',
            password='teacherpassword',
            phone='1112223333',
            user_type='teacher',
            first_name='teacher',
            last_name='user'
        )
        self.student_user = User.objects.create_user(
            email='student@example.com',
            username='studentuser',
            password='studentpassword',
            phone='9876543210',
            user_type='student',
            first_name='student',
            last_name='user'
        )

    def test_student_join_teacher_successfully(self):
        """
        Ensure an authenticated student can join a teacher successfully.
        """
        self.client.force_authenticate(user=self.student_user)
        url = reverse('authenticated-join-teacher', kwargs={'teacher_username': self.teacher_user.username})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.teacher_user.teacher_profile.student_relations.count(), 1)

    def test_student_join_teacher_already_associated(self):
        """
        Ensure a student who is already associated with a teacher gets an info message.
        """
        self.client.force_authenticate(user=self.student_user)
        # First join
        url = reverse('authenticated-join-teacher', kwargs={'teacher_username': self.teacher_user.username})
        self.client.post(url)
        # Second join attempt
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('info', response.data)

    def test_student_join_nonexistent_teacher(self):
        """
        Ensure joining a nonexistent teacher fails.
        """
        self.client.force_authenticate(user=self.student_user)
        url = reverse('authenticated-join-teacher', kwargs={'teacher_username': 'nonexistentteacher'})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_join_teacher(self):
        """
        Ensure an unauthenticated user cannot join a teacher.
        """
        url = reverse('authenticated-join-teacher', kwargs={'teacher_username': self.teacher_user.username})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_student_user_cannot_join_teacher(self):
        """
        Ensure a non-student user cannot join a teacher.
        """
        non_student_user = User.objects.create_user(
            email='nonstudent@example.com',
            username='nonstudentuser',
            password='password',
            user_type='teacher' 
        )
        self.client.force_authenticate(user=non_student_user)
        url = reverse('authenticated-join-teacher', kwargs={'teacher_username': self.teacher_user.username})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GetStudentProfileAPIViewTestCase(APITestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            username='teacheruser',
            password='teacherpassword',
            user_type='teacher',
            phone='1000000000'
        )
        self.student_user1 = User.objects.create_user(
            email='student1@example.com',
            username='studentuser1',
            password='studentpassword',
            user_type='student',
            phone='1000000001'
        )
        self.student_user2 = User.objects.create_user(
            email='student2@example.com',
            username='studentuser2',
            password='studentpassword',
            user_type='student',
            phone='1000000002'
        )
        # Create a relationship between teacher and student1
        self.teacher_user.teacher_profile.student_relations.create(student=self.student_user1.student_profile)

    def test_student_can_get_own_profile_for_teacher(self):
        """
        Ensure a student can retrieve their own profile for a specific teacher.
        """
        self.client.force_authenticate(user=self.student_user1)
        url = reverse('student-profile', kwargs={'teacher_username': self.teacher_user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student']['user']['email'], self.student_user1.email)

    def test_student_cannot_get_profile_for_unassociated_teacher(self):
        """
        Ensure a student cannot retrieve their profile for a teacher they are not associated with.
        """
        self.client.force_authenticate(user=self.student_user2)
        url = reverse('student-profile', kwargs={'teacher_username': self.teacher_user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_get_another_students_profile(self):
        """
        Ensure a student cannot retrieve another student's profile.
        """
        self.client.force_authenticate(user=self.student_user2)
        url = reverse('student-profile', kwargs={'teacher_username': self.teacher_user.username})
        # This should fail because student2 is not associated with the teacher,
        # effectively preventing them from accessing student1's profile in this context.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_get_student_profile(self):
        """
        Ensure an unauthenticated user cannot retrieve a student profile.
        """
        url = reverse('student-profile', kwargs={'teacher_username': self.teacher_user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_student_user_cannot_get_student_profile(self):
        """
        Ensure a non-student user cannot retrieve a student profile.
        """
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('student-profile', kwargs={'teacher_username': self.teacher_user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GetSudentRelatedToTeacherAPIViewTestCase(APITestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            username='teacheruser',
            password='teacherpassword',
            user_type='teacher',
            phone='1000000000'
        )
        self.student_user1 = User.objects.create_user(
            email='student1@example.com',
            username='studentuser1',
            password='studentpassword',
            user_type='student',
            phone='1000000001'
        )
        self.student_user2 = User.objects.create_user(
            email='student2@example.com',
            username='studentuser2',
            password='studentpassword',
            user_type='student',
            phone='1000000002'
        )
        self.teacher_user.teacher_profile.student_relations.create(student=self.student_user1.student_profile)
        self.teacher_user.teacher_profile.student_relations.create(student=self.student_user2.student_profile)

    def test_teacher_can_get_related_students(self):
        """
        Ensure a teacher can retrieve a list of their associated students.
        """
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('get-students')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data[0]['students']), 2)

    def test_teacher_with_no_students_gets_empty_list(self):
        """
        Ensure a teacher with no associated students gets an empty list.
        """
        teacher_with_no_students = User.objects.create_user(
            email='teacher2@example.com',
            username='teacheruser2',
            password='teacherpassword',
            user_type='teacher',
            phone='1000000003'
        )
        self.client.force_authenticate(user=teacher_with_no_students)
        url = reverse('get-students')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data[0]['students']), 0)

    def test_unauthenticated_user_cannot_get_students(self):
        """
        Ensure an unauthenticated user cannot retrieve the student list.
        """
        url = reverse('get-students')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_teacher_user_cannot_get_students(self):
        """
        Ensure a non-teacher user cannot retrieve the student list.
        """
        self.client.force_authenticate(user=self.student_user1)
        url = reverse('get-students')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GetTeacherProfileAPIViewTestCase(APITestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            username='teacheruser',
            password='teacherpassword',
            user_type='teacher',
            phone='1000000000'
        )
        self.student_user = User.objects.create_user(
            email='student@example.com',
            username='studentuser',
            password='studentpassword',
            user_type='student',
            phone='1000000001'
        )

    def test_teacher_can_get_own_profile(self):
        """
        Ensure a teacher can retrieve their own profile.
        """
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], self.teacher_user.username)

    def test_unauthenticated_user_cannot_get_teacher_profile(self):
        """
        Ensure an unauthenticated user cannot retrieve a teacher profile.
        """
        url = reverse('teacher-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_teacher_user_cannot_get_teacher_profile(self):
        """
        Ensure a non-teacher user cannot retrieve a teacher profile.
        """
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teacher-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PublicTeacherInfoTestCase(APITestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            username='teacheruser',
            password='teacherpassword',
            user_type='teacher',
            phone='1000000000'
        )

    def test_anyone_can_get_public_teacher_info(self):
        """
        Ensure anyone can retrieve a teacher's public profile.
        """
        url = reverse('teacher-profile-puplic-info', kwargs={'teacher_username': self.teacher_user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], self.teacher_user.username)

    def test_get_nonexistent_teacher_public_info(self):
        """
        Ensure requesting a non-existent teacher returns a 404 error.
        """
        url = reverse('teacher-profile-puplic-info', kwargs={'teacher_username': 'nonexistentteacher'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UpdateStudentProfileAPIViewTestCase(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            email='student@example.com',
            username='studentuser',
            password='studentpassword',
            user_type='student',
            phone='1000000001'
        )

    def test_student_can_update_own_profile(self):
        """
        Ensure a student can successfully update their own profile.
        """
        self.client.force_authenticate(user=self.student_user)
        url = reverse('update-student-profile')
        data = {'bio': 'A new bio'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_user.student_profile.refresh_from_db()
        self.assertEqual(self.student_user.student_profile.bio, 'A new bio')

    def test_unauthenticated_user_cannot_update_profile(self):
        """
        Ensure an unauthenticated user cannot update a student profile.
        """
        url = reverse('update-student-profile')
        data = {'bio': 'A new bio'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_student_user_cannot_update_profile(self):
        """
        Ensure a non-student user cannot update a student profile.
        """
        teacher_user = User.objects.create_user(
            email='teacher@example.com',
            username='teacheruser',
            password='teacherpassword',
            user_type='teacher',
            phone='1000000000'
        )
        self.client.force_authenticate(user=teacher_user)
        url = reverse('update-student-profile')
        data = {'bio': 'A new bio'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UpdateTeacherProfileAPIViewTestCase(APITestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            username='teacheruser',
            password='teacherpassword',
            user_type='teacher',
            phone='1000000000'
        )
        self.student_user = User.objects.create_user(
            email='student@example.com',
            username='studentuser',
            password='studentpassword',
            user_type='student',
            phone='1000000001'
        )

    def test_teacher_can_update_own_profile(self):
        """
        Ensure a teacher can successfully update their own profile.
        """
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('update-teacher-profile')
        data = {'bio': 'A new bio for the teacher'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.teacher_user.teacher_profile.refresh_from_db()
        self.assertEqual(self.teacher_user.teacher_profile.bio, 'A new bio for the teacher')

    def test_unauthenticated_user_cannot_update_teacher_profile(self):
        """
        Ensure an unauthenticated user cannot update a teacher profile.
        """
        url = reverse('update-teacher-profile')
        data = {'bio': 'A new bio for the teacher'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_teacher_user_cannot_update_teacher_profile(self):
        """
        Ensure a non-teacher user cannot update a teacher profile.
        """
        self.client.force_authenticate(user=self.student_user)
        url = reverse('update-teacher-profile')
        data = {'bio': 'A new bio for the teacher'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RemoveStudentAPIViewTestCase(APITestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            username='teacheruser',
            password='teacherpassword',
            user_type='teacher',
            phone='1000000000'
        )
        self.student_user = User.objects.create_user(
            email='student@example.com',
            username='studentuser',
            password='studentpassword',
            user_type='student',
            phone='1000000001'
        )
        self.teacher_user.teacher_profile.student_relations.create(student=self.student_user.student_profile)

    def test_teacher_can_remove_student(self):
        """
        Ensure a teacher can successfully remove an associated student.
        """
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-student-remove', kwargs={'student_id': self.student_user.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.teacher_user.teacher_profile.student_relations.count(), 0)

    def test_teacher_cannot_remove_unassociated_student(self):
        """
        Ensure a teacher cannot remove a student they are not associated with.
        """
        unassociated_student = User.objects.create_user(
            email='student2@example.com',
            username='studentuser2',
            password='studentpassword',
            user_type='student',
            phone='1000000002'
        )
        self.client.force_authenticate(user=self.teacher_user)
        url = reverse('teacher-student-remove', kwargs={'student_id': unassociated_student.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_remove_student(self):
        """
        Ensure an unauthenticated user cannot remove a student.
        """
        url = reverse('teacher-student-remove', kwargs={'student_id': self.student_user.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_teacher_user_cannot_remove_student(self):
        """
        Ensure a non-teacher user cannot remove a student.
        """
        self.client.force_authenticate(user=self.student_user)
        url = reverse('teacher-student-remove', kwargs={'student_id': self.student_user.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

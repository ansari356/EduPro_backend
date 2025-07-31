from django.forms import ValidationError
from django.shortcuts import render , get_object_or_404
from rest_framework import generics, status # pyright: ignore[reportMissingImports]
from rest_framework.response import Response
from rest_framework.permissions import AllowAny , IsAuthenticated
from django.core.exceptions import PermissionDenied
from .serializer import RegisterSerializer,StudentRegistrationSerializer ,StudentProfileSerializer , TeacherProfileSerializer, TeacherStudentProfileSerializer, JoinTeacherSerializer,JoinAuthenticatedStudent
from .models import User , StudentProfile , TeacherProfile, TeacherStudentProfile
from course.permissions import IsStudent , IsTeacher

# Create your views here.
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                'username': user.username,
                "user_type": user.user_type,
                'slug': user.slug,
                "avatar": user.avatar.url if user.avatar else None,
                "logo": user.logo.url if user.logo else None,
            }
        }, status=201)


class RegisterStudentAPIView(generics.CreateAPIView):
    serializer_class = StudentRegistrationSerializer
    permission_classes = [AllowAny] 

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['view'] = self
        return context
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response({
            "message": "Student created successfully",
                "user": {
                "id": student.id,
                "email": student.email,
                "phone": student.phone,
                "parent_phone":student.parent_phone,
                'username': student.username,
                "user_type": student.user_type,
                'slug': student.slug,
                "avatar": student.avatar.url if student.avatar else None,
            }
            }, status=201)




# class LoginAndJoinTeacherAPIView(generics.CreateAPIView):
#     serializer_class = JoinTeacherSerializer
#     permission_classes = [AllowAny]

#     def create(self, request, *args, **kwargs):
#         teacher_username = self.kwargs.get('teacher_username')
        
#         if not teacher_username:
#             return Response(
#                 {'error': 'Teacher username is required in the URL.'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         try:
#             teacher_user = User.objects.get(
#                 username=teacher_username,
#                 user_type=User.userType.TEACHER
#             )
#             teacher_profile = teacher_user.teacher_profile
#         except User.DoesNotExist:
#             return Response(
#                 {'error': 'Teacher not found.'},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         except TeacherProfile.DoesNotExist:
#             return Response(
#                 {'error': 'Teacher profile not found.'},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         student_user = serializer.validated_data['student_user']
        
#         student_profile,_ = StudentProfile.objects.get_or_create(user=student_user)
        
#         relation, created = TeacherStudentProfile.objects.get_or_create(
#             teacher=teacher_profile,
#             student=student_profile
#         )
        
#         if created:
#             response_data = {
#                 'success': 'Student joined successfully.',
#             }
#             status_code = status.HTTP_201_CREATED
#         else:
#             response_data = {'info': 'Student is already associated with this teacher.'}
#             status_code = status.HTTP_200_OK
        
#         return Response(response_data, status=status_code)


class AuthenticatedJoinTeacherAPIView(generics.CreateAPIView):
    serializer_class = JoinAuthenticatedStudent
    permission_classes = [IsStudent]

    def create(self, request, *args, **kwargs):
        teacher_username = self.kwargs.get('teacher_username')
        
        if not teacher_username:
            return Response(
                {'error': 'Teacher username is required in the URL.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            teacher_user = User.objects.get(
                username=teacher_username,
                user_type=User.userType.TEACHER
            )
            teacher_profile = teacher_user.teacher_profile
        except User.DoesNotExist:
            return Response(
                {'error': 'Teacher not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except TeacherProfile.DoesNotExist:
            return Response(
                {'error': 'Teacher profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        student_user = self.request.user
        
        student_profile, _ = StudentProfile.objects.get_or_create(user=student_user)
        
        relation, created = TeacherStudentProfile.objects.get_or_create(
            teacher=teacher_profile,
            student=student_profile
        )
        
        if created:
            return Response(
                {'success': 'Student joined successfully.'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'info': 'Student is already associated with this teacher.'},
                status=status.HTTP_200_OK
            )
        
    
        
        

class GetStudentProfileAPIView(generics.RetrieveAPIView):
    serializer_class = TeacherStudentProfileSerializer
    permission_classes = [IsStudent]

    def get_object(self):
        user = self.request.user
        student_profile = get_object_or_404(StudentProfile,user=user)
        teacher_username = self.kwargs.get('teacher_username')
        if not teacher_username:
            raise ValidationError({'teacher_id': 'teacher id is required'})
        teacher = get_object_or_404(User, user_type=User.userType.TEACHER,username= teacher_username)
        teacher_profile = get_object_or_404(TeacherProfile , user=teacher)
        return get_object_or_404(TeacherStudentProfile , student=student_profile , teacher=teacher_profile)



        
        

class GetTeacherProfileAPIView(generics.RetrieveAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self) -> TeacherProfile:
        user: User = self.request.user
        if user.user_type == User.userType.TEACHER:
            return get_object_or_404(TeacherProfile.objects.select_related('user'),user=user)
        else:
            raise PermissionDenied("You are not a Teacher.")
        
   
class UpdateStudentProfileAPIView(generics.UpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self) -> StudentProfile:
        user: User = self.request.user
        if user.user_type == User.userType.STUDENT:
            return get_object_or_404(StudentProfile.objects.select_related('user'), user=user)
        else:
            raise PermissionDenied("You are not a Student.")
        
        
    
    
class UpdateTeacherProfileAPIView(generics.UpdateAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> TeacherProfile:
        user: User = self.request.user
        if user.user_type == User.userType.TEACHER:
            return get_object_or_404(TeacherProfile.objects.select_related('user'), user=user)
        else:
            raise PermissionDenied("You are not a Teacher.")


class TeacherStudentRelationDestroyView(generics.DestroyAPIView):
    serializer_class = TeacherStudentProfileSerializer
    permission_classes = [IsTeacher]
    lookup_field = 'student_id'

    def get_queryset(self):
        user = self.request.user
        if user.user_type == User.userType.TEACHER:
            teacher_profile = get_object_or_404(TeacherProfile, user=user)
            return TeacherStudentProfile.objects.filter(teacher=teacher_profile)
        return TeacherStudentProfile.objects.none()

    def get_object(self):
        queryset = self.get_queryset()
        student_id = self.kwargs.get(self.lookup_field)
        student_profile = get_object_or_404(StudentProfile, id=student_id)
        obj = get_object_or_404(queryset, student=student_profile)
        self.check_object_permissions(self.request, obj)
        return obj

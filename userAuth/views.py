from django.shortcuts import render , get_object_or_404 
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny , IsAuthenticated
from django.core.exceptions import PermissionDenied
from .serializer import RegisterSerializer,StudentRegistrationSerializer ,StudentProfileSerializer , TeacherProfileSerializer
from .models import User , StudentProfile , TeacherProfile


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

class GetStudentProfileAPIView(generics.RetrieveAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self) -> StudentProfile:
        user: User = self.request.user
        if user.user_type == User.userType.STUDENT:
            return get_object_or_404(StudentProfile.objects.select_related('user'),user=user)
        else:
            raise PermissionDenied("You are not a student.")
        
        

class GetTeacherProfileAPIView(generics.RetrieveAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self) -> TeacherProfile:
        user: User = self.request.user
        if user.user_type == User.userType.TEACHER:
            return get_object_or_404(TeacherProfile.objects.select_related('user').prefetch_related('students'),user=user)
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

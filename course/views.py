from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions 
from .models import CourseCategory, Course, CourseEnrollment , Coupon
from .serializer import (CourseCategorySerializer, 
CourseCategoryCreateSerializer, CourseSerializer, CourseCreateSerializer,CouponCreateSerializer,
CouponSerializer,
CourseEnrollmentCreateSerializer,CouesEnrollmentSerializer
)
from .permissions import IsTeacher , IsStudent
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter , OrderingFilter

# Create your views here.


class CourseCategoryCreateAPIView(generics.CreateAPIView):
    serializer_class = CourseCategoryCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    


class CourseCategoryListAPIView(generics.ListAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [permissions.AllowAny]
    
    


class CourseCreateAPIView(generics.CreateAPIView):
    serializer_class = CourseCreateSerializer
    permission_classes = [IsTeacher]



class CourseListAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.user_type == user.userType.TEACHER:
            return Course.objects.filter(teacher=user.teacher_profile).select_related('teacher', 'category').order_by('-created_at')
        return Course.objects.filter(is_published=True).select_related('teacher', 'category').order_by('-created_at')

class CourseUpdateAPIView(generics.UpdateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsTeacher]
    
    def get_object(self):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id, teacher=self.request.user.teacher_profile)
        return course


class CourseDeleteAPIView(generics.DestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsTeacher]
    
    def get_object(self):
        course_id = self.kwargs.get('course_id')
        teacher=self.request.user.teacher_profile
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        teacher.number_of_courses-=1
        teacher.save(update_fields=['number_of_courses'])

        return course






class CouponCreateAPIView(generics.CreateAPIView):
    serializer_class = CouponCreateSerializer
    permission_classes = [IsTeacher]
    
    

   
class CouponListAPIView(generics.ListAPIView):
    serializer_class =  CouponSerializer
    permission_classes = [IsTeacher]
    
    def get_queryset(self):
        user = self.request.user
        try:
            return Coupon.objects.filter(teacher=user.teacher_profile).select_related('course','teacher').order_by('-date')
        except Coupon.DoesNotExist:
            return Coupon.objects.none()


class CouponUpdateAPIView(generics.UpdateAPIView):
    serializer_class = CouponSerializer
    permission_classes = [IsTeacher]
    
    def get_object(self):
        coupon_id = self.kwargs.get('coupon_id')
        if not coupon_id:
            raise ValidationError({'coupon_id': 'Coupon ID is required'})
        try:
            coupon = Coupon.objects.get(id=coupon_id, teacher=self.request.user.teacher_profile)
        except Coupon.DoesNotExist:
            raise ValidationError({'coupon': 'Coupon not found or does not belong to this teacher'})
        return coupon

class CouponDeleteAPIView(generics.DestroyAPIView):
    serializer_class = CouponSerializer
    permission_classes = [IsTeacher]
    
    def get_object(self):
        coupon_id = self.kwargs.get('coupon_id')
        if not coupon_id:
            raise ValidationError({'coupon_id': 'Coupon ID is required'})
        try:
            coupon = Coupon.objects.get(id=coupon_id, teacher=self.request.user.teacher_profile)
        except Coupon.DoesNotExist:
            raise ValidationError({'coupon': 'Coupon not found or does not belong to this teacher'})
        return coupon


class CourseEnrollmentAPIView(generics.CreateAPIView):
    serializer_class = CourseEnrollmentCreateSerializer
    permission_classes = [IsStudent]
    

      
class CourseEnrollmentListAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsStudent]
    
    def get_queryset(self):
        user = self.request.user
        try:
            return Course.objects.filter(enrollments__student=user.student_profile, enrollments__is_active=True).select_related('teacher', 'category').order_by('-created_at')
        except Course.DoesNotExist:
         return Course.objects.none()


class CourseEnrollmentDeletAPIView(generics.DestroyAPIView):
    serializer_class = CouesEnrollmentSerializer
    permission_classes = [IsStudent or IsTeacher]  

    def get_object(self):
        course_id = self.kwargs.get('course_id')
        user = self.request.user
        

        if hasattr(user, 'teacher_profile') and user.teacher_profile:
            course = get_object_or_404(Course, id=course_id, teacher=user.teacher_profile)

            enrollment_id = self.kwargs.get('enrollment_id')
            if enrollment_id:
                membership = get_object_or_404(CourseEnrollment, id=enrollment_id, course=course)
                course.total_enrollments-=1
                course.save(update_fields=['total_enrollments'])
                return membership
            else:
                raise ValidationError({'error': 'Enrollment ID is required for teachers'})
        
     
        elif hasattr(user, 'student_profile') and user.student_profile:
            course = get_object_or_404(Course, id=course_id)
            membership =  get_object_or_404(CourseEnrollment, course=course, student=user.student_profile)
            course.total_enrollments-=1
            course.save(update_fields=['total_enrollments'])
            return membership
        else:
            raise ValidationError({'error': 'User must be either a teacher or student'})
    

    

class CoursesFilterSerachAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    queryset = Course.objects.filter(is_published=True).select_related('teacher', 'category').order_by('-created_at')
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category__name', 'teacher__full_name', 'is_published']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'total_enrollments']
    
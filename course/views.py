from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .permissions import IsLessonAccessible,IsModuleAccessible,IsModuleOwner,IsCourseOwner
from userAuth.models import User
from .models import CourseCategory, Course, CourseEnrollment,Lesson,CourseModule
from .serializer import (CourseCategorySerializer,CourseCategoryCreateSerializer, CourseSerializer,
 CourseCreateSerializer,CouponCreateSerializer,CourseModuleListSerializer,LessonDetailSerializer,
LessonCreateUpdateSerializer,CourseModuleDetailSerializer,CourseModuleCreateSerializer,
CourseModuleUpdateSerializer)




# Create your views here.


class CourseCategoryCreateAPIView(generics.CreateAPIView):
    serializer_class = CourseCategoryCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "message": 'category created successfully',
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class CourseCategoryListAPIView(generics.ListAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    


class courseCreateAPIView(generics.CreateAPIView):
    serializer_class = CourseCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "message": 'course created successfully',
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
        
class CourseListAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return Course.objects.filter(is_published=True).select_related('teacher', 'category').order_by('-created_at')


class CouponCreateAPIView(generics.CreateAPIView):
    serializer_class = CouponCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()
        
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "message": 'Coupon created successfully',
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
        
        
# course module views

# course module list view
class CourseModuleListView(generics.ListAPIView):
    serializer_class = CourseModuleListSerializer
    permission_classes=[permissions.IsAuthenticated]
    
    
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course=get_object_or_404(Course,id=course_id)
    
        return course.modules.filter(is_published=True).all().order_by('order')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request
        })
        return context
    
# course module details view   
class CourseModuleDetailView(generics.RetrieveAPIView):
    serializer_class=CourseModuleDetailSerializer
    permission_classes=[permissions.IsAuthenticated]
    
    def get_object(self):
        module_id=self.kwargs.get('module_id')
        module=get_object_or_404(CourseModule,id=module_id)
        
        return module
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request
        })
        return context
    
# course module create view
class CourseModuleCreateView(generics.CreateAPIView):
    serializer_class=CourseModuleCreateSerializer
    permission_classes=[IsCourseOwner]
    
    def perform_create(self,serializer):
        course_id=self.kwargs.get('course_id')
        course=get_object_or_404(Course,id=course_id)
        
        serializer.save(course=course)
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        course_id = self.kwargs.get('course_id')
        context['course'] = get_object_or_404(Course, id=course_id)
        return context

# course module update view
class CourseModuleUpdateView(generics.UpdateAPIView):
    serializer_class=CourseModuleUpdateSerializer
    permission_classes=[IsModuleOwner]
    
    def get_object(self):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(CourseModule, id=module_id)
        return module
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        module_id = self.kwargs.get('module_id')
        context['module'] = get_object_or_404(CourseModule, id=module_id)
        return context
    
# course module delete view
class CourseModuleDeleteView(generics.DestroyAPIView):
    permission_classes=[IsModuleOwner]
    
    def get_object(self):
        module_id=self.kwargs.get('module_id')
        module=get_object_or_404(CourseModule,id=module_id)
        return module
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"detail": "Module deleted successfully."}, status=status.HTTP_200_OK)




# lessons views

# lesson lis view
class LessonListView(generics.ListAPIView):
    """
   view lessons for specific module
    """
    serializer_class = LessonDetailSerializer
    permission_classes = [IsModuleAccessible]
    
    def get_queryset(self):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(CourseModule, id=module_id)       
        user = self.request.user

        
       # if teacher he will see all module lessons
        if (user.user_type == User.userType.TEACHER and 
            hasattr(user, 'teacher_profile')):
            return module.lessons.all().order_by('order')
        
        # if he is student , he will see all published lessons only
        else:
            return module.lessons.filter(is_published=True).order_by('order')
        
# lesson details view      
class LessonDetailView(generics.RetrieveAPIView):
    """
    shows lesson details
    """
    serializer_class = LessonDetailSerializer
    permission_classes = [IsLessonAccessible]
    lookup_field = 'id'
    
    def get_object(self):
        # module_id = self.kwargs.get('module_id')
        lesson_id = self.kwargs.get('id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        module_id = lesson.module.id
        module = get_object_or_404(CourseModule, id=module_id)
        course = module.course
        user = self.request.user
        
        # if teacher of course return the lesson
        if (user.user_type == User.userType.TEACHER and 
            hasattr(user, 'teacher_profile') and
            course.teacher == user.teacher_profile):
            return lesson
        
        # if student is enrolled
        elif (user.user_type == User.userType.STUDENT and 
              hasattr(user, 'student_profile')):
            enrollment = CourseEnrollment.objects.filter(
                student=user.student_profile,
                course=course,
                is_active=True,
                status__in=['active', 'completed']
            ).first()
            
            if enrollment and lesson.is_published:
                return lesson
        
        raise PermissionDenied("You don't have permission to access this lesson.")
    
# lesson create view 
class LessonCreateView(generics.CreateAPIView):
    """
     create new lesson only for teacher
    """
    serializer_class = LessonCreateUpdateSerializer
    permission_classes = [IsModuleOwner]
    
    def perform_create(self, serializer):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(CourseModule, id=module_id)
        
        serializer.save(module=module)

# lesson update view    
class LessonUpdateView(generics.UpdateAPIView):
    """
    update lesson only for teacher
    """
    serializer_class = LessonCreateUpdateSerializer
    permission_classes = [IsModuleOwner]
    lookup_field = 'id'
    
    def get_object(self):
        lesson_id = self.kwargs.get('id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        return lesson

# lesson delete view 
    
class LessonDeleteView(generics.DestroyAPIView):
    """
    delete lesson only for teacher 
    """
    permission_classes = [IsModuleOwner]
    lookup_field = 'id'
    
    def get_object(self):
        lesson_id = self.kwargs.get('id')
        lesson = get_object_or_404(Lesson, id=lesson_id)

        
        return lesson
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"detail": "Lesson deleted successfully."}, status=status.HTTP_200_OK)


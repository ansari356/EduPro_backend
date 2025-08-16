from django.shortcuts import get_object_or_404
from numpy import generic
from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .permissions import IsLessonAccessible,IsModuleAccessible,IsModuleOwner,IsCourseOwner,IsTeacher , IsStudent, CanRateCourse
from userAuth.models import User, StudentProfile
from .models import CourseCategory, Course, CourseEnrollment,Lesson,CourseModule , Coupon, ModuleEnrollment, Rating,CouponUsage,StudentLessonProgress
from .serializer import (CourseCategorySerializer,CourseCategoryCreateSerializer, CourseSerializer,
 CourseCreateSerializer,CouponCreateSerializer,CourseModuleListSerializer,LessonDetailSerializer,
LessonCreateUpdateSerializer,CourseModuleDetailSerializer,CourseModuleCreateSerializer,
CourseModuleUpdateSerializer,
CouponSerializer,
CourseEnrollmentCreateSerializer,CouesEnrollmentSerializer, ModuleEnrollmentSerializer, ModuleEnrollmentCreateSerializer ,
 CourseRatingCreateSerializer,RatingListSerializer,EarningSerializer,CouponUsageSerialzier,
 CourseSerializerForTeacher,StudentLessonProgressSerilaizer
)
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter , OrderingFilter
from rest_framework.pagination import PageNumberPagination
from .utilis import get_vdocipher_video_details
from django.db import models
from userAuth.serializer import StudentProfileSerializer , userSerializer

# Create your views here.

class CourseCategoryCreateAPIView(generics.CreateAPIView):
    serializer_class = CourseCategoryCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    


class CourseCategoryListAPIView(generics.ListAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [permissions.AllowAny]
    

# class CourseCategoryUpdateAPIView(generics.UpdateAPIView):
#     serializer_class = CourseCategorySerializer
#     permission_classes = [permissions.IsAdminUser]
#     lookup_url_kwarg = 'category_id'
   
#     def get_object(self):
#         category_id = self.kwargs.get('category_id')
#         category = get_object_or_404(CourseCategory, id=category_id)
#         return category


class CourseCategoryUpdateAPIView(generics.UpdateAPIView):
    serializer_class = CourseCategorySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = CourseCategory.objects.all()
    lookup_field = 'id'
    lookup_url_kwarg = 'category_id'

       

class CourseCreateAPIView(generics.CreateAPIView):
    serializer_class = CourseCreateSerializer
    permission_classes = [IsTeacher]
    queryset = Course.objects.all()



class CourseListAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PageNumberPagination
    PageNumberPagination.page_size = 5
    

    def get_queryset(self):
        return Course.objects.filter(is_published=True).select_related('teacher', 'category').order_by('-created_at')

class courselistteacher(generics.RetrieveAPIView):
    serializer_class = CourseSerializerForTeacher
    permission_classes = [IsTeacher]

    def get_object(self):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        if course.teacher != self.request.user.teacher_profile:
            raise PermissionDenied("You do not have permission to view this course.")
        
        return course
        


class CourseListForTeacherAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]


    def get_queryset(self):
        teacher_username = self.kwargs.get('teacher_username')
        user = get_object_or_404(User, username=teacher_username)
        return Course.objects.filter(teacher=user.teacher_profile, is_published=True).select_related('category').order_by('-created_at')


class CourseSpacificToTeacherApiView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsTeacher]
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'teacher_profile'):
            return Course.objects.filter(teacher=user.teacher_profile).select_related('category').order_by('-created_at')
        return Course.objects.none()


class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_object(self):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course.objects.select_related('teacher', 'category'), id=course_id)
        return course

class CourseUpdateAPIView(generics.UpdateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsTeacher]
    
    def get_object(self):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course.objects.select_related('teacher', 'category'), id=course_id, teacher=self.request.user.teacher_profile)
        return course


class CourseDeleteAPIView(generics.DestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsTeacher]
    lookup_field = 'id'
    lookup_url_kwarg = 'course_id'

    def get_queryset(self):
        return Course.objects.filter(teacher=self.request.user.teacher_profile)


class RatingListAPIView(generics.ListAPIView):
    serializer_class = RatingListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        qs = Rating.objects.select_related('student' , 'course')
        return qs.filter(course=course)

class RatingCreateAPIView(generics.CreateAPIView):
    serializer_class = CourseRatingCreateSerializer
    permission_classes = [permissions.IsAuthenticated, CanRateCourse]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['course_id'] = self.kwargs.get('course_id')
        return context

class RatingRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rating.objects.select_related('student', 'course').all()
    permission_classes = [permissions.IsAuthenticated, CanRateCourse]
    serializer_class = CourseRatingCreateSerializer
    lookup_field = 'id'



class CouponCreateAPIView(generics.CreateAPIView):
    serializer_class = CouponCreateSerializer
    permission_classes = [IsTeacher]
   
    
    
    

   
class CouponListAPIView(generics.ListAPIView):
    serializer_class =  CouponSerializer
    permission_classes = [IsTeacher]
    pagination_class = PageNumberPagination
    PageNumberPagination.page_size = 10
    
    def get_queryset(self):
        user = self.request.user
        try:
            return Coupon.objects.filter(teacher=user.teacher_profile).select_related('teacher').order_by('-date')
        except Coupon.DoesNotExist:
            return Coupon.objects.none()



class UsedCopunListAPIView(generics.ListAPIView):
    serializer_class =  CouponUsageSerialzier
    permission_classes = [IsTeacher]
    pagination_class = PageNumberPagination
    PageNumberPagination.page_size = 10
    
    def get_queryset(self):
        user = self.request.user
        try:
            return CouponUsage.objects.filter(coupon__teacher=user.teacher_profile).select_related('coupon').order_by('-used_at')
        except Coupon.DoesNotExist:
            return Coupon.objects.none()

class RevinewAPIView(generics.RetrieveAPIView):
    serializer_class = EarningSerializer
    permission_classes = [IsTeacher]
    
    def get(self, request, *args, **kwargs):
        user = self.request.user
        if not hasattr(user, 'teacher_profile'):
            return Response({"error": "You are not a teacher."}, status=status.HTTP_403_FORBIDDEN)

        total_revenue = CouponUsage.objects.filter(coupon__teacher=user.teacher_profile,).aggregate(total_revenue=models.Sum('coupon__price'))['total_revenue'] or 0.00
        return Response({"revenue": total_revenue}, status=status.HTTP_200_OK)



class TeacherCouponQuerysetMixin:
    """
    A mixin to filter coupons based on the logged-in teacher.
    """
    serializer_class = CouponSerializer
    permission_classes = [IsTeacher]
    lookup_field = 'id'
    lookup_url_kwarg = 'coupon_id'

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'teacher_profile'):
            return Coupon.objects.filter(teacher=user.teacher_profile)
        return Coupon.objects.none()

class CouponDetailAPiView(TeacherCouponQuerysetMixin, generics.RetrieveAPIView):
    """
    Retrieve a specific coupon belonging to the authenticated teacher.
    """
    pass

class CouponUpdateAPIView(TeacherCouponQuerysetMixin, generics.UpdateAPIView):
    """
    Update a specific coupon belonging to the authenticated teacher.
    """
    pass

class CouponDeleteAPIView(TeacherCouponQuerysetMixin, generics.DestroyAPIView):
    """
    Delete a specific coupon belonging to the authenticated teacher.
    """
    pass


class CourseEnrollmentAPIView(generics.CreateAPIView):
    """ post api for course enrollment return status_code 201 Created """
    serializer_class = CourseEnrollmentCreateSerializer
    permission_classes = [IsStudent]

    

      
class CourseEnrollmentListAPIView(generics.ListAPIView):
    
    """this  api retreving all course that student enrolled in  takes in url  teacher username"""
    
    serializer_class = CourseSerializer
    permission_classes = [IsStudent]
    pagination_class = PageNumberPagination
    PageNumberPagination.page_size = 5
    
    def get_queryset(self):
        user = self.request.user
        teacher_username = self.kwargs.get('teacher_username', None)
        try:
            queryset = Course.objects.filter(enrollments__student=user.student_profile, enrollments__is_active=True)
            if teacher_username:
                queryset = queryset.filter(teacher__user__username=teacher_username)
            return queryset.select_related('teacher', 'category').order_by('-created_at')
        except Course.DoesNotExist:
         return Course.objects.none()



    

class CourseEnrollmentDeletAPIView(generics.DestroyAPIView):
    """api for deleteing course enrollment return status_code 204 no content if student who will delete enrollment 
     it must give me course id if teacher who will delete it must give me course id and enrollment id in url
    
    """
    serializer_class = CouesEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
   

    def get_object(self):
        course_id = self.kwargs.get('course_id')
        user = self.request.user
        course = get_object_or_404(Course, id=course_id)

        if user.user_type == User.userType.TEACHER and hasattr(user, 'teacher_profile') and course.teacher == user.teacher_profile:
            enrollment_id = self.kwargs.get('enrollment_id')
            if not enrollment_id:
                raise ValidationError({'error': 'Enrollment ID is required for teachers'})
            enrollment = get_object_or_404(CourseEnrollment, id=enrollment_id, course=course)
        elif user.user_type == User.userType.STUDENT and hasattr(user, 'student_profile'):
            enrollment = get_object_or_404(CourseEnrollment, course=course, student=user.student_profile)
        else:
            raise PermissionDenied("You do not have permission to perform this action.")

        return enrollment
    

    

class CoursesFilterSerachAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    queryset = Course.objects.filter(is_published=True).select_related('teacher', 'category').order_by('-created_at')
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category__name', 'teacher__full_name', 'is_published']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'total_enrollments']
    
    
class GetStudentEnrolledToCourseAPIView(generics.ListAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsTeacher]
    
    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        # Return StudentProfile objects directly
        return StudentProfile.objects.filter(
            enrollments__course__teacher=self.request.user.teacher_profile,
            enrollments__course=course
        ).select_related('user')
    
 
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
    queryset = Lesson.objects.all()
    
    def perform_create(self, serializer):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(CourseModule, id=module_id)
        
        lesson = serializer.save(module=module)
        return lesson
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'lesson_id': lesson.id, 'message': 'Lesson created, video upload in progress.'}, status=status.HTTP_201_CREATED, headers=headers)



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

class ModuleEnrollmentAPIView(generics.CreateAPIView):
    """ post api for module enrollment return status_code 201 Created """
    serializer_class = ModuleEnrollmentCreateSerializer
    permission_classes = [IsStudent]

class CheckVideoStatusAPIView(generics.GenericAPIView):
    permission_classes = [IsTeacher]

    def get(self, request, *args, **kwargs):
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)

        if lesson.video_processing_status == Lesson.VideoProcessingStatus.FAILED:
            return Response({"message": "Video processing failed. Please try uploading again."}, status=status.HTTP_400_BAD_REQUEST)

        if lesson.video_processing_status == Lesson.VideoProcessingStatus.READY:
            return Response({"message": "video is ready"}, status=status.HTTP_200_OK)

        if not lesson.video_id:
            return Response({"message": "video is uploading"}, status=status.HTTP_200_OK)

        video_details = get_vdocipher_video_details(lesson.video_id)

        if not video_details:
            return Response({"message": "Could not retrieve video status."}, status=status.HTTP_400_BAD_REQUEST)

        video_status = video_details.get('status')

        if video_status == 'ready':
            lesson.duration = video_details.get('length', 0)
            lesson.video_processing_status = Lesson.VideoProcessingStatus.READY
            lesson.save(update_fields=['duration', 'video_processing_status'])
            return Response({"message": "video is ready"}, status=status.HTTP_200_OK)
        
        elif video_status == 'Queued':
            lesson.video_processing_status = Lesson.VideoProcessingStatus.QUEUED
            lesson.save(update_fields=['video_processing_status'])
            return Response({"message": "the video is processed"}, status=status.HTTP_200_OK)

        elif video_status == 'pre-upload':
            return Response({"message": "video is uploading"}, status=status.HTTP_200_OK)

        return Response({"message": f"Video status: {video_status}"}, status=status.HTTP_200_OK)

# student lesson progress
class UpdateLessonProgressView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentLessonProgressSerilaizer
    permission_classes = [permissions.IsAuthenticated, IsLessonAccessible]

    def get_object(self):
        lesson_id = self.kwargs.get('id')
        return get_object_or_404(
            StudentLessonProgress,
            student=self.request.user.student_profile,
            lesson_id=lesson_id
        )
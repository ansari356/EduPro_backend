from django.urls import path
from userAuth import views as user_views
from .views import LoginView, LogoutView,CookieTokenRefreshView
from course import views as course_views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [


    # students endpoints
    path('student/student-register/<teacherusername>',user_views.RegisterStudentAPIView.as_view(), name='student_register'),
    path('student/student-profile/',user_views.GetStudentProfileAPIView.as_view(),name='student-profile'),
    path('student/update-profile/', user_views.UpdateStudentProfileAPIView.as_view(), name='update-student-profile'),
    
    # teacher endpoints
    path('teacher/teacher-register/',user_views.RegisterAPIView.as_view(), name='teacher_register'),
    path('teacher/teacher-profile/',user_views.GetTeacherProfileAPIView.as_view(),name='teacher-profile'),
    path('teacher/update-profile/', user_views.UpdateTeacherProfileAPIView.as_view(), name='update-teacher-profile'),
    
    # login paths
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='cookie_token_refresh'),
    
    # courses endpoint
    path('course/category/create/', course_views.CourseCategoryCreateAPIView.as_view(), name='course-category-create'),
    path('course/category/list/', course_views.CourseCategoryListAPIView.as_view(), name='course-category-list'),
    path('course/create/', course_views.courseCreateAPIView.as_view(), name='course-create'),
    path('course/list',course_views.CourseListAPIView.as_view(),name='course-list'),
    
    # course module
    
    # Course Modules ( under course require(course_id))
    path('courses/<uuid:course_id>/modules/', course_views.CourseModuleListView.as_view(), name='course-modules-list'),            # GET: list modules
    path('courses/<uuid:course_id>/modules/create/', course_views.CourseModuleCreateView.as_view(), name='course-module-create'),  # POST: create module
    
    # Single Module (detail / update / delete) - based on module_id only
    path('modules/<uuid:module_id>/', course_views.CourseModuleDetailView.as_view(), name='course-module-detail'),                 # GET: retrieve
    path('modules/<uuid:module_id>/update/', course_views.CourseModuleUpdateView.as_view(), name='course-module-update'),          # PUT/PATCH: update
    path('modules/<uuid:module_id>/delete/', course_views.CourseModuleDeleteView.as_view(), name='course-module-delete'),          # DELETE: delete
    
    # cousre lesson
    
    # Course Module Lessons ( under module require(module_id))
    path('modules/<uuid:module_id>/lessons/', course_views.LessonListView.as_view(), name='lesson-list'),             # GET: list lessons in a module
    path('modules/<uuid:module_id>/lessons/create/', course_views.LessonCreateView.as_view(), name='lesson-create'), # POST: create lesson in module
    
    # Single Lesson actions (using lesson id)
    path('lessons/<uuid:id>/', course_views.LessonDetailView.as_view(), name='lesson-detail'),             # GET: retrieve lesson
    path('lessons/<uuid:id>/update/', course_views.LessonUpdateView.as_view(), name='lesson-update'),      # PUT/PATCH: update lesson
    path('lessons/<uuid:id>/delete/', course_views.LessonDeleteView.as_view(), name='lesson-delete'),      # DELETE: delete lesson
    
    
    # CuponEndpoints
    path('coupon/create/', course_views.CouponCreateAPIView.as_view(), name='coupon-create'),    
]
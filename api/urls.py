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
    path('course/create/', course_views.CourseCreateAPIView.as_view(), name='course-create'),
    path('course/list/',course_views.CourseListAPIView.as_view(),name='course-list'),
    path('course/update/<course_id>',course_views.CourseUpdateAPIView.as_view(),name='course-update'),
    path('course/course-delete/<course_id>',course_views.CourseDeleteAPIView.as_view(),name='course-delete'),
    path('course/course-enrollment/',course_views.CourseEnrollmentAPIView.as_view(),name='course-enrollmnebt'),
    path('course/course-enrollment-list/',course_views.CourseEnrollmentListAPIView.as_view(),name='course-enrollmnebt-list'),
    path('course/course-enrollment-delete/<course_id>/<enrollment_id>',course_views.CourseEnrollmentDeletAPIView.as_view(),name='course-enrollmnebt-delete'),
    path('course/course-search-filter/',course_views.CoursesFilterSerachAPIView.as_view(),name='course-search-filter'),
    # CuponEndpoints
    path('coupon/create/', course_views.CouponCreateAPIView.as_view(), name='coupon-create'),
    path('coupon/list/', course_views.CouponListAPIView.as_view(), name='coupon-list'), 
    path('coupon/update/<coupon_id>', course_views.CouponUpdateAPIView.as_view(), name='coupon-update'),
    path('coupon/delete/<coupon_id>', course_views.CouponDeleteAPIView.as_view(), name='coupon-delete'),     
        
]
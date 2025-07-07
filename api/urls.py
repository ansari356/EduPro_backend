from django.urls import path
from userAuth import views as user_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [


    
    path('student/student-register/',user_views.RegisterStudentAPIView.as_view(), name='student_register'),
    path('student/student-profile/',user_views.GetStudentProfileAPIView.as_view(),name='student-profile'),
    path('student/update-profile/', user_views.UpdateStudentProfileAPIView.as_view(), name='update-student-profile'),
    
    path('teacher/teacher-register/',user_views.RegisterAPIView.as_view(), name='teacher_register'),
    path('teacher/teacher-profile/',user_views.GetTeacherProfileAPIView.as_view(),name='teacher-profile'),
    path('teacher/update-profile/', user_views.UpdateTeacherProfileAPIView.as_view(), name='update-teacher-profile'),
    
    
]
from django.urls import path
from userAuth import views as user_views
from userAuth.views import LoginView, LogoutView, LoginStudentAPIView , CookieTokenRefreshView,StudentRefreshView
from course import views as course_views
from assessments import views as assessments_views


urlpatterns = [
    # Rating endpoints
    path('courses/<uuid:course_id>/list-ratings/', course_views.RatingListAPIView.as_view(), name='course-ratings-list'),
    path('courses/<uuid:course_id>/ratings/create/', course_views.RatingCreateAPIView.as_view(), name='course-ratings-create'),
    path('course/retrive-upadate-delete-ratings/<uuid:id>/', course_views.RatingRetrieveUpdateDestroyAPIView.as_view(), name='rating-detail'),

    # students endpoints
    path('student/student-register/<teacher_username>',user_views.RegisterStudentAPIView.as_view(), name='student_register'),
    path('student/student-profile/<teacher_username>',user_views.GetStudentProfileAPIView.as_view(),name='student-profile'),
    path('student/update-profile/', user_views.UpdateStudentProfileAPIView.as_view(), name='update-student-profile'),
    
    # teacher endpoints  PublicTeacherInfo
    path('teacher/teacher-register/',user_views.RegisterAPIView.as_view(), name='teacher_register'),
    path('teacher/teacher-profile/',user_views.GetTeacherProfileAPIView.as_view(),name='teacher-profile'),
    path('teacher/teacher-profile/<teacher_username>',user_views.PublicTeacherInfo.as_view(),name='teacher-profile-puplic-info'),
    
    path('teacher/update-profile/', user_views.UpdateTeacherProfileAPIView.as_view(), name='update-teacher-profile'),
    path('teacher/students/remove/<student_id>/', user_views.RemoveStudentAPIView.as_view(), name='teacher-student-remove'),
    path('teacher/students/toggle-block/<student_id>/', user_views.ToggleBlockStudentAPIView.as_view(), name='teacher-student-toggle-block'),
    path('teacher/get_students/',user_views.GetSudentRelatedToTeacherAPIView.as_view(),name="get-students"),
     path('teacher/revenue/', course_views.RevinewAPIView.as_view(), name='teacher-revenue'),
     path('get_student-enrollments/<course_id>', course_views.GetStudentEnrolledToCourseAPIView.as_view(), name='get-student-enrollments'),
     path('teacher/get-student-profile/<student_id>', user_views.GetStudentProfileAssositedWithTeacherAPIView.as_view(), name='get-student-profile-by-id'),
    # login paths
    path('teacher/login/', LoginView.as_view()),
    path('student/login/<teacher_username>/', LoginStudentAPIView.as_view(), name='student-login'),
    path('join-teacher/<teacher_username>/', user_views.AuthenticatedJoinTeacherAPIView.as_view(), name='authenticated-join-teacher'),
    path('logout/', LogoutView.as_view()),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='cookie_token_refresh'),
     path('student/refresh/<teacher_username>/', StudentRefreshView.as_view(), name='student-refresh'),
    
    # courses endpoint
    path('course/category/create/', course_views.CourseCategoryCreateAPIView.as_view(), name='course-category-create'),
    path('course/category/list/', course_views.CourseCategoryListAPIView.as_view(), name='course-category-list'),
    path('course/category/update/<category_id>',  course_views.CourseCategoryUpdateAPIView.as_view(), name='course-category-list'),
    path('course/create/', course_views.CourseCreateAPIView.as_view(), name='course-create'),
    path('course/list/',course_views.CourseListAPIView.as_view(),name='course-list'),
    path('course/teacher-list/<teacher_username>',course_views.CourseListForTeacherAPIView.as_view(),name='course-list-teacher'),
    path('course/course-detail/<course_id>',course_views.CourseDetailAPIView.as_view(),name='course-detail'),
    path('course/update/<course_id>',course_views.CourseUpdateAPIView.as_view(),name='course-update'),
    path('course/course-delete/<course_id>',course_views.CourseDeleteAPIView.as_view(),name='course-delete'),
    path('course/course-enrollment/',course_views.CourseEnrollmentAPIView.as_view(),name='course-enrollmnebt'),
    path('course/course-enrollment-list/<teacher_username>',course_views.CourseEnrollmentListAPIView.as_view(),name='course-enrollmnebt-list'),
    path('course/course-enrollment-delete/<course_id>/<enrollment_id>',course_views.CourseEnrollmentDeletAPIView.as_view(),name='course-enrollmnebt-delete'),
    path('course/course-search-filter/',course_views.CoursesFilterSerachAPIView.as_view(),name='course-search-filter'),
    path('course/module-enrollment/',course_views.ModuleEnrollmentAPIView.as_view(),name='module-enrollment'),
    path('course/private-deatils/<course_id>',course_views.courselistteacher.as_view(),name='module-enrollment-list'),
    # CuponEndpoints
    path('coupon/create/', course_views.CouponCreateAPIView.as_view(), name='coupon-create'),
    path('coupon/list/', course_views.CouponListAPIView.as_view(), name='coupon-list'), 
    path('coupon/detail/<coupon_id>', course_views.CouponDetailAPiView.as_view(), name='coupon-detail'),
    path('coupon/update/<coupon_id>', course_views.CouponUpdateAPIView.as_view(), name='coupon-update'),
    path('coupon/delete/<coupon_id>', course_views.CouponDeleteAPIView.as_view(), name='coupon-delete'),     
    path('coupon/used-coupons/', course_views.UsedCopunListAPIView.as_view(), name='coupon-usage'),
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
    # progress
    path('lessons/<uuid:id>/complete/', course_views.UpdateLessonProgressView.as_view(), name='lesson-progress-create'),
    # video status check
    path('video/check-status/<lesson_id>', course_views.CheckVideoStatusAPIView.as_view(), name='check-video-status'),
    
      # Assessment CRUD
     path('teacher/assessments/', 
         assessments_views.TeacherAssessmentListCreateView.as_view(), 
         name='teacher-assessment-list-create'), 
     
    path('teacher/courses/<uuid:course_id>/assessments/', 
         assessments_views.TeacherAssessmentListCreateView.as_view(), 
         name='teacher-assessment-list-create'),
    
    path('teacher/assessments/<uuid:assessment_id>/', 
         assessments_views.TeacherAssessmentRetrieveUpdateDestroyView.as_view(), 
         name='teacher-assessment-detail'),
    
    # Question CRUD
    path('teacher/assessments/<uuid:assessment_id>/questions/', 
         assessments_views.TeacherQuestionListCreateView.as_view(), 
         name='teacher-question-list-create'),
    
    path('teacher/assessments/questions/<uuid:question_id>/', 
         assessments_views.TeacherQuestionRetrieveUpdateDestroyView.as_view(), 
         name='teacher-question-detail'),
    
    # Question Options CRUD
    path('teacher/questions/<uuid:question_id>/options/', 
         assessments_views.TeacherQuestionOptionListCreateView.as_view(), 
         name='teacher-question-option-list-create'),
    
    path('teacher/questions/options/<uuid:option_id>/', 
         assessments_views.TeacherQuestionOptionRetrieveUpdateDestroyView.as_view(), 
         name='teacher-question-option-detail'),
    
    # student assessments
    path('student/assessments/<str:teacher_username>/', 
         assessments_views.StudentAssessmentListView.as_view(), 
         name='student-assessment-list'),
    
    # student start assessment
    path('student/assessments/<uuid:assessment_id>/<str:teacher_username>/start/', 
         assessments_views.StudentStartAssessmentView.as_view(), 
         name='student-start-assessment'),
    
    # student submit assessment
    path(
        'students/attempts/<uuid:attempt_id>/submit/',
        assessments_views.StudentSubmitAssessmentView.as_view(),
        name='student-submit-attempt'
    ),
    
    # all attemps
    path(
        'student/<str:teacher_username>/attempts/',
        assessments_views.StudentAssessmentAttemptListView.as_view(),
        name='student-assessment-attempt-list'
    ),
    
    # attemp result
    path(
        'student/attempts/<uuid:attempt_id>/result/',
        assessments_views.StudentAssessmentAttemptDetailView.as_view(),
        name='student-assessment-attempt-result'
    ),
    
    # Teacher Grading Endpoints
    
    # all questions that need to manual grading
    # additional filters (assessment_id,assessment_type,question_type)
    path('teacher/grading/pending/', 
         assessments_views.TeacherPendingGradingListView.as_view(), 
         name='teacher-pending-grading-list'),
    
    path('teacher/courses/<uuid:course_id>/grading/pending/', 
         assessments_views.TeacherPendingGradingListView.as_view(), 
         name='teacher-pending-grading-list'),
    
    path('teacher/assessments/<uuid:assessment_id>/grading/pending/', 
         assessments_views.TeacherPendingGradingListView.as_view(), 
         name='teacher-pending-grading-list'),
    
    path('teacher/assessments/<str:assessment_type>/grading/pending/', 
         assessments_views.TeacherPendingGradingListView.as_view(), 
         name='teacher-pending-grading-list'),
    
    path('teacher/assessments/questions/<str:question_type>/grading/pending/', 
         assessments_views.TeacherPendingGradingListView.as_view(), 
         name='teacher-pending-grading-list'),
    
    # teacher grade specific answer
    path('teacher/grading/answer/<uuid:answer_id>/', 
         assessments_views.TeacherGradeAnswerView.as_view(), 
         name='teacher-grade-answer'),
]

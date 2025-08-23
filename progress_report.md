### **Project: EduPro - Progress Report**

---

### **Technical Implementation Details**

*   **Technology Stack:**
    *   **Backend Framework:** Django
    *   **API Development:** Django REST Framework
    *   **Authentication:** djangorestframework-simplejwt (JSON Web Tokens)
    *   **Database:** PostgreSQL (psycopg2-binary)
    *   **Asynchronous Tasks:** Celery with Redis as the message broker
    *   **API Documentation:** drf-yasg (Swagger/OpenAPI)
    *   **Environment Variables:** python-decouple, python-dotenv
    *   **Image Processing:** Pillow
    *   **Video Processing:** moviepy, imageio-ffmpeg

*   **Database Schema Overview:**
    *   **`userAuth` Module:**
        *   `User`: A custom user model inheriting from `AbstractUser`, with roles for "Student" and "Teacher."
        *   `StudentProfile` and `TeacherProfile`: One-to-one related models to store specialized information for each user type.
        *   `TeacherStudentProfile`: A many-to-many through model to manage the relationship between teachers and students.
    *   **`course` Module:**
        *   `CourseCategory`: Organizes courses into distinct categories.
        *   `Course`: The central model for course information, linked to a `TeacherProfile`.
        *   `CourseModule` and `Lesson`: A hierarchical structure for organizing course content, with modules containing lessons.
        *   `CourseEnrollment` and `ModuleEnrollment`: Manage student enrollments at both the course and module levels.
        *   `Coupon` and `CouponUsage`: A system for creating and tracking promotional coupons.
        *   `Rating`: Allows students to rate and review courses.
        *   `StudentLessonProgress`: Tracks the completion status of each lesson for a student.
    *   **`assessments` Module:**
        *   `Assessment`: A flexible base model for creating quizzes, assignments, and course exams, linked to a `TeacherProfile` and a course, module, or lesson.
        *   `Question` and `QuestionOption`: A structured system for creating questions with various types (e.g., multiple choice, true/false, short answer) and their corresponding options.
        *   `StudentAssessmentAttempt`: Records each attempt a student makes on an assessment, including the start and end times, score, and status.
        *   `StudentAnswer`: Stores the student's answer for each question in an attempt, with support for both automated and manual grading.

---

### **API Endpoint Summary**

*   **`userAuth` Module:**
    *   **Authentication:**
        *   `POST /api/teacher/login/`: Teacher login.
        *   `POST /api/student/login/<teacher_username>/`: Student login.
        *   `POST /api/logout/`: User logout.
        *   `POST /api/token/refresh/`: Refresh JWT token.
        *   `POST /api/student/refresh/<teacher_username>/`: Student-specific token refresh.
    *   **Registration:**
        *   `POST /api/teacher/teacher-register/`: Teacher registration.
        *   `POST /api/student/student-register/<teacher_username>`: Student registration.
    *   **Profile Management:**
        *   `GET /api/teacher/teacher-profile/`: Get teacher profile.
        *   `GET /api/teacher/teacher-profile/<teacher_username>`: Get public teacher profile.
        *   `PUT/PATCH /api/teacher/update-profile/`: Update teacher profile.
        *   `GET /api/student/student-profile/<teacher_username>`: Get student profile.
        *   `PUT/PATCH /api/student/update-profile/`: Update student profile.
    *   **Teacher-Student Management:**
        *   `POST /api/join-teacher/<teacher_username>/`: Student joins a teacher.
        *   `GET /api/teacher/get_students/`: Get a list of a teacher's students.
        *   `DELETE /api/teacher/students/remove/<student_id>/`: Remove a student.
        *   `PATCH /api/teacher/students/toggle-block/<student_id>/`: Block/unblock a student.

*   **`course` Module:**
    *   **Course and Category Management:**
        *   `POST /api/course/category/create/`: Create a course category.
        *   `GET /api/course/category/list/`: List all course categories.
        *   `PUT/PATCH /api/course/category/update/<category_id>`: Update a course category.
        *   `POST /api/course/create/`: Create a new course.
        *   `GET /api/course/list/`: List all published courses.
        *   `GET /api/course/teacher-list/<teacher_username>`: List courses by a specific teacher.
        *   `GET /api/course/course-detail/<course_id>`: Get course details.
        *   `PUT/PATCH /api/course/update/<course_id>`: Update a course.
        *   `DELETE /api/course/course-delete/<course_id>`: Delete a course.
    *   **Enrollment:**
        *   `POST /api/course/course-enrollment/`: Enroll in a course.
        *   `GET /api/course/course-enrollment-list/<teacher_username>`: List course enrollments.
        *   `DELETE /api/course/course-enrollment-delete/<course_id>/<enrollment_id>`: Delete a course enrollment.
    *   **Content Management (Modules and Lessons):**
        *   `GET /api/courses/<course_id>/modules/`: List course modules.
        *   `POST /api/courses/<course_id>/modules/create/`: Create a course module.
        *   `GET /api/modules/<module_id>/`: Get module details.
        *   `PUT/PATCH /api/modules/<module_id>/update/`: Update a module.
        *   `DELETE /api/modules/<module_id>/delete/`: Delete a module.
        *   `GET /api/modules/<module_id>/lessons/`: List module lessons.
        *   `POST /api/modules/<module_id>/lessons/create/`: Create a lesson.
        *   `GET /api/lessons/<id>/`: Get lesson details.
        *   `PUT/PATCH /api/lessons/<id>/update/`: Update a lesson.
        *   `DELETE /api/lessons/<id>/delete/`: Delete a lesson.
    *   **Ratings and Reviews:**
        *   `GET /api/courses/<course_id>/list-ratings/`: List course ratings.
        *   `POST /api/courses/<course_id>/ratings/create/`: Create a rating.
        *   `GET/PUT/PATCH/DELETE /api/course/retrive-upadate-delete-ratings/<id>/`: Manage a specific rating.

*   **`assessments` Module:**
    *   **Assessment Management (Teacher):**
        *   `GET/POST /api/teacher/assessments/`: List or create assessments.
        *   `GET/PUT/PATCH/DELETE /api/teacher/assessments/<assessment_id>/`: Manage a specific assessment.
    *   **Question Management (Teacher):**
        *   `GET/POST /api/teacher/assessments/<assessment_id>/questions/`: List or create questions.
        *   `GET/PUT/PATCH/DELETE /api/teacher/assessments/questions/<question_id>/`: Manage a specific question.
    *   **Student Assessments:**
        *   `GET /api/student/assessments/<teacher_username>/`: List available assessments for a student.
        *   `POST /api/student/assessments/<assessment_id>/<teacher_username>/start/`: Start an assessment.
        *   `PUT /api/students/attempts/<attempt_id>/submit/`: Submit an assessment.
        *   `GET /api/student/<teacher_username>/attempts/`: List a student's assessment attempts.
        *   `GET /api/student/attempts/<attempt_id>/result/`: Get the result of an attempt.
    *   **Grading (Teacher):**
        *   `GET /api/teacher/grading/pending/`: List answers pending manual grading.
        *   `PUT/PATCH /api/teacher/grading/answer/<answer_id>/`: Grade a specific answer.

---

### **1. User Management and Authentication (`userAuth` module)**

*   **Role-Based User System:**
    *   **Dual User Roles:** The platform supports two distinct user roles: **Teacher** and **Student**, each with its own set of permissions and functionalities.
    *   **Separate Registration:** Dedicated registration endpoints for teachers and students ensure a clear and secure onboarding process.

*   **Authentication and Security:**
    *   **Secure JWT Authentication:** The system uses JSON Web Tokens (JWT) for secure user authentication, with tokens stored in cookies to enhance security.
    *   **Role-Based Login:** Separate login endpoints for teachers and students provide a tailored and secure authentication experience.
    *   **Secure Logout:** The logout functionality is designed to securely terminate user sessions by blacklisting refresh tokens.

*   **Profile Management:**
    *   **Comprehensive User Profiles:** Both teachers and students have detailed profiles that can be easily viewed and updated.
    *   **Public Teacher Profiles:** Teachers have public-facing profiles that showcase their expertise and course offerings.

*   **Teacher-Student Relationship Management:**
    *   **Seamless Student Enrollment:** Students can easily enroll with a teacher, establishing a clear connection within the platform.
    *   **Student Roster Management:** Teachers have access to a paginated and searchable list of their students, with options for filtering and ordering.
    *   **Student Management Tools:** Teachers can view detailed student profiles, block or unblock students, and remove them from their roster as needed.

---

### **2. Course and Content Management (`course` module)**

*   **Structured Content Hierarchy:**
    *   **Courses, Modules, and Lessons:** The platform supports a hierarchical content structure, allowing for the creation of well-organized and easy-to-navigate courses.
    *   **Flexible Content Types:** Lessons can include a variety of content formats, such as videos and documents, to create a rich and engaging learning experience.

*   **Course Management:**
    *   **Full CRUD Operations:** Teachers have complete control over their courses, with the ability to create, read, update, and delete them.
    *   **Advanced Filtering and Searching:** Robust filtering and searching capabilities make it easy for users to find courses based on various criteria.
    *   **Teacher-Specific Views:** Teachers can view a list of all the courses they have created, providing a clear overview of their content.

*   **Enrollment and Progress Tracking:**
    *   **Flexible Enrollment Options:** The system supports both course-level and module-level enrollments, giving students the flexibility to choose how they want to learn.
    *   **Student Progress Monitoring:** The platform tracks student progress at the lesson level, allowing for detailed monitoring of their learning journey.

*   **Monetization and Promotions:**
    *   **Coupon System:** A robust coupon system allows teachers to create and manage promotional offers and discounts for their courses.
    *   **Revenue Tracking:** Teachers can track their earnings and monitor the financial performance of their courses.

*   **Ratings and Reviews:**
    *   **Student Feedback:** Students can rate and review courses, providing valuable feedback for both teachers and prospective students.

---

### **3. Assessments and Grading (`assessments` module)**

*   **Versatile Assessment and Question Types:**
    *   **Multiple Assessment Formats:** The platform supports a variety of assessment types, including quizzes, assignments, and course exams.
    *   **Flexible Question Options:** A wide range of question formats, such as multiple choice, true/false, short answer, essay, and fill-in-the-blank, are available.

*   **Assessment Configuration and Control:**
    *   **Fine-Grained Settings:** Teachers have extensive control over assessment settings, including the ability to publish or unpublish, set time limits, and define the maximum number of attempts.
    *   **Scheduling and Availability:** Assessments can be scheduled with specific availability windows to ensure they are accessible at the appropriate times.

*   **Student Attempts and Grading:**
    *   **Comprehensive Attempt Tracking:** The system meticulously tracks student attempts, recording key information such as the attempt number, status, and time taken.
    *   **Automated and Manual Grading:** The platform supports both automated grading for objective questions and manual grading for subjective questions, providing a flexible and efficient workflow.
    *   **Personalized Feedback:** Teachers can provide detailed feedback on student attempts to help guide their learning and improvement.

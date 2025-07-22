erDiagram
    User {
        UUID id PK
        string email UK
        string first_name
        string last_name
        string username UK
        string phone UK
        string parent_phone
        string avatar
        string logo
        boolean is_active
        string user_type
        datetime created_at
        datetime updated_at
        datetime last_login
        string slug UK
    }

    StudentProfile {
        UUID id PK
        UUID user_id FK
        string full_name
        text bio
        string profile_picture
        date date_of_birth
        string address
        string country
        string city
        int number_of_courses
        int number_of_completed_courses
        string gender
    }

    TeacherProfile {
        UUID id PK
        UUID user_id FK
        string full_name
        text bio
        string profile_picture
        date date_of_birth
        string address
        string country
        string city
        int number_of_courses
        string specialization
        text experiance
        int number_of_students
        decimal rating
        datetime created_at
        string gender
    }

    CourseCategory {
        UUID id PK
        string name UK
        string description
        string slug
        string icon
    }

    Course {
        UUID id PK
        UUID teacher_id FK
        string title
        text description
        string trailer_video
        decimal price
        string status
        boolean is_free
        UUID category_id FK
        string slug
        string thumbnail
        datetime created_at
        int total_enrollments
        int total_lessons
        int total_reviews
        decimal average_rating
        int total_durations
    }

    CourseEnrollment {
        UUID id PK
        UUID student_id FK
        UUID course_id FK
        datetime enrollment_date
        datetime ended_date
        string status
        boolean is_completed
        boolean is_active
        decimal progress
    }

    Coupon {
        UUID id PK
        UUID teacher_id FK
        UUID course_id FK
        string code UK
        string status
        int max_uses
        int used_count
        datetime expiration_date
        int discount
        boolean is_active
        datetime date
    }

    User ||--o{ StudentProfile : "has"
    User ||--o{ TeacherProfile : "has"
    TeacherProfile }o--o{ User : "students"
    TeacherProfile ||--|{ Course : "creates"
    CourseCategory ||--|{ Course : "categorizes"
    StudentProfile ||--|{ CourseEnrollment : "enrolls in"
    Course ||--|{ CourseEnrollment : "is enrolled in"
    TeacherProfile ||--|{ Coupon : "creates"
    Course ||--|{ Coupon : "has"
    StudentProfile }o--o{ Coupon : "uses"

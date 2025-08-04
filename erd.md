erDiagram
    User {
        UUID id PK
        Email email UK
        String first_name
        String last_name
        String username UK
        String phone UK
        String parent_phone
        String avatar
        String logo
        Boolean is_active
        String user_type
        DateTime created_at
        DateTime updated_at
        DateTime last_login
        String slug UK
    }

    StudentProfile {
        UUID id PK
        UUID user_id FK
        String full_name
        Text bio
        String profile_picture
        Date date_of_birth
        String address
        String country
        String city
        String gender
    }

    TeacherProfile {
        UUID id PK
        UUID user_id FK
        String full_name
        Text bio
        String profile_picture
        Date date_of_birth
        String address
        String country
        String city
        Integer number_of_courses
        String specialization
        String institution
        Text experiance
        Integer number_of_students
        Decimal rating
        DateTime created_at
        String gender
        String logo
        String theme_color
    }

    TeacherStudentProfile {
        UUID teacher_id FK
        UUID student_id FK
        Date enrollment_date
        Text notes
        Boolean is_active
        Integer completed_lessons
        DateTime last_activity
        Integer number_of_completed_courses
    }

    CourseCategory {
        UUID id PK
        String name UK
        String icon
    }

    Course {
        UUID id PK
        UUID teacher_id FK
        UUID category_id FK
        String title
        Text description
        URL trailer_video
        Decimal price
        Boolean is_published
        Boolean is_free
        String thumbnail
        DateTime created_at
        Integer total_enrollments
        Integer total_lessons
        Integer total_reviews
        Decimal average_rating
        Integer total_durations
    }

    CourseEnrollment {
        UUID id PK
        UUID student_id FK
        UUID course_id FK
        DateTime enrollment_date
        DateTime ended_date
        String status
        Boolean is_completed
        Boolean is_active
        Decimal progress
    }

    Coupon {
        UUID id PK
        UUID teacher_id FK
        UUID course_id FK
        String code UK
        String status
        Integer max_uses
        Integer used_count
        DateTime expiration_date
        Integer discount
        Boolean is_active
        DateTime date
    }

    CouponUsage {
        UUID id PK
        UUID coupon_id FK
        UUID student_id FK
        DateTime used_at
    }

    CourseModule {
        UUID id PK
        UUID course_id FK
        String title
        Text description
        String image
        Integer order
        Boolean is_published
        DateTime created_at
        Integer total_lessons
        Integer total_duration
    }

    Lesson {
        UUID id PK
        UUID module_id FK
        String title
        Text description
        Integer order
        Boolean is_published
        Boolean is_free
        Integer duration
        DateTime created_at
        File video
        File document
        String thumbnail
    }

    User ||--o{ StudentProfile : "has one"
    User ||--o{ TeacherProfile : "has one"
    TeacherProfile ||--o{ TeacherStudentProfile : "manages"
    StudentProfile ||--o{ TeacherStudentProfile : "is managed by"
    TeacherProfile ||--o{ Course : "teaches"
    CourseCategory ||--o{ Course : "categorizes"
    StudentProfile ||--o{ CourseEnrollment : "enrolls in"
    Course ||--o{ CourseEnrollment : "has"
    TeacherProfile ||--o{ Coupon : "creates"
    Course ||--o{ Coupon : "applies to"
    Coupon ||--o{ CouponUsage : "used in"
    StudentProfile ||--o{ CouponUsage : "uses"
    Course ||--o{ CourseModule : "contains"
    CourseModule ||--o{ Lesson : "includes"

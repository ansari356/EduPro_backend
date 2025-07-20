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

    User ||--o{ StudentProfile : "has"
    User ||--o{ TeacherProfile : "has"
    TeacherProfile }o--o{ User : "students"

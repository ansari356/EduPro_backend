from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User , StudentProfile , TeacherProfile, TeacherStudentProfile
from django.db import transaction

class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True,required=True,validators=[validate_password])
    password2 = serializers.CharField(write_only=True,required=True)
    logo = serializers.ImageField(required=False, allow_null=True)  

    
    class Meta:
        model = User
        fields = ['first_name','last_name', 'username','email','phone','password1', 'password2','avatar','logo']
    
    def validate(self, attrs):
        if attrs.get('password1') != attrs.get('password2'):
            raise serializers.ValidationError({'password': "Passwords don't match"})
        return attrs
    
    
    def validate_email(self,value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value
    
    
    def validate_phone(self,value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('phone already exists')
        return value
    
    
    def validate_user_type(self, value):
        valid_types = [choice[0] for choice in User.userType.choices]
        if value not in valid_types:
            raise serializers.ValidationError('Invalid user type user_type must be only(student, teacher)')
        return value
        
    
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        
        user = User.objects.create_user(
            **validated_data,
            password=password,
            user_type=User.userType.TEACHER
        )
        return user


class StudentRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    parent_phone = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'phone', 'parent_phone', 'password1', 'password2', 'avatar']

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('Phone already exists')
        return value

    def create(self, validated_data):
        teacher_username = self.context['view'].kwargs.get('teacher_username')
        if not teacher_username:
            raise serializers.ValidationError({'teacher': 'Teacher username is required.'})

        try:
            teacher_profile = TeacherProfile.objects.select_related('user').get(
                user__username=teacher_username, 
                user__user_type=User.userType.TEACHER
            )
        except TeacherProfile.DoesNotExist:
            raise serializers.ValidationError({'teacher': 'Teacher with this username does not exist.'})

        validated_data.pop('password2')
        password = validated_data.pop('password1')

        with transaction.atomic():
            student_user = User.objects.create_user(
                **validated_data,
                password=password,
                user_type=User.userType.STUDENT
            )
            
         
            TeacherStudentProfile.objects.create(
                teacher=teacher_profile,
                student=student_user.student_profile
            )

        return student_user


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email' , 'phone']
        read_only_fields = fields
 

class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name', 'last_name', 'email', 'slug', 'phone', 'user_type', 'avatar', 'logo', 'is_active', 'created_at', 'last_login']
        read_only_fields =  fields


class StudentProfileSerializer(serializers.ModelSerializer):
    user = userSerializer(read_only=True)


    class Meta:
        model = StudentProfile
        fields = ['user', 'id', 'full_name', 'bio', 'profile_picture',  'date_of_birth', 'address', 'country', 'city', 'gender']
        read_only_fields = ['user', 'id', ]

            
        
class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserInfoSerializer(read_only=True)
    # students = serializers.SerializerMethodField()
    number_of_students = serializers.SerializerMethodField()
    number_of_courses = serializers.SerializerMethodField()
    class Meta:
        model = TeacherProfile
        fields = ['user', 'id', 'full_name', 'bio', 'profile_picture', 'date_of_birth', 'address', 'country', 'city', 'number_of_courses', 'specialization', 'institution', 'experiance', 'number_of_students', 'rating', 'gender','created_at', 'logo', 'theme_color']
        read_only_fields = ['students', 'rating', 'user', 'number_of_courses']

    # def get_students(self, obj):
    #     relations = TeacherStudentProfile.objects.filter(teacher=obj)
    #     student_profiles = [relation.student for relation in relations]
    #     return StudentProfileSerializer(student_profiles, many=True).data

    def get_number_of_students(self, obj):
        return obj.student_relations.count()
    
    
    def get_number_of_courses(self, obj):
        # Check if the value was annotated by the view
        if hasattr(obj, 'courses_count'):
            return obj.courses_count
        
        # Fallback for safety, though it's less efficient.
        # This should ideally not be hit if views are optimized.
        from course.models import Course
        return Course.objects.filter(teacher=obj).count()



class GetStudentRelatedToTeacherSerializer(serializers.ModelSerializer):
    students = serializers.SerializerMethodField()

    class Meta:
        model = TeacherProfile
        fields = ['students']

    def get_students(self, obj):
        relations = obj.student_relations.all()
        student_profiles = [relation.student for relation in relations]
        return StudentProfileSerializer(student_profiles, many=True).data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        return attrs


class JoinTeacherSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        student_user = User.objects.filter(
            email=email, 
            user_type=User.userType.STUDENT
        ).first()
        
        if not student_user:
            raise serializers.ValidationError({'email': 'Student with this email does not exist.'})
        
        if not student_user.check_password(password):
            raise serializers.ValidationError({'password': 'Incorrect password.'})

        attrs['student_user'] = student_user
        return attrs


class TeacherStudentProfileSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(read_only=True)
    number_of_enrollment_courses = serializers.SerializerMethodField()
    class Meta:
        model = TeacherStudentProfile
        fields = ['id', 'student' ,'enrollment_date', 'notes', 'is_active',  'completed_lessons', 'last_activity', 'number_of_completed_courses','number_of_enrollment_courses']

    def get_number_of_enrollment_courses(self, obj):
        # Check if the value was annotated by the view
        if hasattr(obj, 'enrollment_courses_count'):
            return obj.enrollment_courses_count
        
        # Fallback for safety, though it's less efficient.
        # This should ideally not be hit if views are optimized.
        return obj.student.enrollments.filter(course__teacher=obj.teacher).count()



class JoinAuthenticatedStudent(serializers.ModelSerializer):
    class Meta:
        model = TeacherStudentProfile
        fields = ['id', 'teacher', 'student', 'enrollment_date', 'notes', 'is_active', 'completed_lessons', 'last_activity', 'number_of_completed_courses']
        read_only_fields = fields

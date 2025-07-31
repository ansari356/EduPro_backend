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
            raise serializers.ValidationError('Invalid user type user_typre must be only(student, teacher, asisstant)')
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
    password1 = serializers.CharField(write_only=True,required=True,validators=[validate_password])
    password2 = serializers.CharField(write_only=True,required=True)
    parent_phone = serializers.CharField(required=True)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'phone', 'parent_phone', 'password1', 'password2', 'avatar']
    
    
    def validate(self, attrs):
            if attrs.get('password1') != attrs.get('password2'):
                raise serializers.ValidationError({'password': "Passwords don't match"})
            
            if not attrs.get('parent_phone'):
                raise serializers.ValidationError(
                    {"parent_phone": "Parent phone is required for students."}
                )

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
        if value != User.userType.STUDENT:
            raise serializers.ValidationError('User type must be student')
        return value
    

        
        

    def create(self, validated_data):
        username = self.context.get('view').kwargs.get('teacher_username')

        if not username:
            raise serializers.ValidationError({'teacher': 'Teacher username is required.'})

        try:
            teacher = User.objects.get(user_type=User.userType.TEACHER, username=username)
            teacher_profile = TeacherProfile.objects.get(user=teacher)
        except User.DoesNotExist:
            raise serializers.ValidationError({'teacher': 'Teacher with this username does not exist.'})
        except TeacherProfile.DoesNotExist:
            raise serializers.ValidationError({'teacher': 'Teacher profile not found.'})

        validated_data.pop('password2')
        password = validated_data.pop('password1')

        student_user = User.objects.create_user(
            **validated_data,
            password=password,
            user_type=User.userType.STUDENT
        )
        
        student_profile = StudentProfile.objects.get(user=student_user)
        
        TeacherStudentProfile.objects.create(
            teacher=teacher_profile,
            student=student_profile
        )

        return student_user


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', "avatar"]
        read_only_fields = fields
 

class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name', 'last_name', 'email', 'slug', 'phone', 'user_type', 'avatar', 'logo', 'is_active', 'created_at', 'last_login']
        read_only_fields =  fields


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserInfoSerializer(read_only=True)


    class Meta:
        model = StudentProfile
        fields = ['user', 'id', 'full_name', 'bio', 'profile_picture',  'date_of_birth', 'address', 'country', 'city', 'gender']
        read_only_fields = ['user', 'id', ]

            
        
class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserInfoSerializer(read_only=True)
    students = serializers.SerializerMethodField()
    number_of_students = serializers.SerializerMethodField()

    class Meta:
        model = TeacherProfile
        fields = ['user', 'id', 'full_name', 'bio', 'profile_picture', 'date_of_birth', 'address', 'country', 'city', 'number_of_courses', 'specialization', 'experiance', 'number_of_students', 'students', 'rating', 'gender']
        read_only_fields = ['students', 'rating', 'user', 'number_of_courses']

    def get_students(self, obj):
        relations = TeacherStudentProfile.objects.filter(teacher=obj)
        student_profiles = [relation.student for relation in relations]
        return StudentProfileSerializer(student_profiles, many=True).data

    def get_number_of_students(self, obj):
        return obj.student_relations.count()


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
    class Meta:
        model = TeacherStudentProfile
        fields = ['id', 'student', 'teacher' ,'enrollment_date', 'notes', 'is_active',  'completed_lessons', 'last_activity', 'student_id','number_of_courses', 'number_of_completed_courses']
        read_only_fields = ['enrollment_date', 'last_activity' , 'teacher','number_of_courses', 'number_of_completed_courses']



class JoinAuthenticatedStudent(serializers.Serializer):
    class Meta:
        model = TeacherStudentProfile
        read_only_fields = '__all__'
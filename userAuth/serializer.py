from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User , StudentProfile , TeacherProfile

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
        password1 = validated_data.pop('password1',None)
        validated_data.pop('password2',None)
        logo = validated_data.pop('logo', None)
        user = User(
            first_name = validated_data.get('first_name'),
            last_name = validated_data.get('last_name'),
            email = validated_data.get('email'),
            username=validated_data.get('username'),
            phone=validated_data.get('phone'),
            user_type=User.userType.TEACHER,
            avatar = validated_data.get('avatar', ''),
           
        )
        if user.user_type == User.userType.TEACHER and logo:
            user.logo = logo
            
        if password1:
            user.set_password(password1)
        user.save()
        return user


class StudentRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True,required=True,validators=[validate_password])
    password2 = serializers.CharField(write_only=True,required=True)
    parent_phone = serializers.CharField(required = False,allow_null=True , allow_blank=True)
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
    
        username = self.context.get('view').kwargs.get('teacherusername')
    
        if not username:
            raise serializers.ValidationError({'teacher': 'Teacher username is required.'})
        
        teacher = User.objects.filter(user_type=User.userType.TEACHER, username=username).first()

        if not teacher:
            raise serializers.ValidationError({'teacher': 'User is not a teacher'})
        
        password1 = validated_data.pop('password1', None)
        validated_data.pop('password2', None)
        
        user = User(
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            email=validated_data.get('email'),
            username=validated_data.get('username'),
            phone=validated_data.get('phone'),
            parent_phone=validated_data.get('parent_phone'),
            user_type= User.userType.STUDENT, 
            avatar=validated_data.get('avatar', ''),
        )
        
        if password1:
            user.set_password(password1)
        user.save()
        try:
            teacher_profile = TeacherProfile.objects.get(user=teacher)
            teacher_profile.students.add(user)
            teacher_profile.save() 
        except TeacherProfile.DoesNotExist:
            raise serializers.ValidationError({'teacher': 'Teacher profile not found.'})
        return user


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', "avatar", 'email']
        read_only_fields = fields
 

class userSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField() # لعرض عدد الطلاب المرتبطين بالمدرس
    students = UserInfoSerializer(many=True, read_only=True)  # لعرض معلومات الطلاب المرتبطين بالمدرس
    class Meta:
        model = User
        fields = ['id','first_name', 'last_name', 'email', 'slug', 'phone', 'user_type','students', 'avatar', 'logo', 'is_active', 'created_at', 'last_login', 'student_count']
        read_only_fields =  fields
    def get_student_count(self, obj):
        if hasattr(obj, 'teacher_profile'):
            return obj.teacher_profile.students.count()
        return 0
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.user_type == User.userType.STUDENT:
            representation.pop('student_count',None)
            representation.pop('students',None)

        elif instance.user_type == User.userType.TEACHER:
            representation.pop('teacher',None)
        return representation


class StudentProfileSerializer(serializers.ModelSerializer):
    user = userSerializer(read_only=True)
    teachers = serializers.SerializerMethodField()  
    class Meta:
        model = StudentProfile
        fields = ['user','id', 'full_name', 'bio', 'profile_picture', 'teachers', 'date_of_birth', 'address', 'country', 'city', 'number_of_courses', 'number_of_completed_courses','gender']
        read_only_fields = ['user','number_of_courses', 'number_of_completed_courses','teachers']
        
    def get_teachers(self, obj):
        teacher_profiles = obj.user.teachers.all()
        teacher_users = [profile.user for profile in teacher_profiles]
        return UserInfoSerializer(teacher_users, many=True).data
            
        
class TeacherProfileSerializer(serializers.ModelSerializer):
    user = userSerializer(read_only=True)
    students = UserInfoSerializer(many=True, read_only=True)  # لعرض معلومات الطلاب المرتبطين بالمدرس
    class Meta:
        model = TeacherProfile
        fields = ['user','id', 'full_name', 'bio',  'profile_picture', 'date_of_birth', 'address', 'country', 'city', 'number_of_courses','specialization','experiance','number_of_students','students', 'rating','gender']
        read_only_fields = ['number_of_students', 'students' , 'rating','user','number_of_courses']



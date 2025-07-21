from rest_framework import serializers
from django.shortcuts import  get_object_or_404
from .models import CourseCategory , Course , CourseEnrollment , Coupon
from userAuth.serializer  import TeacherProfileSerializer, StudentProfileSerializer

class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'icon']
        read_only_fields = ['id']

class CourseCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['id', 'name','icon']
        
    
    def create(self, validated_data):
        user = self.context['request'].user
        if not user.is_authenticated or user.user_type != user.userType.TEACHER:
            raise serializers.ValidationError({'user': 'User is not a teacher'})
        category = CourseCategory.objects.create(
            **validated_data,
        )
        return category
        

class CourseSerializer(serializers.ModelSerializer):
    category = CourseCategorySerializer(read_only=True)
    teacher = TeacherProfileSerializer(read_only=True)
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'teacher', 'trailer_video', 'price', 
            'is_published', 'is_free', 'category',  'thumbnail',
            'created_at', 'total_enrollments', 'total_lessons',
            'total_reviews', 'average_rating', 'total_durations'
        ]
        read_only_fields = ['id', 'created_at', 'total_enrollments',
                            'total_lessons', 'total_reviews', 
                            'average_rating', 'total_durations']


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['title', 'description', 'trailer_video', 'price', 'is_free', 'category', 'thumbnail']
    
    def validate(self, data):
        user = self.context['request'].user
        if user.user_type != user.userType.TEACHER:
            raise serializers.ValidationError({'teacher': 'User is not a teacher'})
        
        if data.get('is_free') and data.get('price',0) > 0:
            raise serializers.ValidationError({'price': 'Price must be 0 for free courses'}) 
        
        return data

    def create(self, validated_data):
        teacher = self.context['request'].user.teacher_profile
        course = Course.objects.create(
            teacher=teacher,
            **validated_data
        )
        teacher.number_of_courses += 1
        teacher.save(update_fields=['number_of_courses'])
        return course


class CouponCreateSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(write_only=True, required=True)  
    class Meta:
        model = Coupon
        fields = ['course_id','code', 'status', 'max_uses', 'expiration_date']
        
    
    def validate(self, data):
        user = self.context['request'].user
        if user.user_type != user.userType.TEACHER:
            raise serializers.ValidationError({'teacher': 'User is not a teacher'})
        return data
    
    
    def create(self, validated_data):
        user = self.context['request'].user
        course_id = validated_data.pop('course_id')
        course = get_object_or_404(Course, id=course_id)
        if not course:
            raise serializers.ValidationError({'course': 'Course is required'})
        
        if course.teacher != user.teacher_profile:
            raise serializers.ValidationError({'course': 'You are not the teacher of this course'})
        
        coupon = Coupon.objects.create(
            teacher=user.teacher_profile,
            course=course,
            is_active=True,
            **validated_data
        )
        return coupon
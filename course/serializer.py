from rest_framework import serializers
from django.shortcuts import  get_object_or_404
from .models import CourseCategory , Course , CourseEnrollment , Coupon , CouponUsage
from userAuth.serializer  import TeacherProfileSerializer, StudentProfileSerializer , UserInfoSerializer
from django.db import IntegrityError, transaction
from django.utils import timezone

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
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'trailer_video', 'price', 
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
        fields = ['course_id', 'status', 'max_uses', 'discount', 'expiration_date']
        
    
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

class CouponSerializer(serializers.ModelSerializer):

    class Meta:
        model = Coupon
        fields = ['id', 'course', 'teacher', 'code', 'status', 'max_uses', 'used_count', 'expiration_date', 'discount', 'is_active', 'date']
        read_only_fields = ['id', 'code', 'used_count', 'date', ]

class CourseEnrollmentCreateSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(write_only=True, required=True, allow_blank=True)
    course_id = serializers.UUIDField(write_only=True, required=True)
    
    class Meta:
        model = CourseEnrollment
        fields = ['course_id', 'coupon_code']

    
    def create(self, validated_data):
        user = self.context['request'].user
        course_id = validated_data.pop('course_id')
        coupon_code = validated_data.pop('coupon_code', None)
        student_profile = user.student_profile


        if not coupon_code:
            raise serializers.ValidationError({'coupon_code': 'Coupon code is required'})

        try:
            with transaction.atomic():
                # Optimize: Fetch coupon with related course and teacher in one query
                coupon = Coupon.objects.select_for_update().select_related(
                    'course', 'teacher'
                ).get(code=coupon_code)
                
                course = coupon.course  # Use course from coupon (already fetched)
                
                # Validate course ID matches
                if str(course.id) != str(course_id):
                    raise serializers.ValidationError({'course': 'Coupon is not valid for this course'})
                
                # Consolidated validations
                now = timezone.now()
                if coupon.expiration_date and coupon.expiration_date < now:
                    raise serializers.ValidationError({'coupon': 'Coupon has expired'})
                if coupon.used_count >= coupon.max_uses:
                    raise serializers.ValidationError({'coupon': 'Coupon has reached its maximum uses'})
                if not coupon.is_active:
                    raise serializers.ValidationError({'coupon': 'Coupon is not active'})
                if not course.is_published:
                    raise serializers.ValidationError({'course': 'Course is not published'})
                
                # Optimize: Check if user is student of teacher using efficient query
                if not coupon.teacher.students.filter(id=user.id).exists():
                    raise serializers.ValidationError({'user': 'You are not a student of this teacher.'})
                    
                # Check if already enrolled
                if CourseEnrollment.objects.filter(student=student_profile, course=course).exists():
                    raise serializers.ValidationError({'student': 'Student already enrolled in this course'})
                
               
                if coupon.status == Coupon.CouponType.FULL_ACCSESSED or coupon.discount == course.price:
                    enrollment = CourseEnrollment.objects.create(
                        student=student_profile,
                        course=course,
                        status=CourseEnrollment.EnrollmentStatus.COMPLETED,
                        is_active=True
                    )
                    
                   
                    CouponUsage.objects.create(
                        coupon=coupon,
                        student=student_profile,
                    )
                    
                    coupon.used_count += 1
                    if coupon.used_count >= coupon.max_uses:
                        coupon.is_active = False
                    coupon.save(update_fields=['used_count', 'is_active'])
                    
                    course.total_enrollments += 1
                    course.save(update_fields=['total_enrollments'])
               
                    return enrollment
                else:
                    raise serializers.ValidationError({'coupon': 'Coupon status does not allow enrollment'})
        
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({'coupon': 'Invalid coupon code'})
        except IntegrityError:
            raise serializers.ValidationError({'student': 'Concurrent enrollment attempt detected'})


class CouesEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = ['id', 'teacher', 'student', 'course', 'status', 'is_active', 'date']
        read_only_fields = ['id', 'date']
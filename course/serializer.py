from rest_framework import serializers
from django.shortcuts import  get_object_or_404
from moviepy.video.io.VideoFileClip import VideoFileClip
from .models import CourseCategory , Course , CourseEnrollment , Coupon , CouponUsage,Lesson,CourseModule, ModuleEnrollment,Rating,StudentLessonProgress
from userAuth.models import StudentProfile
from django.db import IntegrityError, transaction
from django.utils import timezone
from .utilis import genrate_coupon_code , genrate_otp
from datetime import timedelta
import uuid
import os
from django.core.files.storage import default_storage
import shutil
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


class CourseSerializerForTeacher(serializers.ModelSerializer):
    category = CourseCategorySerializer(read_only=True)
    class Meta:
        model = Course
        fields = "__all__"
        read_only_fields = read_only_fields = ['id', 'created_at', 'total_enrollments',
                            'total_lessons', 'total_reviews', 
                            'average_rating', 'total_durations',' total_revenue']



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
    number_of_coupons = serializers.IntegerField(min_value=1,write_only=True, required=True)
    class Meta:
        model = Coupon
        fields = ['number_of_coupons','price']


    def create(self, validated_data):
        user = self.context['request'].user
        number_of_coupons = validated_data.pop('number_of_coupons')
        coupons_to_create = []
        expiration_date = timezone.now() + timedelta(days=30)
        for _ in range(number_of_coupons):
            code = genrate_coupon_code(10)
            coupons_to_create.append(
                Coupon(
                    teacher=user.teacher_profile,
                    is_active=True,
                    code=code,
                    expiration_date=expiration_date,
                    **validated_data
                )
            )
        try:
            Coupon.objects.bulk_create(coupons_to_create, ignore_conflicts=True)
        except IntegrityError:
            pass

        return Coupon.objects.filter(teacher=user.teacher_profile).order_by('-date')
class CouponSerializer(serializers.ModelSerializer):

    class Meta:
        model = Coupon
        fields = ['id',  'teacher', 'code', 'status', 'max_uses', 'used_count', 'expiration_date', 'price', 'is_active', 'date']
        read_only_fields = ['id', 'code', 'used_count', 'date', ]

class CouponUsageSerialzier(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)
    student = serializers.ReadOnlyField(source='student.full_name')
    course = serializers.ReadOnlyField(source='course.title')
    module = serializers.ReadOnlyField(source='module.title')
    
    class Meta:
        model = CouponUsage
        fields = ['id', 'coupon', 'student', 'module', 'course', 'used_at']
        read_only_fields = ['id', 'used_at']


class CourseEnrollmentCreateSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    course_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:
        model = CourseEnrollment
        fields = ['course_id', 'coupon_code']

    def _validate_and_use_coupon(self, coupon_code, course, student_profile):
        try:
            coupon = Coupon.objects.select_for_update().select_related('teacher').get(code=coupon_code)
            now = timezone.now()

            if coupon.teacher != course.teacher:
                raise serializers.ValidationError({'coupon': 'Coupon is not valid for this course'})
            if coupon.expiration_date and coupon.expiration_date < now:
                raise serializers.ValidationError({'coupon': 'Coupon has expired'})
            if coupon.used_count >= coupon.max_uses:
                raise serializers.ValidationError({'coupon': 'Coupon has reached its maximum uses'})
            if not coupon.is_active:
                raise serializers.ValidationError({'coupon': 'Coupon is not active'})
            if not course.is_published:
                raise serializers.ValidationError({'course': 'Course is not published'})
            if not coupon.teacher.student_relations.filter(student=student_profile).exists():
                raise serializers.ValidationError({'user': 'You are not a student of this teacher.'})
            
            if coupon.status == Coupon.CouponType.FULL_ACCSESSED and coupon.price == course.price:
                CouponUsage.objects.create(coupon=coupon, student=student_profile , course=course)
                
                coupon.used_count += 1
                if coupon.used_count >= coupon.max_uses:
                    coupon.is_active = False
                coupon.save(update_fields=['used_count', 'is_active'])
                return True
            else:
                raise serializers.ValidationError({'coupon': 'Coupon status does not allow enrollment'})
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({'coupon': 'Invalid coupon code'})

    def create(self, validated_data):
        user = self.context['request'].user
        course_id = validated_data.pop('course_id')
        coupon_code = validated_data.pop('coupon_code', None)
        student_profile = user.student_profile
        course = get_object_or_404(Course, id=course_id)

        existing_enrollment = CourseEnrollment.objects.filter(student=student_profile, course=course).first()

        if existing_enrollment:
            if existing_enrollment.access_type == CourseEnrollment.AccessType.FULL_ACCESS:
                raise serializers.ValidationError({'student': 'Student already has full access to this course'})
            
            if coupon_code:
                with transaction.atomic():
                    if self._validate_and_use_coupon(coupon_code, course, student_profile):
                        existing_enrollment.access_type = CourseEnrollment.AccessType.FULL_ACCESS
                        existing_enrollment.status = CourseEnrollment.EnrollmentStatus.COMPLETED
                        existing_enrollment.save(update_fields=['access_type', 'status'])
                        return existing_enrollment
            else:
                raise serializers.ValidationError({'student': 'Student already enrolled in this course with no access. Provide a coupon to upgrade.'})

        else:
            if coupon_code:
                with transaction.atomic():
                    if self._validate_and_use_coupon(coupon_code, course, student_profile):
                        enrollment = CourseEnrollment.objects.create(
                            student=student_profile,
                            course=course,
                            access_type=CourseEnrollment.AccessType.FULL_ACCESS,
                            status=CourseEnrollment.EnrollmentStatus.COMPLETED,
                            is_active=True
                        )
                        course.total_revenue+=course.price
                        course.save(update_fields=['total_revenue'])
                        return enrollment
            else:
                enrollment = CourseEnrollment.objects.create(
                    student=student_profile,
                    course=course,
                    access_type=CourseEnrollment.AccessType.NO_ACCESS,
                    status=CourseEnrollment.EnrollmentStatus.PENDING,
                    is_active=True
                )
                return enrollment
        return existing_enrollment


class CouesEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = ['id', 'teacher', 'student', 'course', 'status', 'is_active', 'date']
        read_only_fields = ['id', 'date']


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['full_name', 'profile_picture']

class RatingListSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    class Meta:
        model = Rating
        fields = ['id', 'student', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'student', 'created_at']


class CourseRatingCreateSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    class Meta:
        model = Rating
        fields =['rating', 'comment']
        
    def validate_comment(self, value):
        if len(value) < 3 or len(value) > 500:
            raise serializers.ValidationError("Comment must be between 3 and 500 characters.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        course_id = self.context.get('course_id')
        
        try:
            student_profile = user.student_profile
        except AttributeError:
            raise serializers.ValidationError({'user': 'User is not a student'})
        
        course = get_object_or_404(Course, id=course_id)
        
        
        rating = Rating.objects.create(course=course, student=student_profile, **validated_data)
        return rating


class ModuleEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleEnrollment
        fields = '__all__'


class ModuleEnrollmentCreateSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    module_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:
        model = ModuleEnrollment
        fields = ['module_id', 'coupon_code']

    def _validate_and_use_coupon(self, coupon_code, module, student_profile):
        try:
            coupon = Coupon.objects.select_for_update().select_related('teacher').get(code=coupon_code)
            now = timezone.now()

            if coupon.teacher != module.course.teacher:
                raise serializers.ValidationError({'coupon': 'Coupon is not valid for this module'})
            if coupon.expiration_date and coupon.expiration_date < now:
                raise serializers.ValidationError({'coupon': 'Coupon has expired'})
            if coupon.used_count >= coupon.max_uses:
                raise serializers.ValidationError({'coupon': 'Coupon has reached its maximum uses'})
            if not coupon.is_active:
                raise serializers.ValidationError({'coupon': 'Coupon is not active'})
            if not module.is_published:
                raise serializers.ValidationError({'module': 'Module is not published'})
            if not coupon.teacher.student_relations.filter(student=student_profile).exists():
                raise serializers.ValidationError({'user': 'You are not a student of this teacher.'})
            
            if coupon.status == Coupon.CouponType.FULL_ACCSESSED and coupon.price == module.price:
                CouponUsage.objects.create(coupon=coupon, student=student_profile , module=module , course = module.course)
                coupon.used_count += 1
                if coupon.used_count >= coupon.max_uses:
                    coupon.is_active = False
                coupon.save(update_fields=['used_count', 'is_active'])
                return True
            else:
                raise serializers.ValidationError({'coupon': 'Coupon status does not allow enrollment'})
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({'coupon': 'Invalid coupon code'})

    def create(self, validated_data):
        user = self.context['request'].user
        module_id = validated_data.pop('module_id')
        coupon_code = validated_data.pop('coupon_code', None)
        student_profile = user.student_profile
        module = get_object_or_404(CourseModule, id=module_id)

        if ModuleEnrollment.objects.filter(student=student_profile, module=module).exists():
            raise serializers.ValidationError({'student': 'Student already enrolled in this module'})

        if coupon_code:
            with transaction.atomic():
                if self._validate_and_use_coupon(coupon_code, module, student_profile):
                    enrollment = ModuleEnrollment.objects.create(
                        student=student_profile,
                        module=module,
                        status=ModuleEnrollment.EnrollmentStatus.ACTIVE,
                        is_active=True
                    )
                    module.course.total_revenue+=module.price
                    module.course.save(update_fields=['total_revenue'])
                    

                    return enrollment
        elif module.price == 0 or module.is_free:
             enrollment = ModuleEnrollment.objects.create(
                student=student_profile,
                module=module,
                status=ModuleEnrollment.EnrollmentStatus.ACTIVE,
                is_active=True
            )
             return enrollment
        else:
            raise serializers.ValidationError({'coupon_code': 'Coupon code is required for paid modules.'})
        return None
    
    

    
# lesson serializers

class LessonSimpleSerializer(serializers.ModelSerializer):
    thumbnail=serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id','title','order', 'duration','thumbnail']
        read_only_fields = fields
        
    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

class LessonDetailSerializer(serializers.ModelSerializer):
    otp = serializers.SerializerMethodField()
    playback_info = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    module = serializers.CharField(source='module.title',read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'module', 'otp', 'playback_info', 'description', 'order',
            'is_published', 'is_free', 'duration',
            'created_at',  'document_url', 'thumbnail_url'
        ]

        read_only_fields = fields

    def get_document_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.document.url) if obj.document else None

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.thumbnail.url) if obj.thumbnail else None
    
    def get_otp(self, obj):
        otp, _ = genrate_otp(obj.video_id)
        return otp

    def get_playback_info(self, obj):
        _, playback_info = genrate_otp(obj.video_id)
        return playback_info



class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'order',
            'is_published', 'is_free', 'duration', 'video_id',
            'document', 'thumbnail', 'module'
        ]
        read_only_fields=['id', 'duration', 'module']
        extra_kwargs = {
            'video_id': {'required': True}
        }
        
    # validate_order
    def validate_order(self, value):
        if value and value <= 0:
            raise serializers.ValidationError("lesson order must be greater than 0")
        return value
    
    # validate_document
    def validate_document(self, value):
        if value and not value.name.lower().endswith(('.pdf', '.doc', '.docx','pptx')):
            raise serializers.ValidationError("The file must be in PDF or Word or powerpoint format.")
        return value
    
    # validate_thumbnail
    def validate_thumbnail(self, value):
        if value and not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise serializers.ValidationError("The image must be JPG or PNG or jpeg.")
        if value and value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Image larger than 2 MB")
        return value
    
    
    
    def create(self, validated_data):
        lesson = Lesson.objects.create(**validated_data)
        return lesson
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    
class StudentLessonProgressSerilaizer(serializers.ModelSerializer):
    class Meta:
        model=StudentLessonProgress
        fields=['id','is_completed']
        read_only_fields=['id']
            
# course module serializers

# To display the list of modules (light display without much detail).
class CourseModuleListSerializer(serializers.ModelSerializer):
    course=serializers.CharField(source='course.title',read_only=True)
    class Meta:
        model = CourseModule
        fields = ['id', 'title','course','description', 'order', 'price', 'is_free','is_published', 'total_lessons', 'total_duration']
        read_only_fields=fields
    
    
    
# To view full details for a single course module with it's lessons 
class CourseModuleDetailSerializer(serializers.ModelSerializer):
    course=serializers.CharField(source='course.title',read_only=True)
    lessons=serializers.SerializerMethodField()
    class Meta:
        model = CourseModule
        fields = ['id', 'title','course', 'order','price','is_free','is_published', 'total_lessons', 'total_duration','lessons']
        read_only_fields=fields
    
    
    
    def get_lessons(self,obj):
        request = self.context['request']
        user = self.context['request'].user
        lessons_qs = obj.lessons.all()
        
        if hasattr(user, 'teacher_profile'):
            if obj.course.teacher != user.teacher_profile:
                lessons_qs = lessons_qs.filter(is_published=True)
        else:
            lessons_qs = lessons_qs.filter(is_published=True)

        return LessonSimpleSerializer(lessons_qs, many=True,context=self.context).data


#create
class CourseModuleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields = [ 'title', 'description', 'order','is_published','is_free','price']
    
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title must not be empty.")
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value

    def validate_order(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("lesson order must be greater than 0")
        return value

        

# update,retrieve,delete
class CourseModuleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields=['title', 'description', 'order', 'is_published','price','is_free']
    
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title must not be empty.")
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value
    
    
    def validate_order(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("lesson order must be greater than 0")
        return value
    

class EarningSerializer(serializers.Serializer):
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)


class VdoCipherUploadCredentialSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)

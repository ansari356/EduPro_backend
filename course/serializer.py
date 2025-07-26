from rest_framework import serializers
from django.shortcuts import  get_object_or_404
from .models import CourseCategory , Course , CourseEnrollment , Coupon,Lesson,CourseModule,CourseEnrollment
from userAuth.serializer  import TeacherProfileSerializer, StudentProfileSerializer
from django.core.validators import FileExtensionValidator
from rest_framework.exceptions import PermissionDenied
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
from userAuth.models import User

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
    
    

    
# lesson serializers

class LessonSimpleSerializer(serializers.ModelSerializer):
    thumbnail=serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id','title', 'duration','thumbnail']
        read_only_fields = fields
        
    def get_thumbnail(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

class LessonDetailSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    module = serializers.CharField(source='module.title',read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'module', 'description', 'order',
            'is_published', 'is_free', 'duration',
            'created_at', 'video_url', 'document_url', 'thumbnail_url'
        ]

        read_only_fields = fields
    def get_video_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.video.url) if obj.video else None

    def get_document_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.document.url) if obj.document else None

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.thumbnail.url) if obj.thumbnail else None
class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'order',
            'is_published', 'is_free', 'duration',
            'video', 'document', 'thumbnail', 'module'
        ]
        read_only_fields=['duration','module']
        
    # validate_duration
    def validate_duration(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("lesson duration must be greater than 0")
        return value
    
    # validate_order
    def validate_order(self, value):
        if value and value <= 0:
            raise serializers.ValidationError("lesson order must be greater than 0")
        return value
    
    # validate_video
    def validate_video(self, value):
        if value and not value.name.lower().endswith(('.mp4', '.mov', '.avi')):
            raise serializers.ValidationError("Unsupported extensions ")
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
    
    def validate(self, attrs):
        module = attrs.get('module') or (self.instance.module if self.instance else None)
        order = attrs.get('order') or (self.instance.order if self.instance else None)

        if module and order:
            existing = Lesson.objects.filter(module=module, order=order)
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError("there is already lesson in this order")
        return attrs
    
    def get_video_duration(self, path):
        try:
            if not path.lower().endswith(('.mp4', '.mov', '.avi')):
                return 0
            clip = VideoFileClip(path)
            return clip.duration 
        except Exception as e:
            return 0
    
    # calculate duration after video saving
    def create(self,validated_data):
        video=validated_data.get('video',None)
        lesson=Lesson.objects.create(**validated_data)
        
        if video:
            duration = self.get_video_duration(lesson.video.path) # duration in seconds
            lesson.duration = int(duration)
            lesson.save()
        return lesson
    
    # manipulate video in update
    def update(self, instance, validated_data):
        video = validated_data.get('video', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if video:
            duration = self.get_video_duration(instance.video.path)
            instance.duration = int(duration)
            instance.save()
        return instance


# course module serializers

# To display the list of modules (light display without much detail).
class CourseModuleListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    course=serializers.CharField(source='course.title',read_only=True)
    class Meta:
        model = CourseModule
        fields = ['id', 'title','course', 'order', 'total_lessons', 'total_duration','image_url']
        read_only_fields=fields
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
    
# To view full details for a single course module with it's lessons 
class CourseModuleDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    course=serializers.CharField(source='course.title',read_only=True)
    lessons=lessons = serializers.SerializerMethodField()
    class Meta:
        model = CourseModule
        fields = ['id', 'title','course', 'order', 'total_lessons', 'total_duration','image_url','lessons']
        read_only_fields=fields
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_lessons(self,obj):
        request = self.context['request']
        user = self.context['request'].user
        lessons_qs = obj.lessons.all()
        
        if (
            obj.course.teacher != user.teacher_profile
        ):
            lessons_qs = lessons_qs.filter(is_published=True)

        return LessonSimpleSerializer(lessons_qs, many=True,context=self.context).data


#create
class CourseModuleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields = [ 'title','course', 'description', 'order','image']
    
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title must not be empty.")
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value
    
    def validate_course(self,value):
        if not value:
            raise serializers.ValidationError("Course must not be empty")

    def validate_image(self, value):
        if value:
            if not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError("The image must be JPG or PNG.")
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Image size must be less than 2MB.")
        return value
    
    def validate_order(self, value):
        if value and value <= 0:
            raise serializers.ValidationError("lesson order must be greater than 0")
        return value
    
    def validate(self,attrs):
        course = self.context.get('course')
        order=attrs.get('order')
        
        if course and order:
            existing=CourseModule.objects.filter(course=course,order=order).exists()

            if existing :
                raise serializers.ValidationError("there is already course in this order")
        
        return attrs
        

# update,retrieve,delete
class CourseModuleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields=['title', 'description', 'order', 'is_published', 'image']
    
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title must not be empty.")
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value
    
    def validate_image(self, value):
        if value:
            if not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError("The image must be JPG or PNG.")
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Image size must be less than 2MB.")
        return value
    
    def validate_order(self, value):
        if value and value <= 0:
            raise serializers.ValidationError("Module order must be greater than 0")
        return value
    
    def validate(self,attrs):
        module=self.context.get('module')
        course=module.course
        order=self.context.get('order')
        
        existing=CourseModule.objects.filter(course=course,order=order)
        
        if self.instance:
            existing=existing.exclude(id=self.instance.id)

        if existing.exists():
            raise serializers.ValidationError("There is already a module with this order in the course.")
        return attrs
from rest_framework import serializers
from .models import CourseCategory , Course , CourseEnrollment


class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'description', 'slug', 'icon']
        

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'trailer_video', 'price', 
            'status', 'is_free', 'category', 'slug', 'thumbnail',
            'created_at', 'total_enrollments', 'total_lessons',
            'total_reviews', 'average_rating', 'total_durations'
        ]
        read_only_fields = ['id', 'created_at', 'total_enrollments',
                            'total_lessons', 'total_reviews', 
                            'average_rating', 'total_durations']


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['title', 'description', 'trailer_video', 'price', 'status', 'is_free', 'category', 'thumbnail']

    

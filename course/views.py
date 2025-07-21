from django.shortcuts import render , get_object_or_404
from rest_framework import generics, permissions
from .models import CourseCategory, Course, CourseEnrollment
from .serializer import (CourseCategorySerializer, 
CourseCategoryCreateSerializer, CourseSerializer, CourseCreateSerializer,CouponCreateSerializer
)
from rest_framework.response import Response
from rest_framework import status
# Create your views here.


class CourseCategoryCreateAPIView(generics.CreateAPIView):
    serializer_class = CourseCategoryCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "message": 'category created successfully',
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class CourseCategoryListAPIView(generics.ListAPIView):
    queryset = CourseCategory.objects.all()
    serializer_class = CourseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    


class courseCreateAPIView(generics.CreateAPIView):
    serializer_class = CourseCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "message": 'course created successfully',
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
        
class CourseListAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return Course.objects.filter(is_published=True).select_related('teacher', 'category').order_by('-created_at')


class CouponCreateAPIView(generics.CreateAPIView):
    serializer_class = CouponCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()
        
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "message": 'Coupon created successfully',
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
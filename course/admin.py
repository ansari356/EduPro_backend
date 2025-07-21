from django.contrib import admin
from .models import CourseCategory, Course, CourseEnrollment , Coupon

# Register your models here.

class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(CourseCategory, CourseCategoryAdmin)


class CourseAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'teacher', 'category', 'is_published', 'price', 'created_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'description')
    raw_id_fields = ('teacher',)


admin.site.register(Course, CourseAdmin)


class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'teacher', 'course', 'status', 'max_uses', 'expiration_date')
    list_filter = ('status',)
    search_fields = ('code',)
    raw_id_fields = ('teacher', 'course')
    
admin.site.register(Coupon, CouponAdmin)
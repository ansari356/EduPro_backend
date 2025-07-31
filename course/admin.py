from django.contrib import admin
from .models import CourseCategory, Course, CourseEnrollment , Coupon ,CouponUsage,CourseModule,Lesson

# Register your models here.

class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name')
    search_fields = ('name',)

admin.site.register(CourseCategory, CourseCategoryAdmin)


class CourseAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'teacher', 'category', 'is_published', 'price', 'created_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'description')
    raw_id_fields = ('teacher',)


admin.site.register(Course, CourseAdmin)




class CouponAdmin(admin.ModelAdmin):
    list_display = ('id','code', 'teacher', 'course', 'status', 'max_uses', 'expiration_date')
    list_filter = ('status',)
    search_fields = ('code',)
    raw_id_fields = ('teacher', 'course')
    
admin.site.register(Coupon, CouponAdmin)

class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id','student', 'course', 'status',  'enrollment_date','ended_date')
    list_filter = ('status',)
    search_fields = ('student',)
    raw_id_fields = ('student', 'course')

admin.site.register(CourseEnrollment ,CourseEnrollmentAdmin)


class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('student', 'coupon', 'used_at')
    list_filter = ('student', 'coupon')
    search_fields = ('student', 'coupon')
    raw_id_fields = ('student', 'coupon')

admin.site.register(CouponUsage, CouponUsageAdmin)


class CourseModuleAdmin(admin.ModelAdmin):
    list_display =['id','course','title','description','is_published','created_at','total_lessons','total_duration']
    list_filter = ('title','course')
    search_fields = ('title','course')
    
admin.site.register(CourseModule, CourseModuleAdmin)

class LessonAdmin(admin.ModelAdmin):
    list_display =['id','module','title','description','is_published','created_at','is_free','duration']
    list_filter = ('title','module')
    search_fields = ('title','module')
admin.site.register(Lesson, LessonAdmin)

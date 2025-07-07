from django.contrib import admin
from .models import User , StudentProfile , TeacherProfile 
# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'phone', 'user_type', 'is_active', 'created_at', 'updated_at','last_login')
    list_filter = ('user_type', 'is_active')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-created_at',)


admin.site.register([StudentProfile,TeacherProfile])

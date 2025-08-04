from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User , StudentProfile , TeacherProfile, TeacherStudentProfile
# Register your models here.
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'phone', 'user_type', 'is_active', 'created_at', 'updated_at','last_login', 'refresh_token',)
    list_filter = ('user_type', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "username",
                    "phone",
                    "parent_phone",
                    "avatar",
                    "logo",
                   "refresh_token",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "user_type" ,"is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'username', 'email', 'phone','user_type', 'password1', 'password2', 'avatar', 'logo'),
        }),
    )
    readonly_fields = ('last_login', 'created_at', 'updated_at')

# admin.site.register(User)
admin.site.register([StudentProfile,TeacherProfile])


@admin.register(TeacherStudentProfile)
class TeacherStudentProfileAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'student', 'enrollment_date', 'is_active', 'last_activity')
    list_filter = ('teacher', 'student', 'is_active')
    search_fields = ('teacher__user__username', 'student__user__username')
    readonly_fields = ('enrollment_date', 'last_activity')
    list_per_page = 20

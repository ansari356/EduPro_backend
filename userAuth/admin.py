from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User , StudentProfile , TeacherProfile
# Register your models here.
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'phone', 'user_type', 'is_active', 'created_at', 'updated_at','last_login')
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

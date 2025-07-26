from rest_framework import permissions

class IsTeacher(permissions.BasePermission):

    message = "Only teachers are allowed to perform this action"

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == request.user.userType.TEACHER
        )
        
class IsStudent(permissions.BasePermission):

    message = "Only students are allowed to perform this action"

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == request.user.userType.STUDENT
        )
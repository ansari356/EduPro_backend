from django.forms import ValidationError
from django.shortcuts import render , get_object_or_404
from rest_framework import generics, status 
from rest_framework.response import Response
from rest_framework.permissions import AllowAny , IsAuthenticated
from django.core.exceptions import PermissionDenied
from .serializer import RegisterSerializer,StudentRegistrationSerializer ,StudentProfileSerializer , TeacherProfileSerializer, TeacherStudentProfileSerializer, GetStudentRelatedToTeacherSerializer,JoinAuthenticatedStudent,LoginSerializer,UserInfoSerializer
from .models import User , StudentProfile , TeacherProfile, TeacherStudentProfile
from course.permissions import IsStudent , IsTeacher
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from rest_framework.pagination import PageNumberPagination
# Create your views here.
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                'username': user.username,
                "user_type": user.user_type,
                'slug': user.slug,
                "avatar": user.avatar.url if user.avatar else None,
                "logo": user.logo.url if user.logo else None,
            }
        }, status=201)


class RegisterStudentAPIView(generics.CreateAPIView):
    serializer_class = StudentRegistrationSerializer
    permission_classes = [AllowAny] 

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['view'] = self
        return context
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response({
            "message": "Student created successfully",
                "user": {
                "id": student.id,
                "email": student.email,
                "phone": student.phone,
                "parent_phone":student.parent_phone,
                'username': student.username,
                "user_type": student.user_type,
                'slug': student.slug,
                "avatar": student.avatar.url if student.avatar else None,
            }
            }, status=201)


class AuthenticatedJoinTeacherAPIView(generics.CreateAPIView):
    serializer_class = JoinAuthenticatedStudent
    permission_classes = [IsStudent]

    def create(self, request, *args, **kwargs):
        teacher_username = self.kwargs.get('teacher_username')
        
        if not teacher_username:
            return Response(
                {'error': 'Teacher username is required in the URL.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            teacher_user = User.objects.get(
                username=teacher_username,
                user_type=User.userType.TEACHER
            )
            teacher_profile = teacher_user.teacher_profile
        except User.DoesNotExist:
            return Response(
                {'error': 'Teacher not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except TeacherProfile.DoesNotExist:
            return Response(
                {'error': 'Teacher profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        student_user = self.request.user
        
        student_profile, _ = StudentProfile.objects.get_or_create(user=student_user)
        
        relation, created = TeacherStudentProfile.objects.get_or_create(
            teacher=teacher_profile,
            student=student_profile
        )
        
        if created:
            return Response(
                {'success': 'Student joined successfully.'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'info': 'Student is already associated with this teacher.'},
                status=status.HTTP_200_OK
            )


class GetStudentProfileAPIView(generics.RetrieveAPIView):
    serializer_class = TeacherStudentProfileSerializer
    permission_classes = [IsStudent]
    queryset = TeacherStudentProfile.objects.all()

    def get_object(self):
        user = self.request.user
        student_profile = get_object_or_404(StudentProfile, user=user)
        teacher_username = self.kwargs.get('teacher_username')

        if not teacher_username:
            raise ValidationError({'teacher_id': 'teacher username is required'})

        teacher_user = get_object_or_404(User, user_type=User.userType.TEACHER, username=teacher_username)
        teacher_profile = get_object_or_404(TeacherProfile, user=teacher_user)

        queryset = self.get_queryset().select_related(
            'student__user', 'teacher__user'
        ).annotate(
            enrollment_courses_count=Count(
                'student__enrollments',
                filter=Q(student__enrollments__course__teacher=teacher_profile)
            )
        )

        obj = get_object_or_404(
            queryset,
            student=student_profile,
            teacher=teacher_profile
        )
        self.check_object_permissions(self.request, obj)
        return obj

class BasePagination(PageNumberPagination):
    page_size = 1


class GetSudentRelatedToTeacherAPIView(generics.ListAPIView):
    serializer_class = GetStudentRelatedToTeacherSerializer
    permission_classes = [IsTeacher]
    pagination_class = BasePagination

    

    def get_queryset(self):
        user = self.request.user
        try:
            teacher_profile = TeacherProfile.objects.get(user=user)
            return TeacherStudentProfile.objects.filter(teacher=teacher_profile).select_related(
                'student__user'
            ).order_by('student__full_name')
            
        except TeacherProfile.DoesNotExist:
            return TeacherStudentProfile.objects.none()


class ToggleBlockStudentAPIView(APIView):
    """
    A view for a teacher to toggle the block status of a student.
    This action flips the 'is_active' flag on the TeacherStudentProfile.
    """
    permission_classes = [IsTeacher]

    def patch(self, request, *args, **kwargs):
        teacher_profile = request.user.teacher_profile
        student_id = self.kwargs.get('student_id')
        student_profile = get_object_or_404(StudentProfile, user__id=student_id)
        if not student_id:
            raise ValidationError({'student_id': 'Student ID is required in the URL.'})

        # Retrieve the specific student-teacher relationship instance
        instance = get_object_or_404(
            TeacherStudentProfile,
            teacher=teacher_profile,
            student=student_profile,
        )

        instance.is_active = not instance.is_active
        instance.save(update_fields=['is_active'])

        if instance.is_active:
            message = "Student has been unblocked."
        else:
            message = "Student has been blocked."

        return Response({"message": message}, status=status.HTTP_200_OK)
        

class GetTeacherProfileAPIView(generics.RetrieveAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsTeacher]
    queryset = TeacherProfile.objects.all()

    def get_object(self) -> TeacherProfile:
        user: User = self.request.user
        if user.user_type != User.userType.TEACHER:
            raise PermissionDenied("You are not a Teacher.")

        queryset = self.get_queryset().select_related('user').annotate(
            courses_count=Count('courses')
        )
        
        obj = get_object_or_404(queryset, user=user)
        self.check_object_permissions(self.request, obj)
        return obj


class PublicTeacherInfo(generics.RetrieveAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [AllowAny]
    queryset = TeacherProfile.objects.all()

    def get_object(self):
        
        teacher_username = self.kwargs.get('teacher_username')

        if not teacher_username:
            raise ValidationError({'teacher_id': 'teacher username is required'})

        user = get_object_or_404(User, user_type=User.userType.TEACHER, username=teacher_username)
        
        

        queryset = self.get_queryset().select_related('user').annotate(
            courses_count=Count('courses')
        )
        
        
        
        obj = get_object_or_404(queryset, user=user)
        self.check_object_permissions(self.request, obj)
        return obj


class UpdateStudentProfileAPIView(generics.UpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsStudent]
    
    def get_object(self) -> StudentProfile:
        user: User = self.request.user
        if user.user_type == User.userType.STUDENT:
            return get_object_or_404(StudentProfile.objects.select_related('user'), user=user)
        else:
            raise PermissionDenied("You are not a Student.")


class UpdateTeacherProfileAPIView(generics.UpdateAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsTeacher]

    def get_object(self) -> TeacherProfile:
        user: User = self.request.user
        if user.user_type == User.userType.TEACHER:
            return get_object_or_404(TeacherProfile.objects.select_related('user'), user=user)
        else:
            raise PermissionDenied("You are not a Teacher.")


class RemoveStudentAPIView(generics.DestroyAPIView):
    serializer_class = TeacherStudentProfileSerializer
    permission_classes = [IsTeacher]
    
    def get_object(self):
        user  = self.request.user
        teacher = get_object_or_404(TeacherProfile.objects.select_related('user') , user=user)
        student_id = self.kwargs.get('student_id')
        if not student_id:
            raise ValidationError({'student_id': 'student id is required'})
        student = get_object_or_404(User, user_type=User.userType.STUDENT, id=student_id)
        student_profile = get_object_or_404(StudentProfile.objects.select_related('user') , user=student)
        return get_object_or_404(TeacherStudentProfile.objects.select_related('student' , 'teacher') , student=student_profile , teacher=teacher)

# login views

class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    def post(self,request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            email = validated_data.get('email')
            password = validated_data.get('password')
            user=authenticate(username=email,password=password)
            
            if user is not None and user.user_type != User.userType.STUDENT:
                refresh=RefreshToken.for_user(user)
                access_token=str(refresh.access_token)
                refresh_token=str(refresh)
                
               
            

                res=Response(UserInfoSerializer(user).data,status=200)
                
                # set token into cokkie
                res.set_cookie(
                    
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    secure=False,
                    samesite='Lax'
                )
                res.set_cookie(
                    
                    key='refresh_token',
                    value=refresh_token,
                    httponly=True,
                    secure=False,
                    samesite='Lax',
                    # path='/api/v1/token/refresh/'
                )
                
               
                
                return res
            else:
                return Response({"error": "Invalid credentials"}, status=401)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginStudentAPIView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, teacher_username):
        
     
        
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        email = validated_data.get('email')
        password = validated_data.get('password')

        try:
            teacher_user = User.objects.select_related('teacher_profile').get(username=teacher_username, user_type=User.userType.TEACHER)
        except User.DoesNotExist:
            return Response({"error": "Teacher not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user_to_check = User.objects.select_related('student_profile').get(email=email)
            if user_to_check.user_type != User.userType.STUDENT:
                return Response({"error": "Invalid user type. User is not a student."}, status=status.HTTP_400_BAD_REQUEST)
            # check if the user belongs to the teacher
            
            if not TeacherStudentProfile.objects.filter(student=user_to_check.student_profile, teacher=teacher_user.teacher_profile).exists():
                return Response({"error": f"You are not registered as a student for this teacher."}, status=status.HTTP_403_FORBIDDEN)
            
            if user_to_check.refresh_token and user_to_check.is_active:
                try:
                    RefreshToken(user_to_check.refresh_token)
                    return Response({"error": "User is already logged in from another device."}, status=status.HTTP_403_FORBIDDEN)
                except TokenError:
                    # Token is invalid, allow login
                    pass
            if not hasattr(user_to_check, 'student_profile'):
                return Response({"error": "Invalid user type. Student profile not found."}, status=status.HTTP_400_BAD_REQUEST)
                
            if not TeacherStudentProfile.objects.filter(student=user_to_check.student_profile, teacher=teacher_user.teacher_profile).exists():
                return Response({"error": f"You are not registered as a student for {teacher_username}."}, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials. Please check your email and password"}, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(username=email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            user.refresh_token = refresh_token
            user.save(update_fields=['refresh_token'])

            res = Response(UserInfoSerializer(user).data, status=status.HTTP_200_OK)
            
            res.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=False, 
                samesite='Lax'
            )
            res.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite='Lax',
            )
            return res
        else:
            return Response({"error": "Invalid credentials. Please check your email and password."}, status=status.HTTP_401_UNAUTHORIZED)


# logout view supports blacklist
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token: 
                 return Response({'message':'No refresh token found'},status=400)
            token=RefreshToken(refresh_token)
            token.blacklist()
        
            user = request.user
            if user.user_type == User.userType.STUDENT:
                user.refresh_token = None
                user.save(update_fields=['refresh_token'])

            res=Response({"message": "Logged out successfully"},status=status.HTTP_205_RESET_CONTENT)
            res.delete_cookie('access_token') 
            res.delete_cookie('refresh_token') 
            
            return res
        except TokenError :
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # It's good practice to log the exception e
            return Response({"error": "An unexpected error occurred during logout."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# refresh token view (cokkies)
class CookieTokenRefreshView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        refresh_token = request.COOKIES.get('refresh_token')
        print(request.COOKIES)
        if refresh_token is None:
            return Response({'error':'Refresh token not found'},status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh=RefreshToken(refresh_token)
            access_token=str(refresh.access_token)
        except TokenError:

            return Response({'error': 'Invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        res=Response({'message':'Token refreshed successfully'},status=status.HTTP_200_OK)
        res.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            samesite='Lax',
            secure=False
        )
        return res


class StudentRefreshView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, teacher_username):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response({'error': 'Refresh token not found'}, status=status.HTTP_401_UNAUTHORIZED)

        # Validate teacher_username first
        try:
            teacher = get_object_or_404(User, username=teacher_username, user_type=User.userType.TEACHER)
            teacher_profile = get_object_or_404(TeacherProfile, user=teacher)
        except (User.DoesNotExist, TeacherProfile.DoesNotExist):
            return Response({'error': 'Invalid teacher specified.'}, status=status.HTTP_404_NOT_FOUND)

        # Perform student-teacher relationship check if user is authenticated and has a student profile
        if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
            student_profile = request.user.student_profile
            if not TeacherStudentProfile.objects.filter(student=student_profile, teacher=teacher_profile).exists():
                return Response({'error': 'You are not registered as a student for this teacher.'}, status=status.HTTP_403_FORBIDDEN)
        # If user is not authenticated or not a student, we skip the student-teacher relationship check.
        # The token refresh will proceed if the refresh token is valid.

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
        except TokenError:
            return Response({'error': 'Invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        res = Response({'message': 'Token refreshed successfully'}, status=status.HTTP_200_OK)
        res.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            samesite='Lax',
            secure=False
        )
        return res

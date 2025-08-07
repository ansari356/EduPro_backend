from django.shortcuts import render
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from userAuth.serializer import LoginSerializer,UserInfoSerializer
from userAuth.models import User , TeacherStudentProfile



# Create your views here.


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
            return Response({"error": "A user with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

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

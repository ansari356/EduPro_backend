from django.shortcuts import render
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from userAuth.serializer import LoginSerializer,UserInfoSerializer
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
            
            if user is not None:
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


# logout view supports blacklist
class LogoutView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token: 
                 return Response({'message':'No refresh token found'},status=400)
            
            token=RefreshToken(refresh_token)
            token.blacklist()
            res=Response({"message": "Logged out successfully"},status=205)
            res.delete_cookie('access_token') 
            res.delete_cookie('refresh_token') 
            
            return res
        except TokenError :
            return Response({"error": "Invalid token"}, status=400)

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

        res=Response({'message':'Token refreshed successfully'},status=200)
        res.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            samesite='Lax',
            secure=False
        )
        return res

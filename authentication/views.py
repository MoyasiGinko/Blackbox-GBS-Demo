from django.shortcuts import render
from django.http.response import HttpResponsePermanentRedirect
from django.shortcuts import redirect
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, views, permissions, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg import openapi
from django.conf import settings
from django.utils import timezone
import jwt
import os
from .utils import send_email
from .models import (
    User, Subscription, Payment, Service, 
    UserService, Cookie, CookieInjectionLog, LoginAttempt
)
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import (
    UserCreateSerializer, LoginSerializer, EmailVerificationSerializer,
    ResetPasswordEmailRequestSerializer, SetNewPasswordSerializer,
    LogoutSerializer, SubscriptionSerializer, ServiceSerializer,
    UserServiceSerializer, PaymentSerializer, CookieSerializer
)

class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = [os.environ.get('APP_SCHEMA'), 'http', 'https']

class RegisterView(generics.GenericAPIView):
    serializer_class = UserCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        verification_token = RefreshToken.for_user(user).access_token
        verification_url = f"{os.environ.get('FRONTEND_BASE_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"
        send_email(
            subject="Verify your email",
            recipient_list=[user.email],
            message=f"Please verify your email by clicking on the following link: {verification_url}"
        )
        
        return Response({
            'email': user.email,
            'message': "Successfully registered. Please verify your email"
        }, status=status.HTTP_201_CREATED)

class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    token_param_config = openapi.Parameter(
        'token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            if not user.email_verified:
                user.email_verified = True
                user.is_active = True
                user.save()
            return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Activation link expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Log the login attempt
        LoginAttempt.objects.create(
            user=User.objects.get(email=serializer.validated_data['email']),
            success=True,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            location_data={
                'ip': request.META.get('REMOTE_ADDR'),
                'forwarded_for': request.META.get('HTTP_X_FORWARDED_FOR', '')
            }
        )
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        email = request.data.get('email', '')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            verification_token = RefreshToken.for_user(user).access_token
            reset_url = f"{os.environ.get('FRONTEND_BASE_URL', 'http://localhost:3000')}/reset-password?token={verification_token}"
            send_email(
                subject="Reset your password",
                recipient_list=[user.email],
                message=f"Please reset your password by clicking on the following link: {reset_url}"
            )
        return Response(
            {'success': 'If an account exists with this email, we have sent a password reset link'},
            status=status.HTTP_200_OK
        )

class PasswordTokenCheckApi(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):
        redirect_url = request.GET.get('redirect_url', '')
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {'error': 'Token is not valid, please request a new one'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'success': True, 'message': 'Credentials Valid', 'uidb64': uidb64, 'token': token},
                status=status.HTTP_200_OK
            )
        except DjangoUnicodeDecodeError:
            return Response(
                {'error': 'Token is not valid, please request a new one'},
                status=status.HTTP_400_BAD_REQUEST
            )

class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {'success': True, 'message': 'Password reset successful'},
            status=status.HTTP_200_OK
        )

class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

class UserServiceViewSet(viewsets.ModelViewSet):
    serializer_class = UserServiceSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return UserService.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subscription.objects.filter(is_active=True)
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CookieViewSet(viewsets.ModelViewSet):
    serializer_class = CookieSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Cookie.objects.filter(user_service__user=self.request.user)

    def perform_create(self, serializer):
        user_service = serializer.validated_data['user_service']
        if user_service.user != self.request.user:
            raise PermissionError("You can only create cookies for your own services")
        serializer.save()

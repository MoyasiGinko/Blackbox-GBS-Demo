from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.admin.models import LogEntry
from .models import (
    User, Subscription, Payment, Service, 
    UserService, Cookie, CookieInjectionLog
)
from .validators import clean_first_name, clean_last_name, password_validator

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=8, write_only=True)
    confirm_password = serializers.CharField(max_length=68, min_length=8, write_only=True)
    
    class Meta:
        model = User
        fields = (
            'email', 'full_name', 'password', 'confirm_password',
            'phone_number', 'subscription'
        )

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        password_validator(password)

        if password != confirm_password:
            raise serializers.ValidationError({'password': 'Passwords do not match'})

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=68, write_only=True)
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'password', 'tokens')

    def get_tokens(self, obj):
        user = User.objects.get(email=obj['email'])
        return user.tokens()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(email=email, password=password)
        
        if not user:
            raise AuthenticationFailed('Invalid credentials')
        if not user.is_active:
            raise AuthenticationFailed('Account is disabled')
        if not user.email_verified:
            raise AuthenticationFailed('Email not verified')

        return {
            'email': user.email,
            'tokens': user.tokens()
        }

class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            password_validator(password)
            
            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('Reset link is invalid or has expired')

            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            raise AuthenticationFailed('Reset link is invalid or has expired')

class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)
    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ['email', 'redirect_url']

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError('Token is invalid or expired')

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'name', 'price', 'duration_days', 'features', 'description']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'login_url', 'description', 'required_subscription']

class UserServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserService
        fields = ['id', 'service', 'credentials', 'is_active', 'created_at', 'last_used', 'usage_count']
        read_only_fields = ['created_at', 'last_used', 'usage_count']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_status', 'subscription', 'transaction_id', 'payment_method', 'billing_details']
        read_only_fields = ['timestamp']

class CookieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cookie
        fields = ['id', 'user_service', 'cookie_data', 'expires_at', 'status']
        read_only_fields = ['extracted_at', 'last_validated']

class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'

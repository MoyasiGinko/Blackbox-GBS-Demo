from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.admin.models import LogEntry
from .models import User, Company, Branch
from .validators import clean_first_name, clean_last_name, age_validator, password_validator


# class UserProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('id', 'email', 'first_name', 'last_name', 'age', 
#                  'address', 'profile_image', 'is_staff', 'is_active', 
#                  'is_verified', 'is_superuser')
#         read_only_fields = ('email', 'is_staff', 'is_active', 'is_verified', 'is_superuser')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=8, write_only=True)
    confirm_password = serializers.CharField(max_length=68, min_length=8, write_only=True)
    
    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name', 'company_code', 
            'branch_code', 'username', 'mobile', 'user_type', 
            'login_type','role_id', 'password', 'confirm_password'
        )

    def validate(self, attrs):
        first_name = attrs.get('first_name')
        last_name = attrs.get('last_name')
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        clean_first_name(first_name)
        clean_last_name(last_name)
        password_validator(password)

        if password != confirm_password:
            raise serializers.ValidationError({'password': 'Passwords do not match'})

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
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
        if not user.is_verified:
            raise AuthenticationFailed('Email is not verified')

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

            password_validator(password)  # Validate password
            
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

class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'

class CompanySerializer(serializers.ModelSerializer):
  class Meta:
    model = Company
    fields = ['company_name', 'company_code', 'company_type', 'head_office', 'longitude', 'latitude']
    read_only_fields = ['created_by', 'updated_by', 'deleted_by', 'deleted_date', 'created_date', 'updated_date', 'is_deleted']

class BranchSerializer(serializers.ModelSerializer):
  class Meta:
    model = Branch
    fields = ['branch_code', 'company_id', 'branch_name', 'address', 'longitude', 'latitude']
    read_only_fields = ['created_by', 'updated_by', 'deleted_by', 'deleted_date', 'created_date', 'updated_date', 'is_deleted']
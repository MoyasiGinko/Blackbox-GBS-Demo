from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Subscription, Payment, Service, 
    UserService, Cookie, CookieInjectionLog, LoginAttempt
)
from django.urls import path
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
import os
from .utils import send_email

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'is_active', 'is_staff', 'subscription', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_admin', 'email_verified', 'two_factor_enabled')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone_number')}),
        ('Subscription', {'fields': ('subscription',)}),
        ('Security', {'fields': ('email_verified', 'two_factor_enabled')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_admin', 'groups', 'user_permissions')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new and not obj.email_verified:
            verification_token = RefreshToken.for_user(obj).access_token
            verification_url = f"{os.environ.get('FRONTEND_BASE_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"
            send_email(
                subject="Verify your email",
                recipient_list=[obj.email],
                message=f"Please verify your email by clicking on the following link: {verification_url}"
            )

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_status', 'subscription', 'timestamp')
    list_filter = ('payment_status', 'timestamp')
    search_fields = ('user__email', 'transaction_id')
    readonly_fields = ('timestamp',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'login_url', 'is_active', 'required_subscription')
    list_filter = ('is_active', 'required_subscription')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserService)
class UserServiceAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'is_active', 'created_at', 'last_used', 'usage_count')
    list_filter = ('is_active', 'service')
    search_fields = ('user__email', 'service__name')
    readonly_fields = ('created_at', 'last_used', 'usage_count')

    def get_queryset(self, request):
        # Prevent exposure of encrypted credentials in list view
        return super().get_queryset(request).defer('_credentials')

@admin.register(Cookie)
class CookieAdmin(admin.ModelAdmin):
    list_display = ('user_service', 'status', 'extracted_at', 'expires_at', 'last_validated')
    list_filter = ('status', 'extracted_at')
    search_fields = ('user_service__user__email', 'user_service__service__name')
    readonly_fields = ('extracted_at', 'last_validated')

    def get_queryset(self, request):
        # Prevent exposure of encrypted cookie data in list view
        return super().get_queryset(request).defer('_cookie_data')

@admin.register(CookieInjectionLog)
class CookieInjectionLogAdmin(admin.ModelAdmin):
    list_display = ('cookie', 'injection_status', 'timestamp', 'ip_address')
    list_filter = ('injection_status', 'timestamp')
    search_fields = ('cookie__user_service__user__email', 'message')
    readonly_fields = ('timestamp',)

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'success', 'ip_address')
    list_filter = ('success', 'timestamp')
    search_fields = ('user__email', 'ip_address')
    readonly_fields = ('timestamp',)

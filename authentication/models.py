from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .manager import CustomUserManager
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
# Create your models here.

class User(AbstractBaseUser, PermissionsMixin):
    
    id = models.AutoField(primary_key=True)
    company_code = models.CharField(max_length=255, unique=True, null=True)
    branch_code = models.CharField(max_length=255, unique=True, null=True)
    username = models.CharField(max_length=255, unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    user_type = models.IntegerField(null=True)
    login_type = models.IntegerField(null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    role_id = models.IntegerField(null=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='created_users')
    last_update = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='updated_users')
    is_deleted = models.BooleanField(default=False)
    deleted_date = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='deleted_users')
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # Override groups and permissions with custom related_names
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username', 'mobile',]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

    def soft_delete(self, user):
        self.is_deleted = True
        self.deleted_date = timezone.now()
        self.deleted_by = user
        self.status = False
        self.save()

    class Meta:
        ordering = ['-created_date']
   
    
class Company(models.Model):
    company_name = models.CharField(max_length=255)
    company_code = models.CharField(max_length=255, unique=True)
    company_type = models.CharField(max_length=255)
    head_office = models.CharField(max_length=255)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
  
  # Base model fields
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='company_created_users')
    updated_date = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='company_updated_users')
    is_deleted = models.BooleanField(default=False)
    deleted_date = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='company_deleted_users')
    status = models.BooleanField(default=True)

    # Permission fields
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
  
    def __str__(self):
        return self.company_name


class Branch(models.Model):
    branch_code = models.CharField(max_length=255, unique=True)
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    company_name= models.CharField(max_length=255)
    branch_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    
    # Base model fields
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="branch_created_users")
    updated_date = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='branch_updated_users')
    is_deleted = models.BooleanField(default=False)
    deleted_date = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='branch_deleted_users')
    status = models.BooleanField(default=True)
    
    # Permission fields
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.company.company_name} - {self.branch_name}"
    
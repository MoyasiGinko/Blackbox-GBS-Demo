from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .manager import CustomUserManager
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
# Create your models here.


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="%(class)s_created_by"
    )
    last_update = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="%(class)s_updated_by"
    )
    is_deleted = models.BooleanField(default=False)
    deleted_date = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL, related_name="%(class)s_deleted_by"
    )
    status = models.BooleanField(default=True)

    class Meta:
        abstract = True

class BasePermission(models.Model):
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        abstract = True

class Company(BaseModel):
    company_name = models.CharField(max_length=255)
    company_code = models.CharField(max_length=255, unique=True)
    company_type = models.CharField(max_length=255)
    head_office = models.CharField(max_length=255)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    def __str__(self):
        return self.company_name

class Branch(BaseModel):
    branch_code = models.CharField(max_length=255, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    branch_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    def __str__(self):
        return f"{self.company.company_name} - {self.branch_name}"

class User(AbstractBaseUser, BaseModel, BasePermission, PermissionsMixin):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users', null=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='users', null=True)
    username = models.CharField(max_length=255, unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    login_type = models.ForeignKey('LoginType', on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    role_id = models.IntegerField(null=True)
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
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username', 'mobile']

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
   

class LoginType(BaseModel):
    login_type = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.login_type
    
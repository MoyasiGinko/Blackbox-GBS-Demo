import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .manager import CustomUserManager
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from cryptography.fernet import Fernet

def get_encryption_key():
    """Get or create encryption key for sensitive data"""
    return Fernet(settings.ENCRYPTION_KEY.encode())

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    subscription = models.ForeignKey(
        'Subscription', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='users'
    )
    last_login = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email

    def has_subscription(self):
        """Check if user has an active subscription"""
        if not self.subscription:
            return False
        latest_payment = self.payments.filter(
            payment_status='success'
        ).order_by('-timestamp').first()
        if not latest_payment:
            return False
        expiry_date = latest_payment.timestamp + timezone.timedelta(
            days=self.subscription.duration_days
        )
        return timezone.now() <= expiry_date

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    price = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    duration_days = models.IntegerField(validators=[MinValueValidator(1)])
    features = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (${self.price} for {self.duration_days} days)"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    subscription = models.ForeignKey(
        Subscription, 
        on_delete=models.CASCADE,
        related_name='payments'
    )
    transaction_id = models.CharField(max_length=255, unique=True)
    payment_method = models.CharField(max_length=50)
    billing_details = models.JSONField(default=dict)
    refund_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} - {self.payment_status}"

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    login_url = models.URLField()
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    required_subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        related_name='services'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='user_services'
    )
    service = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE,
        related_name='user_services'
    )
    _credentials = models.TextField()  # Encrypted credentials
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True)
    usage_count = models.IntegerField(default=0)

    @property
    def credentials(self):
        """Decrypt credentials before returning"""
        if not self._credentials:
            return {}
        fernet = get_encryption_key()
        decrypted = fernet.decrypt(self._credentials.encode())
        return eval(decrypted.decode())

    @credentials.setter
    def credentials(self, value):
        """Encrypt credentials before saving"""
        if not value:
            self._credentials = ''
            return
        fernet = get_encryption_key()
        encrypted = fernet.encrypt(str(value).encode())
        self._credentials = encrypted.decode()

    def __str__(self):
        return f"{self.user.email} - {self.service.name}"

class Cookie(models.Model):
    COOKIE_STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_service = models.ForeignKey(
        UserService, 
        on_delete=models.CASCADE,
        related_name='cookies'
    )
    _cookie_data = models.TextField()  # Encrypted cookie data
    extracted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=COOKIE_STATUS_CHOICES,
        default='valid'
    )
    last_validated = models.DateTimeField(auto_now=True)
    validation_errors = models.TextField(blank=True)

    @property
    def cookie_data(self):
        """Decrypt cookie data before returning"""
        if not self._cookie_data:
            return {}
        fernet = get_encryption_key()
        decrypted = fernet.decrypt(self._cookie_data.encode())
        return eval(decrypted.decode())

    @cookie_data.setter
    def cookie_data(self, value):
        """Encrypt cookie data before saving"""
        if not value:
            self._cookie_data = ''
            return
        fernet = get_encryption_key()
        encrypted = fernet.encrypt(str(value).encode())
        self._cookie_data = encrypted.decode()

    def __str__(self):
        return f"{self.user_service.service.name} cookie for {self.user_service.user.email}"

    def is_valid(self):
        return (
            self.status == 'valid' and 
            timezone.now() <= self.expires_at
        )

class CookieInjectionLog(models.Model):
    INJECTION_STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cookie = models.ForeignKey(
        Cookie, 
        on_delete=models.CASCADE,
        related_name='injection_logs'
    )
    injection_status = models.CharField(
        max_length=20, 
        choices=INJECTION_STATUS_CHOICES
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    request_data = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.cookie.user_service.service.name} injection - {self.injection_status}"

class LoginAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='login_attempts'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location_data = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user.email} - {'Success' if self.success else 'Failure'}"

from django.core.exceptions import ValidationError
from .models import *
from django.core.validators import RegexValidator

def clean_first_name(first_name):
    if not len(first_name) > 3:
        raise ValidationError(
            {"first_name": "First name must be at least 3 characters long"}
        )
    return first_name

def clean_last_name(last_name):
    if not len(last_name) > 3:
        raise ValidationError(
            {"last_name": "Last name must be at least 3 characters long"}
        )
    return last_name

def age_validator(age):
    if age and int(age) < 18:
        raise ValidationError(
            {"age": "Age must be at least 18 years"}
        )
    return age

def password_validator(password):
    if len(password) < 8:
        raise ValidationError(
            {"password": "Password must be at least 8 characters long"}
        )
    if not any(char.isdigit() for char in password):
        raise ValidationError(
            {"password": "Password must contain at least one number"}
        )
    if not any(char.isupper() for char in password):
        raise ValidationError(
            {"password": "Password must contain at least one uppercase letter"}
        )
    return password

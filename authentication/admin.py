from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UserCreationForm, UserChangeForm
from .models import User, Company, Branch, LoginType


class UserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ('email', 'mobile', 'is_staff', 'is_active', 'login_type', 'is_verified','is_superuser')
    list_filter = ('email', 'is_active','is_staff', 'is_verified', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'mobile', 'company', 'branch', 'login_type')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_verified', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2','is_staff', 'is_active', 'is_verifid', 'is_superuser')}
         ),
    )
    search_fields = ('email',)
    ordering = ('email',)

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_code', 'company_type', 'head_office', 'longitude', 'latitude')
    search_fields = ('company_name', 'company_code')
    list_filter = ('company_type',)
    ordering = ('company_name',)
    
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_code', 'company_id',  'branch_name', 'address', 'longitude', 'latitude')
    search_fields = ('branch_code', 'branch_name')
    list_filter = ('company_id',)
    ordering = ('branch_code',)

class LoginTypeAdmin(admin.ModelAdmin):
    list_display = ('login_type',)
    search_fields = ('login_type',)
    ordering = ('login_type',)

admin.site.register(Company, CompanyAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(LoginType, LoginTypeAdmin)
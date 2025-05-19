from django.urls import path

# from main.models import HospitalPackage
from . import views
from rest_framework import routers, viewsets
from rest_framework.routers import DefaultRouter

from django.conf.urls import include
from rest_framework_simplejwt.views import (
    TokenVerifyView
)

router = DefaultRouter()
router.register(r'users', views.AuthorityRegisterViewSet, basename='users')
router.register(r'company', views.CompanyViewSet, basename='company')
router.register(r'branch', views.BranchViewSet, basename='branch')

authentication =[
    path('', include(router.urls)),
    path('login/', views.LoginAPIView.as_view(), name="login"),
    # path('profile/', views.UserProfileAPIView.as_view(), name="profile"),
    path('email-verify/', views.VerifyEmail.as_view(), name="email-verify"),
    path('token/verify/',TokenVerifyView.as_view(),name="token_verify"),
    path('request-reset-email/',views.RequestPasswordResetEmail.as_view(),name="request-reset-email"),
    path('password-reset/<uidb64>/<token>/', views.PasswordTokenCheckApi.as_view(),name="password-reset-confirm"),
    path('password-reset-complete',views.SetNewPasswordAPIView.as_view(),name="password-reset-complete"),
    path('logout/', views.LogoutAPIView.as_view(), name="logout"),
    path('check_company_code/', views.CheckCompanyCode.as_view(), name="check_company_code"),
    path('get_branches_by_company/', views.GetBranchesByCompany.as_view(), name="get_branches_by_company"),
]

urlpatterns  = authentication
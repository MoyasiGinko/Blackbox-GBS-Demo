from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenVerifyView
from . import views

router = DefaultRouter()
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscription')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'user-services', views.UserServiceViewSet, basename='user-service')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'cookies', views.CookieViewSet, basename='cookie')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.RegisterView.as_view(), name="register"),
    path('login/', views.LoginView.as_view(), name="login"),
    path('email-verify/', views.VerifyEmail.as_view(), name="email-verify"),
    path('token/verify/', TokenVerifyView.as_view(), name="token_verify"),
    path('request-reset-email/', views.RequestPasswordResetEmail.as_view(), name="request-reset-email"),
    path('password-reset/<uidb64>/<token>/', views.PasswordTokenCheckApi.as_view(), name="password-reset-confirm"),
    path('password-reset-complete/', views.SetNewPasswordAPIView.as_view(), name="password-reset-complete"),
    path('logout/', views.LogoutAPIView.as_view(), name="logout"),
]

from django.shortcuts import render
from django.http.response import HttpResponsePermanentRedirect
from django.shortcuts import redirect

from django.utils.encoding import smart_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from drf_yasg import openapi
from django.conf import settings
from django.utils import timezone
import jwt
import os
from .utils import Util
from .models import User, Company, Branch
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import HttpResponseRedirect
from .serializers import (
    UserCreateSerializer, LoginSerializer, EmailVerificationSerializer,
    ResetPasswordEmailRequestSerializer, SetNewPasswordSerializer,
    LogoutSerializer, CompanySerializer, BranchSerializer
)


class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = [os.environ.get('APP_SCHEMA'), 'http', 'https']

class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    token_param_config = openapi.Parameter(
        'token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.is_active = True
                user.save()
            return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Activation link expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        email = request.data.get('email','')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request=request).domain
            relativeLink = reverse('password-reset-confirm', kwargs={"uidb64":uidb64, "token":token})
            redirect_url = request.data.get('redirect_url','')
            absurl = 'http://'+current_site + relativeLink
            email_body = "Hello, \n Use link below to reset your password \n" + \
                absurl + "?redirect_url="+redirect_url
            data = {
                'email_body':email_body, 'to_email':email, 'email_subject':'Reset Your Password'
            }
            Util.send_email(data)
        return Response({'success':'We have sent you a link to reset your password'}, status = status.HTTP_200_OK)

class PasswordTokenCheckApi(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):
        redirect_url = request.GET.get('redirect_url','')
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if PasswordResetTokenGenerator().check_token(user, token):
                if len(redirect_url) > 3:
                    return CustomRedirect(redirect_url+'?token_valid=False')
                else:
                    return CustomRedirect(os.environ.get('FRONTEND_URL','')+'?token_valid=False')
            
            if redirect_url and len(redirect_url) > 3:
                return CustomRedirect(redirect_url+'?token_valid=True&message=Credentials Valid&uidb64='+uidb64+'&token='+token)
            else:
                return CustomRedirect(os.environ.get('FRONTEND_URL','')+'?token_valid=False')
        except DjangoUnicodeDecodeError as identifier:
            try:
                if not PasswordResetTokenGenerator().check_token(user):
                    return CustomRedirect(redirect_url+'?token_valid=False')
            except UnboundLocalError as e:
                return Response({'error':'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)

class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success':True, 'message':'Password Reset Successful'}, status=status.HTTP_200_OK)

class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

# class UserProfileAPIView(generics.GenericAPIView):
#     permission_classes = (permissions.IsAuthenticated,)
#     serializer_class = UserProfileSerializer

#     def get(self, request):
#         serializer = self.serializer_class(request.user)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# class ActivityLogs(generics.ListAPIView):
#     queryset = LogEntry.objects.all()
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = LogEntrySerializer



class AuthorityRegisterViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_deleted=False).order_by('-created_date')
    serializer_class = UserCreateSerializer
    authentication_classes = [JWTAuthentication] 
    
    def get_permissions(self):
        if self.action in ['create', 'list']:
            permission_classes = [AllowAny]
        else: 
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print('serializer : ', serializer.validated_data)
        company = serializer.validated_data['company']
        branch = serializer.validated_data['branch']
        print('company Name : ', company.company_name)
        print('branch Name : ', branch.branch_name)
        
        if not Company.objects.filter(company_name=company.company_name).exists():
            return Response({'error': 'Company does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not Branch.objects.filter(branch_name=branch.branch_name).exists():
            return Response({'error': 'Branch does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not Branch.objects.filter(company=company, branch_name=branch.branch_name).exists():
            return Response({'error': 'Branch does not exist in the specified company'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        token = RefreshToken.for_user(user).access_token
        # Send verification email
        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')
        abs_url = f'http://{current_site}{relative_link}?token={str(token)}'
        email_body = f'Hi {user.first_name}, Use this link to verify your email:\n{abs_url}'
        
        data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Verify your email'
        }
        # Util.send_email(data)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {'email': user.email, 'message': "Successfully registered. Please verify your email"},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
        
    def perform_update(self, serializer):
        # serializer.save(updated_by=self.request.user)
        serializer.save()
    
    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_date = timezone.now()
        # instance.deleted_by = self.request.user
        instance.save()

class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email =serializer.data['email']
        tokens = serializer.data['tokens']

        errors = serializer.errors
        first_error = None
        for field, error_list in errors.items():
            first_error = error_list[0].__str__()
            print('first_error : ', first_error)
            break
        
        user = User.objects.get(email=email)
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not user.login_type:
            return Response({'error': 'User must have a valid login type'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.company:
            return Response({'error': 'User must have a valid company'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.branch:
            return Response({'error': 'User must have a valid branch'}, status=status.HTTP_400_BAD_REQUEST)
    
        # if not user.role_id:
        #     return Response({'error': 'User must have a valid role'}, status=status.HTTP_400_BAD_REQUEST)
        
        login_type = user.login_type.login_type
        if login_type == 'fmc':
            return redirect(f'/api/fmc/login?email={email}&tokens={tokens}')
        elif login_type == 'erp':
            return redirect(f'/api/erp/login?email={email}&tokens={tokens}')
        elif login_type == 'vendor':
            return redirect(f'/api/vendor/login?email={email}&tokens={tokens}')
        elif login_type == 'customer':
            return redirect(f'/api/customer/login?email={email}&tokens={tokens}')
        else:
            return Response({'error': 'Invalid login type. User Must have a valid login type'}, status=status.HTTP_400_BAD_REQUEST)

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.filter(is_deleted=False).order_by('-created_date')
    serializer_class = CompanySerializer
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.action in ['create', 'list']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
        serializer.save()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_by = self.request.user
        instance.deleted_date = timezone.now()
        instance.save()

class BranchViewSet(viewsets.ModelViewSet): 
    queryset = Branch.objects.filter(is_deleted=False).order_by('-created_date')
    serializer_class = BranchSerializer
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.action in ['create', 'list']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
        serializer.save()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_by = self.request.user
        instance.deleted_date = timezone.now()
        instance.save()
        
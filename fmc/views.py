from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from authentication.models import User

class LoginView(APIView):
  def get(self, request):
    username = request.GET.get('username')
    tokens = request.GET.get('tokens')
    user = User.objects.get(username=username)
    if not user:
      return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    print('the user is', user)
    data = {
      'Message': "Hello From FMC Module",
      'email': user.email,
      'first_name': user.first_name,
      'last_name': user.last_name,
      'mobile': user.mobile,
      'username': user.username,
      'company': user.company.company_name,
      'branch': user.branch.branch_name,
      'role_id': user.role_id,
      'is_superuser': user.is_superuser,
      'is_staff': user.is_staff,
      'is_verified': user.is_verified,
      'is_active': user.is_active,
      'login_type': user.login_type.login_type,
      'token': tokens
    }
    return Response(data, status=status.HTTP_200_OK)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from authentication.models import User

class LoginView(APIView):
  def get(self, request):
    email = request.GET.get('email')
    tokens = request.GET.get('tokens')
    user = User.objects.get(email=email)
    if not user:
      return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    print('the user is', user)
    data = {
      'login_type': user.login_type.login_type,
      'token': tokens
    }
    return Response(data, status=status.HTTP_200_OK)
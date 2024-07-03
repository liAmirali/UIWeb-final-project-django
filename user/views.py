from django.shortcuts import render
from rest_framework import generics, views
from rest_framework import permissions, status
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenVerifyView
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from .serializers import SignUpSerializer
from .tokens import email_verification_token

User = get_user_model()


class SignUpUserView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = [permissions.AllowAny]


class ActivateUserView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user.is_email_verified:
            return Response({'message': "Email is already verified."}, status=status.HTTP_400_BAD_REQUEST)
        elif user is not None and email_verification_token.check_token(user, token):
            user.is_active = True
            user.is_email_verified = True
            user.save()
            return Response({'message': 'Thank you for your email confirmation. Now you can log in.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Activation link is invalid!'}, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenVerifyView(TokenVerifyView):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            # Token is valid, retrieve user info
            token = UntypedToken(request.data['token'])
            user_id = token.payload.get('user_id')
            user = User.objects.get(id=user_id)

            # Add user data to the response
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
            return Response({'token_valid': True, 'user': user_data}, status=status.HTTP_200_OK)

        except TokenError as e:
            raise InvalidToken(e.args[0])

        except User.DoesNotExist:
            return Response({'error': 'Token is invalid.'}, status=status.HTTP_401_UNAUTHORIZED)

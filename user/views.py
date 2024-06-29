from rest_framework import generics, views
from rest_framework import permissions, status
from rest_framework.response import Response

from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from django.core.mail import send_mail

from django.conf import settings

from .serializers import SignUpSerializer
from .tokens import email_verification_token

User = get_user_model()


class SignUpUserView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    model = User
    permission_classes = [
        permissions.AllowAny  # Or anon users can't register
    ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'message': 'Please confirm your email address to complete the registration'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

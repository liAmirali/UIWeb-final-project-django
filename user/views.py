from rest_framework import generics
from rest_framework import permissions

from django.contrib.auth import get_user_model

from .serializers import SignUpSerializer

User = get_user_model()


class SignUpUserView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    model = User
    permission_classes = [
        permissions.AllowAny  # Or anon users can't register
    ]

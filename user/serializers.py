import re
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name',
                  'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
        }

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate_username(self, value):
        if len(value) < 4:
            raise serializers.ValidationError(
                'Username must be at least 4 characters long.')
        if not re.match("^[a-zA-Z]*$", value):
            raise serializers.ValidationError(
                'Username must only contain alphabets.')
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                'A user with that username already exists.')

        return value

    def validate(self, attrs):
        self.validate_password(attrs.get('password'))
        self.validate_username(attrs.get('username'))
        return super().validate(attrs)

    def create(self, validated_data):
        user = User(
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name',
                  'username', 'email',]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        username_or_email = attrs.get('username')
        password = attrs.get('password')

        # Check if the username_or_email is an email
        if '@' in username_or_email:
            user = authenticate(request=self.context.get(
                'request'), email=username_or_email, password=password)
        else:
            user = authenticate(request=self.context.get(
                'request'), username=username_or_email, password=password)

        if user is not None and user.is_active and user.is_email_verified:
            data = {}
            refresh = self.get_token(user)

            data['refresh'] = str(refresh)
            data['access'] = str(refresh.access_token)

            if self.context.get('request'):
                update_last_login(None, user)

            data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }

            return data
        else:
            raise serializers.ValidationError(
                'No active account found with the given credentials')

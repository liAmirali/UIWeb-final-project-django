from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        if (username is None and email is None) or password is None:
            raise ValueError('You must provide both username/email and password.')
        if username is not None and email is not None:
            raise ValueError('You must provide only one of username and email.')
        

        try:
            if email is not None:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

from django.contrib.auth.models import AbstractUser
from django.db import models


class AppUser(AbstractUser):
    # Making email field unique
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)

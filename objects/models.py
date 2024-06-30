from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AppObject(models.Model):
    object_key = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User, related_name='objects', on_delete=models.SET_NULL, null=True)
    shared_with = models.ManyToManyField(User, related_name='shared_objects')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

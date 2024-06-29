from django.db import models


class AppObject(models.Model):
    name = models.CharField(max_length=100)
    object_key = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        'auth.User', related_name='objects', on_delete=models.SET_NULL, null=True)
    shared_with = models.ManyToManyField('auth.User', related_name='shared_objects')

    def __str__(self):
        return self.name

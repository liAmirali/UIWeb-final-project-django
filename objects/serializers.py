from rest_framework import serializers
from .models import AppObject

from django.contrib.auth import get_user_model

User = get_user_model()


class AppObjectSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = AppObject
        fields = ['object_key', 'name', 'owner',
                  'shared_with', 'uploaded_at', 'is_owner', 'size', 'mime_type', 'file_type']

    def get_is_owner(self, obj):
        request = self.context.get('request', None)
        if request:
            return obj.owner == request.user
        return False


class AccessUpdateSerializer(serializers.Serializer):
    shared_with = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True)

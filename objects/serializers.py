from rest_framework import serializers
from .models import AppObject

class AppObjectSerializer(serializers.ModelSerializer):
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = AppObject
        fields = ['object_key', 'name', 'owner', 'shared_with', 'uploaded_at', 'is_owner']

    def get_is_owner(self, obj):
        request = self.context.get('request', None)
        if request:
            return obj.owner == request.user
        return False

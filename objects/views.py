import boto3
from botocore.exceptions import ClientError

from uuid import uuid4

from django.conf import settings

from .models import AppObject
from .serializers import AppObjectSerializer, AccessUpdateSerializer

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied


def get_s3_resource():
    try:
        return boto3.resource(
            's3',
            endpoint_url=settings.ARVAN_ENDPOINT,
            aws_access_key_id=settings.ARVAN_ACCESS_KEY,
            aws_secret_access_key=settings.ARVAN_SECRET_KEY
        )

    except Exception as exc:
        raise exc


class UploadObjectView(APIView):
    parser_classes = (MultiPartParser, )
    permission_classes = [IsAuthenticated]

    def put(self, request):
        print("request.user", request.user)
        s3_resource = get_s3_resource()
        try:
            bucket = s3_resource.Bucket('djangowebstorage')
            in_memory_file = request.FILES.get('object', None)

            if in_memory_file is None:
                return Response({"message": "No file found."}, status=status.HTTP_400_BAD_REQUEST)

            print("in_memory_file", type(in_memory_file))

            object_instance = AppObject(object_key=str(uuid4()),
                                        name=in_memory_file.name,
                                        owner=request.user)
            object_instance.save()

            bucket.put_object(
                ACL='private',
                Body=in_memory_file,
                Key=object_instance.object_key
            )

        except ClientError as e:
            raise e

        return Response({"message": "Object uploaded successfully."}, status=status.HTTP_201_CREATED)


class ObjectListView(generics.ListAPIView):
    class ObjectListPagination(PageNumberPagination):
        page_size = 2
        page_size_query_param = 'page_size'

    serializer_class = AppObjectSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ObjectListPagination

    def get_queryset(self):
        user = self.request.user
        owned_objects = AppObject.objects.filter(owner=user)
        shared_objects = AppObject.objects.filter(shared_with=user)
        return (owned_objects | shared_objects).order_by('-uploaded_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class DeleteObject(APIView):
    def delete(self, request):
        s3_resource = get_s3_resource()
        try:
            bucket_name = 'djangowebstorage'
            bucket = s3_resource.Bucket(bucket_name)

            object_name = "file.txt"
            object = bucket.Object(object_name)
            print(object)

            response = object.delete()

            return Response("DONE!")

        except ClientError as e:
            raise e


class AccessUpdateView(generics.UpdateAPIView):
    serializer_class = AccessUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def check_object_permissions(self, request, obj):
        # Check if the user is the owner of the object
        if not obj.owner == request.user:
            raise PermissionDenied("You do not have permission to modify this object's access.")

    def put(self, request, *args, **kwargs):
        object_key = request.data['object_key']
        instance = AppObject.objects.get(object_key=object_key)
        self.check_object_permissions(request, instance)  # Ensure user is owner
        serializer = self.get_serializer(instance, data=request.data)

        if serializer.is_valid():
            # Update shared_with field
            print(serializer.validated_data['shared_with'])
            instance.shared_with.set(serializer.validated_data['shared_with'])
            print("instance.shared_with", instance.shared_with)
            instance.save()
            return Response({"message": "Access updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

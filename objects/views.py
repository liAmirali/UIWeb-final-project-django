import boto3
from botocore.exceptions import ClientError

from uuid import uuid4
import os
import tempfile
import mimetypes

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.core.mail import send_mail

from .models import AppObject
from .serializers import AppObjectSerializer, AccessUpdateSerializer

from user.serializers import UserSerializer

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


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

            # Get the MIME type
            mime_type, _ = mimetypes.guess_type(in_memory_file.name)
            if mime_type is None:
                mime_type = 'application/octet-stream'  # Default MIME type if not detected

            # Determine file type based on MIME type or file extension
            file_extension = in_memory_file.name.split('.')[-1].lower()
            if mime_type.startswith('audio/'):
                file_type = 'music'
            elif mime_type == 'application/pdf':
                file_type = 'pdf'
            elif mime_type.startswith('video/'):
                file_type = 'video'
            elif mime_type.startswith('image/') or file_extension in ['png', 'jpeg', 'jpg']:
                file_type = 'image'
            else:
                file_type = 'others'

            object_instance = AppObject(object_key=str(uuid4()),
                                        name=in_memory_file.name,
                                        owner=request.user,
                                        size=in_memory_file.size,
                                        mime_type=mime_type,
                                        file_type=file_type
                                        )
            object_instance.save()

            bucket.put_object(
                ACL='private',
                Body=in_memory_file,
                Key=object_instance.object_key
            )

        except ClientError as e:
            raise e

        return Response({"message": "Object uploaded successfully."}, status=status.HTTP_201_CREATED)


class DownloadObjectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        object_key = request.query_params.get('object_key')

        if not object_key:
            return Response({"error": "Object key not provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the object from the database
            app_object = AppObject.objects.get(object_key=object_key)
        except AppObject.DoesNotExist:
            return Response({"error": "Object not found in the database."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has access to the object
        if request.user != app_object.owner and request.user not in app_object.shared_with.all():
            return Response({"error": "You do not have permission to access this object."}, status=status.HTTP_403_FORBIDDEN)

        s3_resource = get_s3_resource()
        try:
            # Temporary file path to store the downloaded object
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            download_path = app_object.name

            # Download the file from the S3 bucket
            bucket = s3_resource.Bucket('djangowebstorage')
            bucket.download_file(object_key, download_path)

            # Return the file as a response
            temp_file.seek(0)
            response = FileResponse(open(
                download_path, 'rb'), as_attachment=True, filename=os.path.basename(app_object.name))

            # Cleanup the temporary file
            os.remove(download_path)
            return response

        except ClientError as e:
            print(e)
            return Response({"error": "Failed to download object."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        return (owned_objects | shared_objects).distinct().order_by('-uploaded_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class DeleteObject(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        object_key = request.data.get('object_key')

        if not object_key:
            return Response({"error": "Object key not provided."}, status=status.HTTP_400_BAD_REQUEST)
    

        s3_resource = get_s3_resource()
        try:
            app_object = AppObject.objects.get(object_key=object_key)
            if app_object.owner != request.user:
                return Response({"error": "You do not have permission to access this object."}, status=status.HTTP_403_FORBIDDEN)

            # Delete from the bucket
            bucket_name = 'djangowebstorage'
            bucket = s3_resource.Bucket(bucket_name)
            s3_object = bucket.Object(object_key)
            s3_object.delete()

            # Delete from the database
            app_object.delete()

            return Response({"message": "Object deleted successfully."}, status=status.HTTP_200_OK)

        except AppObject.DoesNotExist:
            return Response({"error": "Object not found in the database."}, status=status.HTTP_404_NOT_FOUND)
        except ClientError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccessUpdateView(generics.UpdateAPIView):
    serializer_class = AccessUpdateSerializer
    permission_classes = [IsAuthenticated]

    def check_object_permissions(self, request, obj):
        # Check if the user is the owner of the object
        if not obj.owner == request.user:
            raise PermissionDenied(
                "You do not have permission to modify this object's access.")

    def put(self, request, *args, **kwargs):
        object_key = request.data['object_key']
        instance = AppObject.objects.get(object_key=object_key)
        self.check_object_permissions(
            request, instance)  # Ensure user is owner

        # Get the current set of users who have access
        old_shared_users = set(instance.shared_with.all())

        serializer = self.get_serializer(instance, data=request.data)

        if serializer.is_valid():
            # Update shared_with field
            instance.shared_with.set(serializer.validated_data['shared_with'])
            instance.save()

            # Get the new set of users who have access
            new_shared_users = set(instance.shared_with.all())
            
            # Determine newly added users
            newly_added_users = new_shared_users - old_shared_users

            # Send email to newly added users
            for user in newly_added_users:
                send_mail(
                    'File Shared with You',
                    'A file has been shared with you. Please check your account for access.',
                    'liamirali.lotfi@gmail.com',
                    [user.email],
                )

            return Response({"message": "Access updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsersAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        object_key = request.query_params.get('object_key')

        if not object_key:
            return Response({"error": "Object key not provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            app_object = AppObject.objects.get(object_key=object_key)
        except AppObject.DoesNotExist:
            return Response({"error": "Object not found in the database."}, status=status.HTTP_404_NOT_FOUND)

        users = User.objects.all()
        response_data = []

        for user in users:
            user_data = UserSerializer(user).data
            user_data['has_access'] = user in app_object.shared_with.all()
            user_data['is_owner'] = user == app_object.owner
            response_data.append(user_data)

        return Response(response_data, status=status.HTTP_200_OK)

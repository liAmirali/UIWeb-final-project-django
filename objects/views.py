import boto3
from botocore.exceptions import ClientError

from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser


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

    def put(self, request):
        s3_resource = get_s3_resource()
        try:
            bucket = s3_resource.Bucket('djangowebstorage')
            in_memory_file = request.FILES.get('object', None)

            if in_memory_file is None:
                return Response({"message": "No file found."}, status=status.HTTP_400_BAD_REQUEST)

            print("in_memory_file", type(in_memory_file))

            bucket.put_object(
                ACL='private',
                Body=in_memory_file,
                Key=in_memory_file.name
                
            )
        except ClientError as e:
            raise e

        return Response({"message": "Object uploaded successfully."}, status=status.HTTP_201_CREATED)


class ListObjects(APIView):
    def get(self, request):
        s3_resource = get_s3_resource()

        try:
            bucket_name = 'djangowebstorage'
            bucket = s3_resource.Bucket(bucket_name)

            for obj in bucket.objects.all():
                print(f"object_name: {obj.key}, last_modified: {
                        obj.last_modified}")

            return Response("DONE!")

        except ClientError as e:
            raise e


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

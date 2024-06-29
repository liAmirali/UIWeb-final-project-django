import logging
import boto3
from botocore.exceptions import ClientError

from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class UploadObjectView(APIView):
    def post(self, request):
        try:
            s3_resource = boto3.resource(
                's3',
                endpoint_url=settings.ARVAN_ENDPOINT,
                aws_access_key_id=settings.ARVAN_ACCESS_KEY,
                aws_secret_access_key=settings.ARVAN_SECRET_KEY
            )

        except Exception as exc:
            raise exc
        else:
            try:
                bucket = s3_resource.Bucket('djangowebstorage')
                file_path = './test.txt'
                object_name = 'file.txt'

                with open(file_path, "rb") as file:
                    bucket.put_object(
                        ACL='private',
                        Body=file,
                        Key=object_name
                    )
            except ClientError as e:
                raise e
        return Response({"message": "Object uploaded successfully."}, status=status.HTTP_201_CREATED)


class ListObjects(APIView):
    def get(self, request):
        print(settings.ARVAN_ACCESS_KEY)
        print(settings.ARVAN_SECRET_KEY)
        print(settings.ARVAN_ENDPOINT)

        try:
            # S3 resource
            s3_resource = boto3.resource(
                's3',
                endpoint_url=settings.ARVAN_ENDPOINT,
                aws_access_key_id=settings.ARVAN_ACCESS_KEY,
                aws_secret_access_key=settings.ARVAN_SECRET_KEY
            )

        except Exception as exc:
            raise exc
        else:
            try:

                bucket_name = 'djangowebstorage'
                bucket = s3_resource.Bucket(bucket_name)

                for obj in bucket.objects.all():
                    print(f"object_name: {obj.key}, last_modified: {obj.last_modified}")

                return Response("DONE!")

            except ClientError as e:
                raise e


class DeleteObject(APIView):
    def delete(self, request):
        print(settings.ARVAN_ACCESS_KEY)
        print(settings.ARVAN_SECRET_KEY)
        print(settings.ARVAN_ENDPOINT)

        try:
            # S3 resource
            s3_resource = boto3.resource(
                's3',
                endpoint_url=settings.ARVAN_ENDPOINT,
                aws_access_key_id=settings.ARVAN_ACCESS_KEY,
                aws_secret_access_key=settings.ARVAN_SECRET_KEY
            )

        except Exception as exc:
            raise exc
        else:
            try:

                bucket_name = 'djangowebstorage'
                object_name = 'file.txt'

                bucket = s3_resource.Bucket('djangowebstorage')
                object = bucket.Object(object_name)

                response = object.delete()

                return Response("DONE!")

            except ClientError as e:
                raise e

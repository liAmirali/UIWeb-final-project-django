from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from unittest.mock import patch, MagicMock
import os

from .models import AppObject

User = get_user_model()


class UploadObjectViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email="test@test.com", password='testpass')
        self.client.force_authenticate(user=self.user)
        # Ensure the correct URL name is used
        self.url = reverse('upload-object')

    @patch('boto3.resource')
    def test_upload_object(self, mock_boto3_resource):
        mock_s3_resource = MagicMock()
        mock_boto3_resource.return_value = mock_s3_resource
        mock_bucket = MagicMock()
        mock_s3_resource.Bucket.return_value = mock_bucket

        with open('testfile.txt', 'w') as f:
            f.write('test content')
        with open('testfile.txt', 'rb') as f:
            response = self.client.put(self.url, {'object': f})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'],
                         "Object uploaded successfully.")


class DownloadObjectViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email="test@test.com", password='testpass')
        self.other_user = User.objects.create_user(
            username='otheruser', email="other@test.com", password='otherpass')
        self.shared_user = User.objects.create_user(
            username='shareduser', email="shared@test.com", password='sharedpass')

        self.app_object = AppObject.objects.create(
            object_key='test-key',
            name='testfile.txt',
            owner=self.user,
            size=100,
            mime_type='text/plain',
            file_type='others'
        )
        self.app_object.shared_with.add(self.shared_user)

        # Make sure to use the correct URL name
        self.url = reverse('download-object')

    def test_missing_object_key(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Object key not provided.")

    def test_object_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {'object_key': 'nonexistent-key'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'],
                         "Object not found in the database.")

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(
            self.url, {'object_key': self.app_object.object_key})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data['error'], "You do not have permission to access this object.")

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from unittest.mock import patch, MagicMock

from .models import AppObject

User = get_user_model()

class UploadObjectViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email="test@test.com", password='testpass')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('upload-object')  # Ensure the correct URL name is used

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
        self.assertEqual(response.data['message'], "Object uploaded successfully.")

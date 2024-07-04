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


class ObjectListViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', email='other@test.com', password='otherpass')
        self.app_object1 = AppObject.objects.create(
            object_key='test-key-1',
            name='testfile1.txt',
            owner=self.user,
            size=100,
            mime_type='text/plain',
            file_type='others'
        )
        self.app_object2 = AppObject.objects.create(
            object_key='test-key-2',
            name='testfile2.txt',
            owner=self.user,
            size=100,
            mime_type='text/plain',
            file_type='others'
        )
        self.app_object2.shared_with.add(self.other_user)
        # Ensure the correct URL name is used
        self.url = reverse('list-objects')

    def test_list_objects(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_objects_shared_with_user(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

class DeleteObjectViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', email='other@test.com', password='otherpass')
        self.shared_user = User.objects.create_user(username='shareduser', email='shared@test.com', password='sharedpass')
        self.app_object = AppObject.objects.create(
            object_key='test-key',
            name='testfile.txt',
            owner=self.user,
            size=100,
            mime_type='text/plain',
            file_type='others'
        )
        self.app_object.shared_with.add(self.shared_user)
        self.url = reverse('delete-object')  # Make sure to use the correct URL name

    def test_missing_object_key(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Object key not provided.")

    def test_object_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url, {'object_key': 'nonexistent-key'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Object not found in the database.")

    def test_unauthorized_access_no_access(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.url, {'object_key': self.app_object.object_key})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "You do not have permission to access this object.")

    def test_unauthorized_access_shared_user(self):
        self.client.force_authenticate(user=self.shared_user)
        response = self.client.delete(self.url, {'object_key': self.app_object.object_key})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "You do not have permission to access this object.")

    @patch('boto3.resource')
    def test_successful_delete_owner(self, mock_boto3_resource):
        self.client.force_authenticate(user=self.user)
        
        mock_s3_resource = MagicMock()
        mock_boto3_resource.return_value = mock_s3_resource
        mock_bucket = MagicMock()
        mock_s3_resource.Bucket.return_value = mock_bucket

        response = self.client.delete(self.url, {'object_key': self.app_object.object_key})

        mock_bucket.Object.return_value.delete.assert_called_once_with()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Object deleted successfully.")

    @patch('boto3.resource')
    def test_object_not_found_in_database(self, mock_boto3_resource):
        self.client.force_authenticate(user=self.user)
        
        AppObject.objects.filter(object_key=self.app_object.object_key).delete()

        mock_s3_resource = MagicMock()
        mock_boto3_resource.return_value = mock_s3_resource
        mock_bucket = MagicMock()
        mock_s3_resource.Bucket.return_value = mock_bucket

        response = self.client.delete(self.url, {'object_key': self.app_object.object_key})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Object not found in the database.")
class AccessUpdateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', email='other@test.com', password='otherpass')
        self.app_object = AppObject.objects.create(
            object_key='test-key',
            name='testfile.txt',
            owner=self.user,
            size=100,
            mime_type='text/plain',
            file_type='others'
        )
        self.url = reverse('update-access')

    @patch('django.core.mail.send_mail')
    def test_update_access(self, mock_send_mail):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.url, {
            'object_key': self.app_object.object_key,
            'shared_with': [self.other_user.id]
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Access updated successfully.")


class UsersAccessViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='testpass')
        self.other_user = User.objects.create_user(username='otheruser', email='other@test.com', password='otherpass')
        self.app_object = AppObject.objects.create(
            object_key='test-key',
            name='testfile.txt',
            owner=self.user,
            size=100,
            mime_type='text/plain',
            file_type='others'
        )
        self.app_object.shared_with.add(self.other_user)
        self.url = reverse('people-shared') 

    def test_users_access(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {'object_key': self.app_object.object_key})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for user_data in response.data:
            if user_data['username'] == 'testuser':
                self.assertTrue(user_data['is_owner'])
            else:
                self.assertFalse(user_data['is_owner'])
                self.assertTrue(user_data['has_access'])

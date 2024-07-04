from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class AppUserManagerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', username='testuser', password='testpass')
        self.superuser = User.objects.create_superuser(email='admin@example.com', username='admin', password='adminpass')

    def test_create_user(self):
        user = User.objects.get(email='testuser@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass'))

    def test_create_superuser(self):
        superuser = User.objects.get(email='admin@example.com')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_user_no_email(self):
        with self.assertRaises(Exception):
            User.objects.create_user(username='testuser', password='testpass')

    def test_create_user_no_username(self):
        with self.assertRaises(Exception):
            User.objects.create_user(email='testuser@example.com', password='testpass')

    def test_unique_email(self):
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email='testuser@example.com', username='testuser2', password='testpass2')

class AppUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', username='testuser', password='testpass')

    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser')

class SignUpSerializerTests(APITestCase):
    def setUp(self):
        self.url = reverse('sign-up')
        self.valid_payload = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testPass123#',
        }

    def test_valid_signup(self):
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

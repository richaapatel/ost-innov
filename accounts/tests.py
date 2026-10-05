from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class CustomUserTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            name='Test User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('testpassword123'))
        
        # Test username is not used/none
        with self.assertRaises(AttributeError):
            user.username

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='testpassword123',
            name='Admin User'
        )
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_email_normalization(self):
        user = User.objects.create_user(
            email='TEST@EXAMPLE.COM',
            password='testpassword123',
            name='Test User'
        )
        self.assertEqual(user.email, 'TEST@example.com')

    def test_email_unique(self):
        User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            name='Test User 1'
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='test@example.com',
                password='testpassword456',
                name='Test User 2'
            )

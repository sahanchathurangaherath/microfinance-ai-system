from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from .models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordRecoveryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='recovery-user',
            email='recovery@example.com',
            password='InitialPass123!',
            first_name='Recovery',
            last_name='User',
        )

    def test_forgot_password_sends_reset_email_for_existing_user(self):
        response = self.client.post('/api/auth/forgot-password/', {'email': 'recovery@example.com'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('recovery@example.com', mail.outbox[0].to)

    def test_reset_password_works_with_valid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post('/api/auth/reset-password/', {
            'uid': uid,
            'token': token,
            'new_password': 'NewStrongPass123!',
            'confirm_password': 'NewStrongPass123!',
        })

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass123!'))

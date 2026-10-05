from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import Client

from skills.models import Skill

from .utils import get_user_initials

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


class RegistrationTests(TestCase):
    valid_password = 'StrongPass9!'

    def registration_data(self, **overrides):
        data = {
            'name': 'Taylor Morgan',
            'email': 'taylor@example.com',
            'password1': self.valid_password,
            'password2': self.valid_password,
        }
        data.update(overrides)
        return data

    def post_registration(self, **overrides):
        return self.client.post(
            reverse('accounts:register'),
            self.registration_data(**overrides),
        )

    def test_valid_registration_succeeds_and_logs_user_in(self):
        response = self.post_registration()

        self.assertRedirects(response, reverse('core:home'))
        user = User.objects.get(email='taylor@example.com')
        self.assertEqual(user.name, 'Taylor Morgan')
        self.assertTrue(user.check_password(self.valid_password))
        self.assertNotEqual(user.password, self.valid_password)
        self.assertEqual(str(user.pk), self.client.session['_auth_user_id'])

    def test_authenticated_user_is_redirected_away_from_registration(self):
        user = User.objects.create_user(
            email='existing@example.com', password=self.valid_password, name='Existing User'
        )
        self.client.force_login(user)

        response = self.client.get(reverse('accounts:register'))

        self.assertRedirects(response, reverse('core:home'))

    def test_name_is_required_and_whitespace_is_rejected(self):
        response = self.post_registration(name='   ')

        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)

    def test_name_maximum_length_is_enforced(self):
        response = self.post_registration(name='a' * 81)

        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)

    def test_surrounding_name_whitespace_is_trimmed(self):
        response = self.post_registration(name='  Taylor Morgan  ')

        self.assertRedirects(response, reverse('core:home'))
        self.assertEqual(User.objects.get(email='taylor@example.com').name, 'Taylor Morgan')

    def test_invalid_email_is_rejected(self):
        response = self.post_registration(email='not-an-email')

        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)

    def test_email_is_normalized_to_lowercase(self):
        response = self.post_registration(email='TAYLOR@EXAMPLE.COM')

        self.assertRedirects(response, reverse('core:home'))
        self.assertTrue(User.objects.filter(email='taylor@example.com').exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            email='existing@example.com', password=self.valid_password, name='Existing User'
        )

        response = self.post_registration(email='EXISTING@EXAMPLE.COM')

        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertEqual(User.objects.filter(email__iexact='existing@example.com').count(), 1)

    def test_password_shorter_than_eight_characters_is_rejected(self):
        response = self.post_registration(password1='Ab1!xyz', password2='Ab1!xyz')

        self.assertEqual(response.status_code, 200)
        self.assertIn('password1', response.context['form'].errors)

    def test_password_longer_than_128_characters_is_rejected(self):
        password = 'A' * 123 + 'a1!xyz'
        response = self.post_registration(password1=password, password2=password)

        self.assertEqual(response.status_code, 200)
        self.assertIn('password1', response.context['form'].errors)

    def test_password_requires_uppercase(self):
        response = self.post_registration(password1='strongpass9!', password2='strongpass9!')

        self.assertIn('password1', response.context['form'].errors)

    def test_password_requires_lowercase(self):
        response = self.post_registration(password1='STRONGPASS9!', password2='STRONGPASS9!')

        self.assertIn('password1', response.context['form'].errors)

    def test_password_requires_number(self):
        response = self.post_registration(password1='StrongPass!', password2='StrongPass!')

        self.assertIn('password1', response.context['form'].errors)

    def test_password_requires_special_character(self):
        response = self.post_registration(password1='StrongPass9', password2='StrongPass9')

        self.assertIn('password1', response.context['form'].errors)

    def test_password_confirmation_must_match(self):
        response = self.post_registration(password2='DifferentPass9!')

        self.assertEqual(response.status_code, 200)
        self.assertIn('password2', response.context['form'].errors)


class LoginTests(TestCase):
    password = 'StrongPass9!'

    def setUp(self):
        self.user = User.objects.create_user(
            email='member@example.com', password=self.password, name='Member User'
        )

    def login_data(self, **overrides):
        data = {'username': 'member@example.com', 'password': self.password}
        data.update(overrides)
        return data

    def test_login_page_is_available_to_anonymous_users(self):
        response = self.client.get(reverse('accounts:login'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_valid_credentials_succeed_and_create_session(self):
        response = self.client.post(reverse('accounts:login'), self.login_data())

        self.assertRedirects(response, reverse('core:home'))
        self.assertEqual(str(self.user.pk), self.client.session['_auth_user_id'])

    def test_email_login_is_case_insensitive(self):
        response = self.client.post(
            reverse('accounts:login'),
            self.login_data(username='MEMBER@EXAMPLE.COM'),
        )

        self.assertRedirects(response, reverse('core:home'))

    def test_invalid_credentials_use_a_generic_error(self):
        response = self.client.post(
            reverse('accounts:login'),
            self.login_data(password='WrongPass9!'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_unknown_email_uses_a_generic_error(self):
        response = self.client.post(
            reverse('accounts:login'),
            self.login_data(username='unknown@example.com'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password.')

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save(update_fields=('is_active',))

        response = self.client.post(reverse('accounts:login'), self.login_data())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_authenticated_user_is_redirected_away_from_login(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('accounts:login'))

        self.assertRedirects(response, reverse('core:home'))

    def test_safe_next_url_is_used_after_login(self):
        response = self.client.post(
            reverse('accounts:login'),
            self.login_data(next=reverse('core:protected')),
        )

        self.assertRedirects(response, reverse('core:protected'))

    def test_external_next_url_is_not_used(self):
        response = self.client.post(
            reverse('accounts:login'),
            self.login_data(next='https://malicious.example/steal'),
        )

        self.assertRedirects(response, reverse('core:home'))


class LogoutAndProtectedRouteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='member@example.com', password='StrongPass9!', name='Member User'
        )

    def test_logout_uses_post_and_destroys_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('accounts:logout'))

        self.assertRedirects(response, reverse('core:home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_does_not_accept_get(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('accounts:logout'))

        self.assertEqual(response.status_code, 405)

    def test_anonymous_user_is_redirected_to_login_with_next(self):
        response = self.client.get(reverse('core:protected'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/protected/')

    def test_authenticated_user_can_access_protected_route(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('core:protected'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'authenticated'})


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='aryan@example.com',
            password='StrongPass9!',
            name='Aryan Patel',
            bio='I enjoy learning by teaching.',
        )
        self.client.force_login(self.user)

    def profile_data(self, **overrides):
        data = {
            'name': 'Aryan Patel',
            'bio': 'I enjoy learning by teaching.',
        }
        data.update(overrides)
        return data

    def test_initials_helper_supports_single_and_multiple_names(self):
        self.assertEqual(get_user_initials('Aryan Patel'), 'AP')
        self.assertEqual(get_user_initials('Aryan'), 'A')
        self.assertEqual(get_user_initials('John Michael Smith'), 'JS')

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()

        response = self.client.get(reverse('accounts:profile'))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
            fetch_redirect_response=False,
        )

    def test_authenticated_user_can_access_profile(self):
        response = self.client.get(reverse('accounts:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_profile_displays_current_user_information(self):
        response = self.client.get(reverse('accounts:profile'))

        self.assertContains(response, 'Aryan Patel')
        self.assertContains(response, 'aryan@example.com')
        self.assertContains(response, 'I enjoy learning by teaching.')
        self.assertContains(response, self.user.created_at.strftime('%B %Y'))
        self.assertNotContains(response, 'name="email"')
        self.assertNotContains(response, 'password')

    def test_offered_and_wanted_skills_are_displayed(self):
        python = Skill.objects.create(name='Python', category='Technology')
        guitar = Skill.objects.create(name='Guitar', category='Music')
        self.user.offered_skills.add(python)
        self.user.wanted_skills.add(guitar)

        response = self.client.get(reverse('accounts:profile'))

        self.assertContains(response, 'Python')
        self.assertContains(response, 'Guitar')

    def test_empty_skill_states_are_displayed(self):
        response = self.client.get(reverse('accounts:profile'))

        self.assertContains(response, "You haven't added any skills yet.")
        self.assertContains(response, "You haven't added any learning goals yet.")

    def test_valid_profile_update_changes_name_and_bio(self):
        response = self.client.post(
            reverse('accounts:profile'),
            self.profile_data(name='  Updated Name  ', bio='  A refreshed bio.  '),
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated Name')
        self.assertEqual(self.user.bio, 'A refreshed bio.')

    def test_successful_update_shows_message(self):
        response = self.client.post(
            reverse('accounts:profile'),
            self.profile_data(bio='A new bio.'),
            follow=True,
        )

        self.assertContains(response, 'Profile updated successfully.')

    def test_name_cannot_be_empty_or_whitespace(self):
        response = self.client.post(
            reverse('accounts:profile'),
            self.profile_data(name='   '),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)

    def test_name_cannot_exceed_80_characters(self):
        response = self.client.post(
            reverse('accounts:profile'),
            self.profile_data(name='a' * 81),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)

    def test_bio_cannot_exceed_500_characters(self):
        response = self.client.post(
            reverse('accounts:profile'),
            self.profile_data(bio='a' * 501),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('bio', response.context['form'].errors)

    def test_bio_can_be_cleared(self):
        response = self.client.post(
            reverse('accounts:profile'),
            self.profile_data(bio=''),
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, '')

    def test_email_is_not_changed_by_profile_update(self):
        response = self.client.post(
            reverse('accounts:profile'),
            self.profile_data(email='attacker@example.com', name='Still Aryan'),
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'aryan@example.com')

    def test_submitted_user_id_cannot_modify_another_user(self):
        other = User.objects.create_user(
            email='other@example.com', password='StrongPass9!', name='Other User', bio='Original bio'
        )

        response = self.client.post(
            reverse('accounts:profile'),
            self.profile_data(user_id=other.pk, name='Only My Profile', bio='Only my bio'),
        )

        self.assertRedirects(response, reverse('accounts:profile'))
        other.refresh_from_db()
        self.assertEqual(other.name, 'Other User')
        self.assertEqual(other.bio, 'Original bio')

    def test_profile_update_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(
            reverse('accounts:profile'),
            self.profile_data(name='Blocked Without CSRF'),
        )

        self.assertEqual(response.status_code, 403)

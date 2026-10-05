from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from .models import Skill
from .services import add_user_skill


User = get_user_model()


class SkillModelTests(TestCase):
    def test_skill_creation_and_string_representation(self):
        skill = Skill.objects.create(
            name=' Python ',
            description='Backend programming',
            category='Technology',
        )
        self.assertEqual(skill.name, 'Python')
        self.assertEqual(str(skill), 'Python')
        self.assertEqual(skill.normalized_name, 'python')

    def test_field_max_lengths_are_validated(self):
        skill = Skill(
            name='x' * 101,
            description='x' * 501,
            category='x' * 81,
        )
        with self.assertRaises(ValidationError):
            skill.full_clean()

    def test_optional_fields_default_to_empty_strings(self):
        skill = Skill.objects.create(name='Python')
        self.assertEqual(skill.description, '')
        self.assertEqual(skill.category, '')

    def test_case_insensitive_duplicate_name_is_rejected(self):
        Skill.objects.create(name='Python')
        with self.assertRaises((ValidationError, IntegrityError)):
            Skill.objects.create(name='python')

    def test_users_can_have_offered_and_wanted_skills(self):
        python = Skill.objects.create(name='Python')
        guitar = Skill.objects.create(name='Guitar')
        spanish = Skill.objects.create(name='Spanish')
        user = User.objects.create_user(email='one@example.com', password='pass12345', name='One')
        other = User.objects.create_user(email='two@example.com', password='pass12345', name='Two')

        user.offered_skills.add(python, guitar)
        user.wanted_skills.add(spanish)
        other.offered_skills.add(python)

        self.assertEqual(set(user.offered_skills.all()), {python, guitar})
        self.assertEqual(list(user.wanted_skills.all()), [spanish])
        self.assertEqual(list(python.teachers.all()), [user, other])


class SkillLibraryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='member@example.com', password='StrongPass9!', name='Member User'
        )
        self.python = Skill.objects.create(
            name='Python', category='Technology', description='Backend code and automation'
        )
        self.design = Skill.objects.create(
            name='Graphic Design', category='Design', description='Visual communication'
        )

    def test_skill_library_is_public(self):
        response = self.client.get(reverse('skills:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python')

    def test_search_matches_name_and_description_case_insensitively(self):
        response = self.client.get(reverse('skills:list'), {'search': 'PYTHON'})
        self.assertContains(response, 'Python')
        self.assertNotContains(response, 'Graphic Design')

        response = self.client.get(reverse('skills:list'), {'search': 'visual communication'})
        self.assertContains(response, 'Graphic Design')

    def test_category_filter_works(self):
        response = self.client.get(reverse('skills:list'), {'category': 'Technology'})
        self.assertContains(response, 'Python')
        self.assertNotContains(response, 'Graphic Design')

    def test_authenticated_user_can_create_a_skill(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('skills:create'), {
            'name': 'Public Speaking',
            'category': 'Communication',
            'description': 'Present with confidence',
        })
        self.assertRedirects(response, reverse('skills:list'))
        self.assertTrue(Skill.objects.filter(name='Public Speaking').exists())

    def test_anonymous_user_cannot_create_a_skill(self):
        response = self.client.get(reverse('skills:create'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('skills:create')}",
            fetch_redirect_response=False,
        )

    def test_case_insensitive_duplicate_skill_creation_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('skills:create'), {
            'name': ' python ',
            'category': 'Technology',
            'description': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A skill with this name already exists.')

    def test_user_can_add_and_remove_offered_skill(self):
        self.client.force_login(self.user)
        add_response = self.client.post(
            reverse('skills:add_offered', args=[self.python.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(add_response.status_code, 200)
        self.assertTrue(add_response.json()['ok'])
        self.assertTrue(self.user.offered_skills.filter(pk=self.python.pk).exists())

        remove_response = self.client.post(
            reverse('skills:remove_offered', args=[self.python.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(remove_response.status_code, 200)
        self.assertTrue(remove_response.json()['ok'])
        self.assertFalse(self.user.offered_skills.filter(pk=self.python.pk).exists())

    def test_user_can_add_and_remove_wanted_skill(self):
        self.client.force_login(self.user)
        self.client.post(reverse('skills:add_wanted', args=[self.design.pk]))
        self.assertTrue(self.user.wanted_skills.filter(pk=self.design.pk).exists())
        self.client.post(reverse('skills:remove_wanted', args=[self.design.pk]))
        self.assertFalse(self.user.wanted_skills.filter(pk=self.design.pk).exists())

    def test_adding_existing_relationship_does_not_duplicate_it(self):
        self.client.force_login(self.user)
        self.client.post(reverse('skills:add_offered', args=[self.python.pk]))
        self.client.post(reverse('skills:add_offered', args=[self.python.pk]))
        self.assertEqual(self.user.offered_skills.filter(pk=self.python.pk).count(), 1)

    def test_offered_skill_cannot_also_be_added_as_wanted(self):
        self.client.force_login(self.user)
        self.client.post(reverse('skills:add_offered', args=[self.python.pk]))

        response = self.client.post(
            reverse('skills:add_wanted', args=[self.python.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])
        self.assertEqual(
            response.json()['message'],
            'You already offer this skill. Remove it from your offered skills before adding it to your wanted skills.',
        )
        self.assertTrue(self.user.offered_skills.filter(pk=self.python.pk).exists())
        self.assertFalse(self.user.wanted_skills.filter(pk=self.python.pk).exists())

    def test_wanted_skill_cannot_also_be_added_as_offered(self):
        self.client.force_login(self.user)
        self.client.post(reverse('skills:add_wanted', args=[self.design.pk]))

        response = self.client.post(
            reverse('skills:add_offered', args=[self.design.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])
        self.assertEqual(
            response.json()['message'],
            'You already want to learn this skill. Remove it from your wanted skills before offering it.',
        )
        self.assertTrue(self.user.wanted_skills.filter(pk=self.design.pk).exists())
        self.assertFalse(self.user.offered_skills.filter(pk=self.design.pk).exists())

    def test_normal_post_overlap_rejection_uses_messages_and_preserves_relationships(self):
        self.client.force_login(self.user)
        self.client.post(reverse('skills:add_offered', args=[self.python.pk]))

        response = self.client.post(
            reverse('skills:add_wanted', args=[self.python.pk]),
            follow=True,
        )

        self.assertContains(response, 'You already offer this skill.')
        self.assertTrue(self.user.offered_skills.filter(pk=self.python.pk).exists())
        self.assertFalse(self.user.wanted_skills.filter(pk=self.python.pk).exists())

    def test_non_overlapping_skill_can_still_be_added(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('skills:add_offered', args=[self.python.pk]))

        self.assertRedirects(response, reverse('skills:list'))
        self.assertTrue(self.user.offered_skills.filter(pk=self.python.pk).exists())

    def test_anonymous_ajax_skill_action_returns_forbidden_json(self):
        response = self.client.post(
            reverse('skills:add_offered', args=[self.python.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['ok'])

    def test_invalid_skill_id_returns_not_found(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('skills:add_offered', args=[999999]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()['ok'])

    def test_invalid_service_kind_is_rejected(self):
        with self.assertRaises(ValidationError):
            add_user_skill(user=self.user, skill=self.python, kind='unknown')

    def test_skill_action_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        response = csrf_client.post(reverse('skills:add_offered', args=[self.python.pk]))
        self.assertEqual(response.status_code, 403)

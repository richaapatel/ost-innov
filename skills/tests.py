from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from .models import Skill


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
        user = User.objects.create_user(email='one@example.com', password='pass12345', name='One')
        other = User.objects.create_user(email='two@example.com', password='pass12345', name='Two')

        user.offered_skills.add(python, guitar)
        user.wanted_skills.add(guitar)
        other.offered_skills.add(python)

        self.assertEqual(set(user.offered_skills.all()), {python, guitar})
        self.assertEqual(list(user.wanted_skills.all()), [guitar])
        self.assertEqual(list(python.teachers.all()), [user, other])

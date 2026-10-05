from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from skills.models import Skill


User = get_user_model()


class CommunityTestDataMixin:
    def create_member(self, email, name, bio=''):
        return User.objects.create_user(
            email=email,
            password='StrongPass9!',
            name=name,
            bio=bio,
        )


class DiscoveryTests(CommunityTestDataMixin, TestCase):
    def setUp(self):
        self.python = Skill.objects.create(name='Python', category='Technology', description='Code and automation')
        self.design = Skill.objects.create(name='UI/UX Design', category='Design', description='User experience')
        self.spanish = Skill.objects.create(name='Spanish', category='Languages', description='Language practice')
        self.current = self.create_member('current@example.com', 'Current Member')
        self.arya = self.create_member('arya@example.com', 'Aryan Patel', 'Backend developer and mentor')
        self.mira = self.create_member('mira@example.com', 'Mira Stone', 'Design enthusiast')
        self.arya.offered_skills.add(self.python)
        self.arya.wanted_skills.add(self.design)
        self.mira.offered_skills.add(self.design)
        self.mira.wanted_skills.add(self.python)

    def test_discovery_is_public(self):
        response = self.client.get(reverse('community:discover'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aryan Patel')

    def test_search_by_name_is_case_insensitive(self):
        response = self.client.get(reverse('community:discover'), {'search': 'ARYAN'})
        self.assertContains(response, 'Aryan Patel')
        self.assertNotContains(response, 'Mira Stone')

    def test_offered_and_wanted_filters_work(self):
        response = self.client.get(reverse('community:discover'), {'offered_skill': self.python.pk})
        self.assertContains(response, 'Aryan Patel')
        self.assertNotContains(response, 'Mira Stone')

        response = self.client.get(reverse('community:discover'), {'wanted_skill': self.python.pk})
        self.assertContains(response, 'Mira Stone')
        self.assertNotContains(response, 'Aryan Patel')

    def test_combined_filters_work(self):
        response = self.client.get(reverse('community:discover'), {
            'search': 'ary',
            'offered_skill': self.python.pk,
            'wanted_skill': self.design.pk,
        })
        self.assertContains(response, 'Aryan Patel')
        self.assertNotContains(response, 'Mira Stone')

    def test_authenticated_current_user_is_excluded(self):
        self.client.force_login(self.current)
        response = self.client.get(reverse('community:discover'))
        self.assertNotContains(response, 'Current Member')

    def test_pagination_defaults_to_nine_and_preserves_filters(self):
        for index in range(10):
            self.create_member(f'user{index}@example.com', f'Member {index}')

        response = self.client.get(reverse('community:discover'), {'search': 'member', 'page': 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.per_page, 9)
        self.assertContains(response, 'search=member')

    def test_invalid_skill_filter_is_safe(self):
        response = self.client.get(reverse('community:discover'), {'offered_skill': 'not-a-number'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_no_results_state_works(self):
        response = self.client.get(reverse('community:discover'), {'search': 'does-not-exist'})
        self.assertContains(response, 'No members match those filters.')


class MemberDetailTests(CommunityTestDataMixin, TestCase):
    def setUp(self):
        self.python = Skill.objects.create(name='Python', category='Technology')
        self.member = self.create_member('member@example.com', 'Jordan Lee', 'I teach practical Python.')
        self.member.offered_skills.add(self.python)

    def test_public_member_profile_displays_public_information(self):
        response = self.client.get(reverse('community:member_detail', args=[self.member.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jordan Lee')
        self.assertContains(response, 'I teach practical Python.')
        self.assertContains(response, 'Python')
        self.assertContains(response, self.member.created_at.strftime('%B %Y'))
        self.assertNotContains(response, 'member@example.com')
        self.assertNotContains(response, 'password')

    def test_missing_member_returns_404(self):
        response = self.client.get(reverse('community:member_detail', args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_sees_login_action(self):
        response = self.client.get(reverse('community:member_detail', args=[self.member.pk]))
        self.assertContains(response, 'Log in to request learning')

    def test_authenticated_other_user_sees_prepared_request_action(self):
        viewer = self.create_member('viewer@example.com', 'Viewer User')
        self.client.force_login(viewer)
        response = self.client.get(reverse('community:member_detail', args=[self.member.pk]))
        self.assertContains(response, 'Request to Learn')

    def test_member_does_not_see_request_action_on_own_profile(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse('community:member_detail', args=[self.member.pk]))
        self.assertContains(response, 'Edit Profile')
        self.assertNotContains(response, 'Request to Learn')

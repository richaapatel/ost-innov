from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from exchanges.models import Exchange
from exchanges.services import change_exchange_status, create_exchange_request
from skills.models import Skill

from .analytics import build_exchange_status_figure, build_skill_demand_figure, figure_to_png_response
from .services import get_dashboard_statistics

import matplotlib.pyplot as plt


User = get_user_model()


class DashboardTestMixin:
    def create_user(self, email, name):
        return User.objects.create_user(
            email=email,
            password='StrongPass9!',
            name=name,
        )


class DashboardAccessAndContentTests(DashboardTestMixin, TestCase):
    def setUp(self):
        self.user = self.create_user('dashboard@example.com', 'Aryan Patel')
        self.other = self.create_user('other-dashboard@example.com', 'Other Member')
        self.python = Skill.objects.create(name='Dashboard Python', category='Technology')
        self.design = Skill.objects.create(name='Dashboard Design', category='Design')
        self.user.offered_skills.add(self.python)
        self.user.wanted_skills.add(self.design)

    def test_anonymous_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_authenticated_dashboard_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)

    def test_statistics_are_scoped_to_authenticated_user(self):
        teacher = self.create_user('dashboard-teacher@example.com', 'Dashboard Teacher')
        teacher.offered_skills.add(self.design)
        received = create_exchange_request(
            learner=self.other,
            teacher_id=self.user.pk,
            skill_id=self.python.pk,
        )
        sent = create_exchange_request(
            learner=self.user,
            teacher_id=teacher.pk,
            skill_id=self.design.pk,
        )
        unrelated = create_exchange_request(
            learner=self.other,
            teacher_id=teacher.pk,
            skill_id=self.design.pk,
        )

        statistics = get_dashboard_statistics(self.user)

        self.assertEqual(statistics['offered_count'], 1)
        self.assertEqual(statistics['wanted_count'], 1)
        self.assertEqual(statistics['pending_count'], 2)
        self.assertNotEqual(received.pk, unrelated.pk)
        self.assertNotEqual(sent.pk, unrelated.pk)

    def test_welcome_and_profile_summary_are_rendered_without_private_fields(self):
        self.user.bio = 'I enjoy teaching practical programming.'
        self.user.save(update_fields=('bio',))
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard:index'))

        self.assertContains(response, 'Welcome, Aryan')
        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.bio)
        self.assertContains(response, 'Dashboard Python')
        self.assertContains(response, 'Dashboard Design')
        self.assertNotContains(response, self.user.email)
        self.assertNotContains(response, 'StrongPass9!')

    def test_dashboard_limits_matches_and_requests(self):
        self.client.force_login(self.user)
        for index in range(5):
            candidate = self.create_user(f'match-{index}@example.com', f'Match Person {index}')
            candidate.offered_skills.add(self.design)
            candidate.wanted_skills.add(self.python)

        teacher = self.create_user('many-requests-teacher@example.com', 'Requests Teacher')
        teacher.offered_skills.add(self.design)
        for index in range(4):
            learner = self.create_user(f'received-{index}@example.com', f'Received {index}')
            create_exchange_request(
                learner=learner,
                teacher_id=self.user.pk,
                skill_id=self.python.pk,
            )
            sent_teacher = self.create_user(f'sent-{index}@example.com', f'Sent {index}')
            sent_teacher.offered_skills.add(self.design)
            create_exchange_request(
                learner=self.user,
                teacher_id=sent_teacher.pk,
                skill_id=self.design.pk,
            )

        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(len(response.context['matches']), 3)
        self.assertEqual(len(response.context['received_requests']), 2)
        self.assertEqual(len(response.context['sent_requests']), 2)

    def test_empty_dashboard_state_is_rendered(self):
        empty_user = self.create_user('empty-dashboard@example.com', 'Empty User')
        self.client.force_login(empty_user)
        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add a learning goal to get matched')
        self.assertContains(response, 'No offered skills yet')
        self.assertContains(response, 'No sent requests yet')
        self.assertContains(response, 'There is no skill demand data yet')
        self.assertContains(response, 'There are currently no exchange requests')


class DashboardChartTests(DashboardTestMixin, TestCase):
    def setUp(self):
        self.user = self.create_user('charts@example.com', 'Charts User')

    def test_anonymous_users_cannot_access_chart_endpoints(self):
        for route_name in ('dashboard:skill_demand_chart', 'dashboard:exchange_status_chart'):
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('accounts:login'), response.url)

    def test_authenticated_chart_endpoints_return_png(self):
        self.client.force_login(self.user)
        for route_name in ('dashboard:skill_demand_chart', 'dashboard:exchange_status_chart'):
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/png')
            self.assertTrue(response.content.startswith(b'\x89PNG'))

    def test_empty_chart_data_returns_images_without_repository_files(self):
        self.client.force_login(self.user)
        before = {path.name for path in Path('dashboard').glob('*.png')}

        skill_response = self.client.get(reverse('dashboard:skill_demand_chart'))
        exchange_response = self.client.get(reverse('dashboard:exchange_status_chart'))

        self.assertEqual(skill_response['Content-Type'], 'image/png')
        self.assertEqual(exchange_response['Content-Type'], 'image/png')
        self.assertEqual(before, {path.name for path in Path('dashboard').glob('*.png')})

    def test_chart_figures_are_closed_after_response_creation(self):
        before = set(plt.get_fignums())
        skill_response = figure_to_png_response(build_skill_demand_figure([]))
        exchange_response = figure_to_png_response(build_exchange_status_figure({status: 0 for status, _ in Exchange.Status.choices}))

        self.assertEqual(skill_response['Content-Type'], 'image/png')
        self.assertEqual(exchange_response['Content-Type'], 'image/png')
        self.assertEqual(before, set(plt.get_fignums()))

    def test_skill_chart_uses_real_demand_data(self):
        skill = Skill.objects.create(name='Chart Python', category='Technology')
        learner = self.create_user('chart-learner@example.com', 'Chart Learner')
        learner.wanted_skills.add(skill)
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard:skill_demand_chart'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'\x89PNG'))

    def test_exchange_chart_includes_all_status_values(self):
        skill = Skill.objects.create(name='Chart Exchange Skill')
        teacher = self.create_user('chart-teacher@example.com', 'Chart Teacher')
        teacher.offered_skills.add(skill)
        learner = self.create_user('chart-learner-2@example.com', 'Chart Learner Two')
        exchange = create_exchange_request(
            learner=learner,
            teacher_id=teacher.pk,
            skill_id=skill.pk,
        )
        change_exchange_status(exchange=exchange, actor=teacher, action=Exchange.Status.ACCEPTED)
        self.client.force_login(teacher)

        response = self.client.get(reverse('dashboard:exchange_status_chart'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'\x89PNG'))

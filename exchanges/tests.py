from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from skills.models import Skill
from skills.services import add_user_skill

from .models import Exchange
from .services import ExchangeServiceError, change_exchange_status, create_exchange_request, get_users_taught_count


User = get_user_model()


class ExchangeTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(email='teacher@example.com', password='pass12345', name='Teacher')
        self.learner = User.objects.create_user(email='learner@example.com', password='pass12345', name='Learner')
        self.other = User.objects.create_user(email='other@example.com', password='pass12345', name='Other')
        self.participant = User.objects.create_user(
            email='participant@example.com', password='pass12345', name='Participant'
        )
        self.skill = Skill.objects.create(name='Python', category='Technology')
        self.teacher.offered_skills.add(self.skill)

    def request(self, **kwargs):
        defaults = {'learner': self.learner, 'teacher_id': self.teacher.pk, 'skill_id': self.skill.pk}
        defaults.update(kwargs)
        return create_exchange_request(**defaults)

    def test_exchange_creation_defaults_to_pending_and_generates_key(self):
        exchange = self.request(message='I would like to learn Python.')
        self.assertEqual(exchange.status, Exchange.Status.PENDING)
        self.assertEqual(exchange.active_request_key, f'{self.learner.pk}:{self.teacher.pk}:{self.skill.pk}')
        self.assertEqual(exchange.teacher, self.teacher)
        self.assertEqual(exchange.learner, self.learner)
        self.assertEqual(exchange.skill, self.skill)
        self.assertEqual(str(exchange), f'{self.learner} → {self.teacher}: {self.skill} (Pending)')

    def test_message_max_length_is_validated(self):
        exchange = Exchange(teacher=self.teacher, learner=self.learner, skill=self.skill, message='x' * 501)
        with self.assertRaises(ValidationError):
            exchange.full_clean()

    def test_duplicate_active_key_is_rejected(self):
        self.request()
        with self.assertRaises(ExchangeServiceError):
            self.request()

    def test_multiple_null_active_request_keys_are_allowed(self):
        first = self.request()
        first.status = Exchange.Status.ACCEPTED
        first.save()
        second = Exchange.objects.create(teacher=self.teacher, learner=self.other, skill=self.skill)
        second.status = Exchange.Status.REJECTED
        second.save()
        self.assertIsNone(first.active_request_key)
        self.assertIsNone(second.active_request_key)
        self.assertEqual(Exchange.objects.filter(active_request_key__isnull=True).count(), 2)

    def test_valid_status_choices(self):
        self.assertEqual({value for value, _ in Exchange.Status.choices}, {'pending', 'accepted', 'rejected', 'completed'})

    def test_service_validation_for_request_creation(self):
        with self.assertRaises(ExchangeServiceError):
            self.request(learner=self.teacher)
        with self.assertRaises(ExchangeServiceError):
            self.request(teacher_id=999999)
        with self.assertRaises(ExchangeServiceError):
            self.request(skill_id=999999)
        unoffered = Skill.objects.create(name='Guitar')
        with self.assertRaises(ExchangeServiceError):
            self.request(skill_id=unoffered.pk)

    def test_status_transition_permissions_and_terminal_states(self):
        pending = self.request()
        with self.assertRaises(ExchangeServiceError):
            change_exchange_status(exchange=pending, actor=self.learner, action=Exchange.Status.ACCEPTED)
        with self.assertRaises(ExchangeServiceError):
            change_exchange_status(exchange=pending, actor=self.learner, action=Exchange.Status.REJECTED)

        accepted = change_exchange_status(exchange=pending, actor=self.teacher, action=Exchange.Status.ACCEPTED)
        self.assertEqual(accepted.status, Exchange.Status.ACCEPTED)
        self.assertIsNone(accepted.active_request_key)
        with self.assertRaises(ExchangeServiceError):
            change_exchange_status(exchange=accepted, actor=self.other, action=Exchange.Status.COMPLETED)
        completed = change_exchange_status(exchange=accepted, actor=self.learner, action=Exchange.Status.COMPLETED)
        self.assertEqual(completed.status, Exchange.Status.COMPLETED)
        with self.assertRaises(ExchangeServiceError):
            change_exchange_status(exchange=completed, actor=self.teacher, action=Exchange.Status.PENDING)

        teacher_completed = self.request(learner=self.participant)
        teacher_completed = change_exchange_status(
            exchange=teacher_completed,
            actor=self.teacher,
            action=Exchange.Status.ACCEPTED,
        )
        teacher_completed = change_exchange_status(
            exchange=teacher_completed,
            actor=self.teacher,
            action=Exchange.Status.COMPLETED,
        )
        self.assertEqual(teacher_completed.status, Exchange.Status.COMPLETED)

        rejected = self.request(learner=self.other)
        rejected = change_exchange_status(exchange=rejected, actor=self.teacher, action=Exchange.Status.REJECTED)
        with self.assertRaises(ExchangeServiceError):
            change_exchange_status(exchange=rejected, actor=self.teacher, action=Exchange.Status.ACCEPTED)
        with self.assertRaises(ExchangeServiceError):
            change_exchange_status(exchange=rejected, actor=self.teacher, action=Exchange.Status.COMPLETED)

    def test_new_request_allowed_after_previous_request_leaves_pending(self):
        first = self.request()
        change_exchange_status(exchange=first, actor=self.teacher, action=Exchange.Status.REJECTED)
        second = self.request()
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(second.status, Exchange.Status.PENDING)


class ExchangeWorkflowTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            email='workflow-teacher@example.com', password='StrongPass9!', name='Teacher One'
        )
        self.learner = User.objects.create_user(
            email='workflow-learner@example.com', password='StrongPass9!', name='Learner One'
        )
        self.third_party = User.objects.create_user(
            email='workflow-third@example.com', password='StrongPass9!', name='Third Party'
        )
        self.skill = Skill.objects.create(name='Workflow Python')
        self.teacher.offered_skills.add(self.skill)

    def _payload(self, **overrides):
        payload = {
            'teacher_id': self.teacher.pk,
            'skill_id': self.skill.pk,
            'message': 'I would love to learn this.',
        }
        payload.update(overrides)
        return payload

    def test_ajax_creation_returns_expected_success_shape(self):
        self.client.force_login(self.learner)
        response = self.client.post(
            reverse('exchanges:create'),
            self._payload(),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['data']['status'], Exchange.Status.PENDING)
        self.assertEqual(body['data']['skill'], self.skill.name)

    def test_duplicate_ajax_creation_returns_conflict_shape(self):
        create_exchange_request(
            learner=self.learner,
            teacher_id=self.teacher.pk,
            skill_id=self.skill.pk,
        )
        self.client.force_login(self.learner)
        response = self.client.post(
            reverse('exchanges:create'),
            self._payload(),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json()['ok'])
        self.assertIn('errors', response.json())

    def test_ajax_validation_error_is_structured(self):
        self.client.force_login(self.learner)
        response = self.client.post(
            reverse('exchanges:create'),
            self._payload(skill_id=999999),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])
        self.assertIn('skill_id', response.json()['errors'])

    def test_creation_uses_authenticated_learner_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.learner)
        response = client.post(reverse('exchanges:create'), self._payload())
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Exchange.objects.exists())

    def test_sent_and_received_lists_show_the_exchange(self):
        exchange = create_exchange_request(
            learner=self.learner,
            teacher_id=self.teacher.pk,
            skill_id=self.skill.pk,
        )
        self.client.force_login(self.learner)
        sent = self.client.get(reverse('exchanges:list'), {'tab': 'sent'})
        self.assertContains(sent, self.teacher.name)
        self.assertContains(sent, exchange.skill.name)

        self.client.force_login(self.teacher)
        received = self.client.get(reverse('exchanges:list'))
        self.assertContains(received, self.learner.name)

    def test_detail_is_private_to_participants(self):
        exchange = create_exchange_request(
            learner=self.learner,
            teacher_id=self.teacher.pk,
            skill_id=self.skill.pk,
        )
        self.client.force_login(self.third_party)
        response = self.client.get(reverse('exchanges:detail', args=[exchange.pk]))
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_accept_and_learner_can_complete_via_views(self):
        exchange = create_exchange_request(
            learner=self.learner,
            teacher_id=self.teacher.pk,
            skill_id=self.skill.pk,
        )
        self.client.force_login(self.learner)
        denied = self.client.post(reverse('exchanges:accept', args=[exchange.pk]))
        self.assertEqual(denied.status_code, 302)
        exchange.refresh_from_db()
        self.assertEqual(exchange.status, Exchange.Status.PENDING)

        self.client.force_login(self.teacher)
        accepted = self.client.post(reverse('exchanges:accept', args=[exchange.pk]))
        self.assertEqual(accepted.status_code, 302)
        exchange.refresh_from_db()
        self.assertEqual(exchange.status, Exchange.Status.ACCEPTED)
        self.assertIsNone(exchange.active_request_key)

        self.client.force_login(self.learner)
        completed = self.client.post(reverse('exchanges:complete', args=[exchange.pk]))
        self.assertEqual(completed.status_code, 302)
        exchange.refresh_from_db()
        self.assertEqual(exchange.status, Exchange.Status.COMPLETED)

    def test_rejected_and_completed_requests_cannot_transition(self):
        rejected = create_exchange_request(
            learner=self.learner,
            teacher_id=self.teacher.pk,
            skill_id=self.skill.pk,
        )
        change_exchange_status(exchange=rejected, actor=self.teacher, action='reject')
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('exchanges:accept', args=[rejected.pk]))
        self.assertEqual(response.status_code, 302)
        rejected.refresh_from_db()
        self.assertEqual(rejected.status, Exchange.Status.REJECTED)

        completed = create_exchange_request(
            learner=self.learner,
            teacher_id=self.teacher.pk,
            skill_id=self.skill.pk,
        )
        change_exchange_status(exchange=completed, actor=self.teacher, action='accept')
        change_exchange_status(exchange=completed, actor=self.teacher, action='complete')
        response = self.client.post(reverse('exchanges:reject', args=[completed.pk]))
        self.assertEqual(response.status_code, 302)
        completed.refresh_from_db()
        self.assertEqual(completed.status, Exchange.Status.COMPLETED)

    def test_completed_exchange_updates_teacher_dashboard_count_only(self):
        self.learner.wanted_skills.add(Skill.objects.create(name='Learner Java'))
        self.learner.offered_skills.add(self.skill)
        with self.assertRaises(ValidationError):
            add_user_skill(user=self.learner, skill=self.skill, kind='wanted')
        self.assertFalse(self.learner.wanted_skills.filter(pk=self.skill.pk).exists())
        self.client.force_login(self.learner)

        request = create_exchange_request(
            learner=self.learner,
            teacher_id=self.teacher.pk,
            skill_id=self.skill.pk,
        )
        change_exchange_status(exchange=request, actor=self.teacher, action=Exchange.Status.ACCEPTED)
        change_exchange_status(exchange=request, actor=self.learner, action=Exchange.Status.COMPLETED)

        self.assertEqual(get_users_taught_count(self.teacher), 1)
        self.assertEqual(get_users_taught_count(self.learner), 0)

        self.client.force_login(self.teacher)
        dashboard = self.client.get(reverse('dashboard:index'))
        self.assertEqual(dashboard.context['statistics']['users_taught_count'], 1)
        self.assertContains(dashboard, 'Users taught')

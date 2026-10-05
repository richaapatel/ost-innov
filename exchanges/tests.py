from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from skills.models import Skill

from .models import Exchange
from .services import ExchangeServiceError, change_exchange_status, create_exchange_request


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

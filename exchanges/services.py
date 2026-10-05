from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from accounts.models import User
from skills.models import Skill

from .models import Exchange


class ExchangeServiceError(ValidationError):
    """Raised when an exchange operation violates a business rule."""


def create_exchange_request(*, learner: User, teacher_id: int, skill_id: int, message: str = '') -> Exchange:
    """Create one pending request after rechecking all participant relationships."""
    if not getattr(learner, 'pk', None):
        raise ExchangeServiceError('A saved learner is required.')
    message = (message or '').strip()
    if len(message) > 500:
        raise ExchangeServiceError('Message cannot exceed 500 characters.')
    try:
        teacher_id = int(teacher_id)
    except (TypeError, ValueError) as exc:
        raise ExchangeServiceError('The selected teacher does not exist.') from exc
    try:
        skill_id = int(skill_id)
    except (TypeError, ValueError) as exc:
        raise ExchangeServiceError('The selected skill does not exist.') from exc

    try:
        with transaction.atomic():
            teacher = User.objects.select_for_update().filter(pk=teacher_id, is_active=True).first()
            if teacher is None:
                raise ExchangeServiceError('The selected teacher does not exist.')
            if teacher.pk == learner.pk:
                raise ExchangeServiceError('A learner cannot request an exchange from themselves.')

            skill = Skill.objects.filter(pk=skill_id).first()
            if skill is None:
                raise ExchangeServiceError('The selected skill does not exist.')
            if not teacher.offered_skills.filter(pk=skill.pk).exists():
                raise ExchangeServiceError('The teacher does not offer the selected skill.')

            existing = Exchange.objects.select_for_update().filter(
                learner_id=learner.pk,
                teacher_id=teacher.pk,
                skill_id=skill.pk,
                status=Exchange.Status.PENDING,
            ).first()
            if existing is not None:
                raise ExchangeServiceError('A pending request already exists for this exchange.')

            try:
                return Exchange.objects.create(
                    learner=learner,
                    teacher=teacher,
                    skill=skill,
                    message=message,
                    status=Exchange.Status.PENDING,
                )
            except IntegrityError as exc:
                # The unique key is the final guard if two requests race.
                raise ExchangeServiceError('A pending request already exists for this exchange.') from exc
    except ExchangeServiceError:
        raise


def change_exchange_status(*, exchange: Exchange, actor: User, action: str) -> Exchange:
    """Apply one of the allowed status transitions with a row lock."""
    if not getattr(actor, 'pk', None):
        raise ExchangeServiceError('A saved actor is required.')

    action = {
        'accept': Exchange.Status.ACCEPTED,
        'reject': Exchange.Status.REJECTED,
        'complete': Exchange.Status.COMPLETED,
    }.get(action, action)

    with transaction.atomic():
        try:
            locked_exchange = Exchange.objects.select_for_update().get(pk=exchange.pk)
        except Exchange.DoesNotExist as exc:
            raise ExchangeServiceError('The exchange does not exist.') from exc
        actor_id = actor.pk

        if locked_exchange.status == Exchange.Status.PENDING:
            if action not in (Exchange.Status.ACCEPTED, Exchange.Status.REJECTED):
                raise ExchangeServiceError('Pending requests can only be accepted or rejected.')
            if locked_exchange.teacher_id != actor_id:
                raise ExchangeServiceError('Only the teacher can accept or reject a request.')
        elif locked_exchange.status == Exchange.Status.ACCEPTED:
            if action != Exchange.Status.COMPLETED:
                raise ExchangeServiceError('Accepted requests can only be completed.')
            if actor_id not in (locked_exchange.teacher_id, locked_exchange.learner_id):
                raise ExchangeServiceError('Only an exchange participant can complete the request.')
        else:
            raise ExchangeServiceError('Rejected and completed requests cannot change status.')

        locked_exchange.status = action
        locked_exchange.save(update_fields=('status', 'active_request_key', 'updated_at'))
        return locked_exchange

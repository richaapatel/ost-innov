from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Skill


User = get_user_model()
VALID_KINDS = {'offered', 'wanted'}


def _skill_manager(*, user, kind):
    if not getattr(user, 'is_authenticated', False) or not getattr(user, 'pk', None):
        raise ValidationError('A saved authenticated user is required.')
    if kind not in VALID_KINDS:
        raise ValidationError('Skill kind must be either offered or wanted.')
    return user.offered_skills if kind == 'offered' else user.wanted_skills


def _validate_skill(skill):
    if not isinstance(skill, Skill) or not skill.pk:
        raise ValidationError('A saved skill is required.')
    if not Skill.objects.filter(pk=skill.pk).exists():
        raise ValidationError('The selected skill does not exist.')


def add_user_skill(*, user, skill, kind):
    """Idempotently associate a skill while preventing offer/learn overlap."""
    _skill_manager(user=user, kind=kind)
    _validate_skill(skill)

    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        target = locked_user.offered_skills if kind == 'offered' else locked_user.wanted_skills
        opposite = locked_user.wanted_skills if kind == 'offered' else locked_user.offered_skills
        if opposite.filter(pk=skill.pk).exists():
            if kind == 'offered':
                raise ValidationError(
                    'You already want to learn this skill. Remove it from your wanted skills before offering it.'
                )
            raise ValidationError(
                'You already offer this skill. Remove it from your offered skills before adding it to your wanted skills.'
            )
        target.add(skill)
    return skill


def remove_user_skill(*, user, skill, kind):
    """Remove a skill association without affecting the shared skill."""
    _skill_manager(user=user, kind=kind)
    _validate_skill(skill)
    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        manager = locked_user.offered_skills if kind == 'offered' else locked_user.wanted_skills
        manager.remove(skill)
    return skill

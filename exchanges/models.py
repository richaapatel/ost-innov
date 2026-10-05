from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from skills.models import Skill


class Exchange(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'

    PENDING = Status.PENDING
    ACCEPTED = Status.ACCEPTED
    REJECTED = Status.REJECTED
    COMPLETED = Status.COMPLETED

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='received_exchanges',
    )
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sent_exchanges',
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.PROTECT,
        related_name='exchanges',
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    message = models.CharField(max_length=500, blank=True, default='')
    active_request_key = models.CharField(max_length=310, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=('teacher', 'status'), name='exchange_teacher_status_idx'),
            models.Index(fields=('learner', 'status'), name='exchange_learner_status_idx'),
            models.Index(fields=('skill', 'status'), name='exchange_skill_status_idx'),
            models.Index(fields=('created_at',), name='exchange_created_at_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(teacher=models.F('learner')),
                name='exchange_teacher_learner_diff',
            ),
        ]

    def __str__(self):
        return f'{self.learner} → {self.teacher}: {self.skill} ({self.get_status_display()})'

    def clean(self):
        super().clean()
        if self.teacher_id and self.learner_id and self.teacher_id == self.learner_id:
            raise ValidationError({'learner': 'A learner cannot request an exchange from themselves.'})

    def save(self, *args, **kwargs):
        if self.status == self.Status.PENDING and self.learner_id and self.teacher_id and self.skill_id:
            self.active_request_key = f'{self.learner_id}:{self.teacher_id}:{self.skill_id}'
        else:
            self.active_request_key = None
        self.full_clean()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and {'status', 'teacher', 'teacher_id', 'learner', 'learner_id', 'skill', 'skill_id'} & set(update_fields):
            kwargs['update_fields'] = set(update_fields) | {'active_request_key'}
        return super().save(*args, **kwargs)

from django.core.exceptions import ValidationError
from django.db import models


class Skill(models.Model):
    """A skill that users can offer or request."""

    name = models.CharField(max_length=100, unique=True)
    # A normalized value gives MySQL-independent, database-backed
    # case-insensitive uniqueness without relying on a collation choice.
    normalized_name = models.CharField(
        max_length=100,
        unique=True,
        editable=False,
    )
    description = models.CharField(max_length=500, blank=True, default='')
    category = models.CharField(max_length=80, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        indexes = [
            models.Index(fields=('category',), name='skill_category_idx'),
        ]

    def __str__(self):
        return self.name

    @staticmethod
    def normalize_name(value: str) -> str:
        return ' '.join(value.strip().casefold().split())

    def clean(self):
        self.name = (self.name or '').strip()
        self.normalized_name = self.normalize_name(self.name)
        if not self.name:
            raise ValidationError({'name': 'Skill name cannot be empty.'})
        if not self.normalized_name:
            raise ValidationError({'name': 'Skill name cannot be empty.'})
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'name' in update_fields and 'normalized_name' not in update_fields:
            kwargs['update_fields'] = set(update_fields) | {'normalized_name'}
        return super().save(*args, **kwargs)

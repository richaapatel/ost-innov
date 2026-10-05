from django import forms
from django.contrib.auth import get_user_model

from skills.models import Skill


User = get_user_model()


class ExchangeRequestForm(forms.Form):
    """Request form used by the modal and the non-JavaScript fallback."""

    teacher_id = forms.IntegerField(widget=forms.HiddenInput)
    skill_id = forms.ModelChoiceField(
        queryset=Skill.objects.none(),
        empty_label='Choose a skill',
        label='Skill you want to learn',
    )
    message = forms.CharField(
        required=False,
        max_length=500,
        strip=True,
        widget=forms.Textarea(attrs={'rows': 4, 'maxlength': 500}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        teacher_id = self.data.get('teacher_id') if self.is_bound else self.initial.get('teacher_id')
        try:
            teacher_id = int(teacher_id) if teacher_id else None
        except (TypeError, ValueError):
            teacher_id = None
        teacher = User.objects.filter(pk=teacher_id, is_active=True).first() if teacher_id else None
        if teacher:
            self.fields['skill_id'].queryset = teacher.offered_skills.order_by('name', 'pk')

    def clean_teacher_id(self):
        teacher_id = self.cleaned_data['teacher_id']
        teacher = User.objects.filter(pk=teacher_id, is_active=True).first()
        if teacher is None:
            raise forms.ValidationError('That member is no longer available.')
        return teacher_id

    def clean_message(self):
        return self.cleaned_data.get('message', '').strip()

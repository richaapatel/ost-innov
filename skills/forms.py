from django import forms

from .models import Skill


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ('name', 'description', 'category')


class SkillCreateForm(forms.ModelForm):
    name = forms.CharField(
        label='Skill name',
        max_length=100,
        strip=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'maxlength': 100,
            'placeholder': 'e.g. Python, Public Speaking, Guitar',
        }),
    )
    category = forms.CharField(
        label='Category',
        max_length=80,
        required=False,
        strip=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'maxlength': 80,
            'placeholder': 'e.g. Technology, Design, Music',
        }),
    )
    description = forms.CharField(
        label='Description',
        max_length=500,
        required=False,
        strip=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'maxlength': 500,
            'placeholder': 'What can people learn about this skill?',
            'rows': 4,
        }),
    )

    class Meta:
        model = Skill
        fields = ('name', 'category', 'description')

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Please enter a skill name.')
        normalized_name = Skill.normalize_name(name)
        if Skill.objects.filter(normalized_name=normalized_name).exists():
            raise forms.ValidationError('A skill with this name already exists.')
        return name

    def clean_category(self):
        return self.cleaned_data['category'].strip()

    def clean_description(self):
        return self.cleaned_data['description'].strip()

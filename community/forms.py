from django import forms

from skills.models import Skill


class DiscoveryFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        max_length=80,
        strip=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by member name',
            'autocomplete': 'off',
        }),
    )
    offered_skill = forms.ModelChoiceField(
        required=False,
        queryset=Skill.objects.none(),
        empty_label='Any skill offered',
    )
    wanted_skill = forms.ModelChoiceField(
        required=False,
        queryset=Skill.objects.none(),
        empty_label='Any skill wanted',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        skills = Skill.objects.order_by('name')
        self.fields['offered_skill'].queryset = skills
        self.fields['wanted_skill'].queryset = skills

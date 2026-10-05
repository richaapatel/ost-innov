from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


User = get_user_model()


class RegistrationForm(forms.ModelForm):
    name = forms.CharField(
        label='Full name',
        max_length=80,
        strip=True,
        widget=forms.TextInput(attrs={
            'autocomplete': 'name',
            'placeholder': 'Your full name',
        }),
    )
    email = forms.EmailField(
        label='Email address',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'you@example.com',
        }),
    )
    password1 = forms.CharField(
        label='Password',
        max_length=128,
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Create a strong password',
        }),
    )
    password2 = forms.CharField(
        label='Confirm password',
        max_length=128,
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Repeat your password',
        }),
    )

    class Meta:
        model = User
        fields = ('name', 'email', 'password1', 'password2')

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Please enter your full name.')
        return name

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password1(self):
        password = self.cleaned_data['password1']
        candidate = User(
            name=self.cleaned_data.get('name', ''),
            email=self.cleaned_data.get('email', ''),
        )
        try:
            validate_password(password, user=candidate)
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'The passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.name = self.cleaned_data['name']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Email address',
        max_length=254,
        strip=True,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'you@example.com',
        }),
    )
    error_messages = {
        'invalid_login': 'Invalid email or password.',
        'inactive': 'Invalid email or password.',
    }

    def clean(self):
        if self.cleaned_data.get('username'):
            self.cleaned_data['username'] = self.cleaned_data['username'].strip().lower()
        return super().clean()


class ProfileUpdateForm(forms.ModelForm):
    name = forms.CharField(
        label='Full name',
        max_length=80,
        strip=True,
        widget=forms.TextInput(attrs={
            'autocomplete': 'name',
            'maxlength': 80,
            'placeholder': 'Your full name',
        }),
    )
    bio = forms.CharField(
        label='Bio',
        max_length=500,
        required=False,
        strip=True,
        widget=forms.Textarea(attrs={
            'autocomplete': 'off',
            'maxlength': 500,
            'placeholder': 'Tell the community a little about yourself...',
            'rows': 5,
        }),
    )

    class Meta:
        model = User
        fields = ('name', 'bio')

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Please enter your full name.')
        return name

    def clean_bio(self):
        return self.cleaned_data['bio'].strip()

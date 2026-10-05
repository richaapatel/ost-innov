from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .forms import LoginForm, ProfileUpdateForm, RegistrationForm
from .utils import get_user_initials


def _auth_redirect(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    return None


def register(request):
    authenticated_redirect = _auth_redirect(request)
    if authenticated_redirect:
        return authenticated_redirect

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            form.add_error('email', 'An account with this email already exists.')
        else:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully.')
            return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, 'accounts/register.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def login_view(request):
    authenticated_redirect = _auth_redirect(request)
    if authenticated_redirect:
        return authenticated_redirect

    next_url = request.POST.get('next') or request.GET.get('next', '')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, 'Welcome back.')
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, 'accounts/login.html', {'form': form, 'next_url': next_url})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect(settings.LOGOUT_REDIRECT_URL)


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile_user': request.user,
        'initials': get_user_initials(request.user.name),
        'offered_skills': request.user.offered_skills.all(),
        'wanted_skills': request.user.wanted_skills.all(),
    })

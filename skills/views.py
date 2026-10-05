import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import SkillCreateForm
from .models import Skill
from .services import add_user_skill, remove_user_skill


logger = logging.getLogger(__name__)


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _json_error(message, *, status=400, errors=None):
    return JsonResponse({
        'ok': False,
        'message': message,
        'errors': errors or {},
    }, status=status)


def _action_authentication(request):
    if request.user.is_authenticated:
        return None
    if _is_ajax(request):
        return _json_error('Please log in to manage your skills.', status=403)
    return redirect_to_login(request.get_full_path())


def _skill_library_context(request):
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '').strip()
    skills = Skill.objects.all()
    if search:
        skills = skills.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if category:
        skills = skills.filter(category=category)

    context = {
        'skills': skills,
        'form': None,
        'search': search,
        'selected_category': category,
        'categories': Skill.objects.exclude(category='').values_list('category', flat=True).distinct().order_by('category'),
        'offered_skills': Skill.objects.none(),
        'wanted_skills': Skill.objects.none(),
        'offered_ids': set(),
        'wanted_ids': set(),
    }
    if request.user.is_authenticated:
        context['offered_skills'] = request.user.offered_skills.all()
        context['wanted_skills'] = request.user.wanted_skills.all()
        context['offered_ids'] = set(context['offered_skills'].values_list('pk', flat=True))
        context['wanted_ids'] = set(context['wanted_skills'].values_list('pk', flat=True))
    return context


@require_GET
def skill_list(request):
    return render(request, 'skills/list.html', _skill_library_context(request))


@login_required
def skill_create(request):
    form = SkillCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error('name', 'A skill with this name already exists.')
        else:
            messages.success(request, 'Skill created successfully.')
            return redirect('skills:list')

    return render(request, 'skills/create.html', {'form': form})


def _get_skill_for_action(request, skill_id):
    try:
        return Skill.objects.get(pk=skill_id)
    except Skill.DoesNotExist:
        if _is_ajax(request):
            return _json_error('That skill could not be found.', status=404)
        raise Http404('Skill not found')


@require_POST
def _change_skill_relationship(request, skill_id, *, kind, add):
    authentication_response = _action_authentication(request)
    if authentication_response:
        return authentication_response

    skill = _get_skill_for_action(request, skill_id)
    if isinstance(skill, JsonResponse):
        return skill

    try:
        service = add_user_skill if add else remove_user_skill
        service(user=request.user, skill=skill, kind=kind)
    except ValidationError as exc:
        message = exc.messages[0] if exc.messages else 'Unable to update this skill.'
        if _is_ajax(request):
            return _json_error(message, errors={'kind': exc.messages}, status=400)
        messages.error(request, message)
        return redirect('skills:list')
    except DatabaseError:
        logger.exception('Unable to update skill relationship for user %s', request.user.pk)
        if _is_ajax(request):
            return _json_error('We could not update that skill right now.', status=500)
        messages.error(request, 'We could not update that skill right now.')
        return redirect('skills:list')

    selected = add
    message = f"Skill {'added to' if add else 'removed from'} your {'offered' if kind == 'offered' else 'wanted'} skills."
    data = {
        'skill_id': skill.pk,
        'skill_name': skill.name,
        'kind': kind,
        'selected': selected,
    }
    if _is_ajax(request):
        return JsonResponse({'ok': True, 'message': message, 'data': data})
    messages.success(request, message)
    return redirect('skills:list')


def add_offered(request, skill_id):
    return _change_skill_relationship(request, skill_id, kind='offered', add=True)


def remove_offered(request, skill_id):
    return _change_skill_relationship(request, skill_id, kind='offered', add=False)


def add_wanted(request, skill_id):
    return _change_skill_relationship(request, skill_id, kind='wanted', add=True)


def remove_wanted(request, skill_id):
    return _change_skill_relationship(request, skill_id, kind='wanted', add=False)

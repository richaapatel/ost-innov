import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from accounts.utils import get_user_initials

from .forms import DiscoveryFilterForm, MatchFilterForm
from .services import discover_members, get_match_results


User = get_user_model()


def _add_public_display_data(members):
    for member in members:
        member.initials = get_user_initials(member.name)
        member.request_skills_json = json.dumps([
            {'id': skill.pk, 'name': skill.name}
            for skill in member.offered_skills.all()
        ])
    return members


@require_GET
def discover(request):
    form = DiscoveryFilterForm(request.GET or None)
    search = ''
    offered_skill = None
    wanted_skill = None
    if form.is_valid():
        search = form.cleaned_data.get('search', '')
        offered_skill = form.cleaned_data.get('offered_skill')
        wanted_skill = form.cleaned_data.get('wanted_skill')

    members = discover_members(
        search=search,
        offered_skill=offered_skill,
        wanted_skill=wanted_skill,
        exclude_user=request.user,
    )
    paginator = Paginator(members, 9)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    _add_public_display_data(page_obj.object_list)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    return render(request, 'community/discover.html', {
        'form': form,
        'page_obj': page_obj,
        'query_string': query_params.urlencode(),
        'result_count': paginator.count,
    })


@require_GET
def member_detail(request, user_id):
    member = get_object_or_404(
        User.objects.filter(is_active=True).prefetch_related('offered_skills', 'wanted_skills'),
        pk=user_id,
    )
    member.initials = get_user_initials(member.name)
    member.request_skills_json = json.dumps([
        {'id': skill.pk, 'name': skill.name}
        for skill in member.offered_skills.all()
    ])
    is_self = request.user.is_authenticated and request.user.pk == member.pk
    return render(request, 'community/member_detail.html', {
        'member': member,
        'is_self': is_self,
    })


@login_required
@require_GET
def matches(request):
    wanted_skills = list(request.user.wanted_skills.all().order_by('name', 'pk')) if request.user.is_authenticated else []
    form = MatchFilterForm(request.GET or None, wanted_skills=wanted_skills)
    skill_id = None
    if form.is_valid():
        selected_skill = form.cleaned_data.get('skill')
        skill_id = selected_skill.pk if selected_skill else None

    results = get_match_results(
        request.user,
        skill_id=skill_id if form.is_valid() else request.GET.get('skill'),
        page=request.GET.get('page', 1),
        limit=9,
    )
    if results.invalid_skill and request.GET.get('skill'):
        form.add_error('skill', 'Choose a skill you have marked as wanted.')

    query_params = request.GET.copy()
    query_params.pop('page', None)
    return render(request, 'community/matches.html', {
        'form': form,
        'matches': results,
        'page_obj': results.page_obj,
        'wanted_skills': results.wanted_skills,
        'selected_skill': results.selected_skill,
        'no_wanted_skills': results.no_wanted_skills,
        'query_string': query_params.urlencode(),
    })

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from accounts.utils import get_user_initials

from .forms import DiscoveryFilterForm
from .services import discover_members


User = get_user_model()


def _add_public_display_data(members):
    for member in members:
        member.initials = get_user_initials(member.name)
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
    is_self = request.user.is_authenticated and request.user.pk == member.pk
    return render(request, 'community/member_detail.html', {
        'member': member,
        'is_self': is_self,
    })

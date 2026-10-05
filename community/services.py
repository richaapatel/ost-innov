import json

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch

from accounts.utils import get_user_initials

User = get_user_model()


class MatchResults(list):
    """A paginated list that also carries matching-page metadata."""

    def __init__(
        self,
        matches=(),
        *,
        page_obj=None,
        wanted_skills=(),
        selected_skill=None,
        no_wanted_skills=False,
        invalid_skill=False,
    ):
        super().__init__(matches)
        self.page_obj = page_obj
        self.wanted_skills = list(wanted_skills)
        self.selected_skill = selected_skill
        self.no_wanted_skills = no_wanted_skills
        self.invalid_skill = invalid_skill


def discover_members(*, search='', offered_skill=None, wanted_skill=None, exclude_user=None):
    """Return database-filtered public members with prefetched skill data."""
    members = User.objects.filter(is_active=True)
    if exclude_user is not None and getattr(exclude_user, 'is_authenticated', False):
        members = members.exclude(pk=exclude_user.pk)
    if search:
        members = members.filter(name__icontains=search)
    if offered_skill is not None:
        members = members.filter(offered_skills=offered_skill)
    if wanted_skill is not None:
        members = members.filter(wanted_skills=wanted_skill)

    return members.annotate(
        offered_skill_count=Count('offered_skills', distinct=True),
        wanted_skill_count=Count('wanted_skills', distinct=True),
    ).prefetch_related(
        'offered_skills',
        'wanted_skills',
    ).order_by('name', 'pk').distinct()


def _empty_match_results(*, wanted_skills=(), page=1, limit=9, selected_skill=None, invalid_skill=False):
    page_obj = Paginator([], limit).get_page(page)
    return MatchResults(
        [],
        page_obj=page_obj,
        wanted_skills=wanted_skills,
        selected_skill=selected_skill,
        no_wanted_skills=not wanted_skills,
        invalid_skill=invalid_skill,
    )


def get_match_results(user, skill_id=None, page=1, limit=9):
    """Return ranked, paginated candidates for the authenticated user.

    The database first narrows candidates to people offering a wanted skill.
    Overlaps and scores are calculated from prefetched relationships, avoiding
    one or more database queries per candidate.
    """
    try:
        limit = max(1, int(limit))
    except (TypeError, ValueError):
        limit = 9
    if not getattr(user, 'is_authenticated', False) or not getattr(user, 'pk', None):
        return _empty_match_results(page=page, limit=limit)

    wanted_skills = list(user.wanted_skills.all().order_by('name', 'pk'))
    offered_skills = list(user.offered_skills.all().order_by('name', 'pk'))
    wanted_ids = {skill.pk for skill in wanted_skills}
    offered_ids = {skill.pk for skill in offered_skills}

    if not wanted_ids:
        return _empty_match_results(wanted_skills=wanted_skills, page=page, limit=limit)

    selected_skill = None
    if skill_id not in (None, ''):
        try:
            selected_skill_id = int(skill_id)
        except (TypeError, ValueError):
            return _empty_match_results(
                wanted_skills=wanted_skills,
                page=page,
                limit=limit,
                invalid_skill=True,
            )
        selected_skill = next((skill for skill in wanted_skills if skill.pk == selected_skill_id), None)
        if selected_skill is None:
            return _empty_match_results(
                wanted_skills=wanted_skills,
                page=page,
                limit=limit,
                invalid_skill=True,
            )
        wanted_ids = {selected_skill.pk}

    candidates = (
        User.objects.filter(is_active=True, offered_skills__in=wanted_ids)
        .exclude(pk=user.pk)
        .distinct()
        .prefetch_related(
            Prefetch('offered_skills', to_attr='_match_offered_skills'),
            Prefetch('wanted_skills', to_attr='_match_wanted_skills'),
        )
    )

    ranked = []
    for candidate in candidates:
        candidate_offered = list(getattr(candidate, '_match_offered_skills', ()))
        candidate_wanted = list(getattr(candidate, '_match_wanted_skills', ()))
        skills_you_want = [skill for skill in candidate_offered if skill.pk in wanted_ids]
        skills_they_want = [skill for skill in candidate_wanted if skill.pk in offered_ids]
        if not skills_you_want:
            continue

        candidate.request_skills_json = json.dumps(
            [{'id': skill.pk, 'name': skill.name} for skill in candidate_offered],
        )
        candidate.initials = get_user_initials(candidate.name)
        ranked.append({
            'candidate': candidate,
            'candidate_name': candidate.name,
            'candidate_bio': candidate.bio,
            'candidate_offered_skills': candidate_offered,
            'candidate_wanted_skills': candidate_wanted,
            'skills_you_want': skills_you_want,
            'skills_they_want': skills_they_want,
            'score': len(skills_you_want) + len(skills_they_want),
            'is_two_way_match': bool(skills_you_want and skills_they_want),
        })

    ranked.sort(key=lambda result: (
        -result['score'],
        result['candidate_name'].casefold(),
        result['candidate'].pk,
    ))
    page_obj = Paginator(ranked, limit).get_page(page)
    return MatchResults(
        list(page_obj.object_list),
        page_obj=page_obj,
        wanted_skills=wanted_skills,
        selected_skill=selected_skill,
    )

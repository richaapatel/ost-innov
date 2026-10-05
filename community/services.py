from django.contrib.auth import get_user_model
from django.db.models import Count


User = get_user_model()


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

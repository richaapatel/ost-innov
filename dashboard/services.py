from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from community.services import get_match_results
from exchanges.models import Exchange
from skills.models import Skill


User = get_user_model()


def _positive_limit(limit, default=3):
    try:
        return max(1, int(limit))
    except (TypeError, ValueError):
        return default


def get_dashboard_user(user):
    """Load the public profile data used across the dashboard in two prefetches."""
    return User.objects.prefetch_related(
        'offered_skills',
        'wanted_skills',
    ).get(pk=user.pk)


def get_dashboard_statistics(user):
    """Return statistics scoped to the authenticated user."""
    counts = User.objects.filter(pk=user.pk).annotate(
        offered_count=Count('offered_skills', distinct=True),
        wanted_count=Count('wanted_skills', distinct=True),
    ).values('offered_count', 'wanted_count').get()
    pending_count = Exchange.objects.filter(
        Q(teacher_id=user.pk) | Q(learner_id=user.pk),
        status=Exchange.Status.PENDING,
    ).count()
    return {
        'offered_count': counts['offered_count'],
        'wanted_count': counts['wanted_count'],
        'pending_count': pending_count,
    }


def get_dashboard_matches(user, limit=3):
    """Reuse the community matching algorithm for the dashboard preview."""
    results = get_match_results(user, page=1, limit=_positive_limit(limit))
    return list(results)


def get_recent_received_requests(user, limit=2):
    return Exchange.objects.filter(teacher_id=user.pk).select_related(
        'teacher',
        'learner',
        'skill',
    ).order_by('-created_at', '-pk')[:_positive_limit(limit, default=2)]


def get_recent_sent_requests(user, limit=2):
    return Exchange.objects.filter(learner_id=user.pk).select_related(
        'teacher',
        'learner',
        'skill',
    ).order_by('-created_at', '-pk')[:_positive_limit(limit, default=2)]


def get_skill_demand_data(limit=5):
    """Return the most requested skill categories across the community."""
    limit = _positive_limit(limit, default=5)
    rows = (
        Skill.objects.values('category')
        .annotate(request_count=Count('learners', distinct=True))
        .filter(request_count__gt=0)
        .order_by('-request_count', 'category')[:limit]
    )
    return [
        {
            'label': row['category'] or 'Uncategorized',
            'count': row['request_count'],
        }
        for row in rows
    ]


def get_skill_demand_summary(data=None):
    data = get_skill_demand_data() if data is None else data
    if not data:
        return 'There is no skill demand data yet. Add learning goals to help shape the community.'
    return f"{data[0]['label']} is currently the most requested skill category in the community."


def get_exchange_status_counts(user):
    """Return this user's exchange status totals, including zero statuses."""
    counts = {status: 0 for status, _ in Exchange.Status.choices}
    rows = (
        Exchange.objects.filter(Q(teacher_id=user.pk) | Q(learner_id=user.pk))
        .values('status')
        .annotate(total=Count('pk'))
    )
    for row in rows:
        if row['status'] in counts:
            counts[row['status']] = row['total']
    return counts


def get_exchange_status_summary(counts):
    total = sum(counts.values())
    if not total:
        return 'There are currently no exchange requests.'
    return f"You have {total} exchange request{'s' if total != 1 else ''} across all statuses."

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.utils import get_user_initials

from .analytics import build_exchange_status_figure, build_skill_demand_figure, figure_to_png_response
from .services import (
    get_dashboard_matches,
    get_dashboard_statistics,
    get_dashboard_user,
    get_exchange_status_counts,
    get_exchange_status_summary,
    get_recent_received_requests,
    get_recent_sent_requests,
    get_skill_demand_data,
    get_skill_demand_summary,
)


@login_required
def index(request):
    dashboard_user = get_dashboard_user(request.user)
    dashboard_user.initials = get_user_initials(dashboard_user.name)
    skill_demand = get_skill_demand_data()
    exchange_statuses = get_exchange_status_counts(dashboard_user)
    return render(request, 'dashboard/index.html', {
        'dashboard_user': dashboard_user,
        'first_name': (dashboard_user.name.strip().split() or ['there'])[0],
        'statistics': get_dashboard_statistics(dashboard_user),
        'matches': get_dashboard_matches(dashboard_user, limit=3),
        'received_requests': get_recent_received_requests(dashboard_user, limit=2),
        'sent_requests': get_recent_sent_requests(dashboard_user, limit=2),
        'skill_demand_summary': get_skill_demand_summary(skill_demand),
        'exchange_status_summary': get_exchange_status_summary(exchange_statuses),
    })


@login_required
def skill_demand_chart(request):
    return figure_to_png_response(build_skill_demand_figure(get_skill_demand_data()))


@login_required
def exchange_status_chart(request):
    return figure_to_png_response(
        build_exchange_status_figure(get_exchange_status_counts(request.user)),
    )

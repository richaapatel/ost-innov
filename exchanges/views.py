from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ExchangeRequestForm
from .models import Exchange
from .services import ExchangeServiceError, change_exchange_status, create_exchange_request


User = get_user_model()


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _form_errors(form):
    return {field: [str(error) for error in errors] for field, errors in form.errors.items()}


def _service_error_response(request, error, *, duplicate=False, status_code=400):
    message = error.messages[0] if getattr(error, 'messages', None) else str(error)
    if _is_ajax(request):
        return JsonResponse(
            {'ok': False, 'message': message, 'errors': {}},
            status=409 if duplicate else status_code,
        )
    messages.error(request, message)
    return redirect(request.POST.get('next') or 'community:discover')


@login_required
def exchange_list(request):
    received = (
        Exchange.objects.filter(teacher=request.user)
        .select_related('teacher', 'learner', 'skill')
        .order_by('-created_at', '-pk')
    )
    sent = (
        Exchange.objects.filter(learner=request.user)
        .select_related('teacher', 'learner', 'skill')
        .order_by('-created_at', '-pk')
    )
    return render(request, 'exchanges/list.html', {
        'received_exchanges': received,
        'sent_exchanges': sent,
        'active_tab': request.GET.get('tab', 'received'),
    })


@login_required
def exchange_detail(request, exchange_id):
    exchange = get_object_or_404(
        Exchange.objects.select_related('teacher', 'learner', 'skill'),
        pk=exchange_id,
    )
    if request.user.pk not in (exchange.teacher_id, exchange.learner_id):
        return HttpResponseForbidden('You do not have access to this exchange.')
    return render(request, 'exchanges/detail.html', {'exchange': exchange})


@login_required
def exchange_create(request):
    if request.method not in ('GET', 'POST'):
        raise Http404
    initial = {'teacher_id': request.GET.get('teacher_id')} if request.method == 'GET' else None
    form = ExchangeRequestForm(request.POST or None, initial=initial)
    if request.method == 'POST':
        if not form.is_valid():
            if _is_ajax(request):
                return JsonResponse({
                    'ok': False,
                    'message': 'Please correct the highlighted fields.',
                    'errors': _form_errors(form),
                }, status=400)
            return render(request, 'exchanges/create.html', {'form': form})
        try:
            exchange = create_exchange_request(
                learner=request.user,
                teacher_id=form.cleaned_data['teacher_id'],
                skill_id=form.cleaned_data['skill_id'].pk,
                message=form.cleaned_data['message'],
            )
        except ExchangeServiceError as error:
            duplicate = 'pending request already exists' in str(error).lower()
            return _service_error_response(request, error, duplicate=duplicate)
        if _is_ajax(request):
            return JsonResponse({
                'ok': True,
                'message': 'Learning request sent successfully.',
                'data': {
                    'exchange_id': exchange.pk,
                    'skill': exchange.skill.name,
                    'status': exchange.status,
                },
            })
        messages.success(request, 'Learning request sent successfully.')
        return redirect('exchanges:detail', exchange_id=exchange.pk)
    teacher = None
    if initial and initial.get('teacher_id'):
        try:
            teacher = User.objects.filter(pk=int(initial['teacher_id']), is_active=True).first()
        except (TypeError, ValueError):
            teacher = None
    return render(request, 'exchanges/create.html', {
        'form': form,
        'teacher': teacher,
        'next_url': request.GET.get('next', ''),
    })


def _change_status(request, exchange_id, action):
    exchange = get_object_or_404(Exchange, pk=exchange_id)
    try:
        updated = change_exchange_status(exchange=exchange, actor=request.user, action=action)
    except ExchangeServiceError as error:
        message = error.messages[0] if getattr(error, 'messages', None) else str(error)
        return _service_error_response(request, error, status_code=403 if message.startswith('Only ') else 400)
    if _is_ajax(request):
        return JsonResponse({
            'ok': True,
            'message': 'Exchange status updated.',
            'data': {'exchange_id': updated.pk, 'status': updated.status},
        })
    messages.success(request, 'Exchange status updated.')
    return redirect('exchanges:detail', exchange_id=updated.pk)


@login_required
@require_POST
def accept_exchange(request, exchange_id):
    return _change_status(request, exchange_id, 'accept')


@login_required
@require_POST
def reject_exchange(request, exchange_id):
    return _change_status(request, exchange_id, 'reject')


@login_required
@require_POST
def complete_exchange(request, exchange_id):
    return _change_status(request, exchange_id, 'complete')

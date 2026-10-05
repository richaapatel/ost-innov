from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

def health_check(request):
    return JsonResponse({"status": "ok"})

def home(request):
    return render(request, 'core/home.html')


@login_required
def protected(request):
    return JsonResponse({'status': 'authenticated'})

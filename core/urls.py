from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('health/', views.health_check, name='health'),
    path('protected/', views.protected, name='protected'),
    path('', views.home, name='home'),
]

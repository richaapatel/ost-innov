from django.urls import path

from . import views

app_name = 'exchanges'

urlpatterns = [
    path('', views.exchange_list, name='list'),
    path('<int:exchange_id>/', views.exchange_detail, name='detail'),
    path('create/', views.exchange_create, name='create'),
    path('<int:exchange_id>/accept/', views.accept_exchange, name='accept'),
    path('<int:exchange_id>/reject/', views.reject_exchange, name='reject'),
    path('<int:exchange_id>/complete/', views.complete_exchange, name='complete'),
]

from django.urls import path

from . import views


app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('charts/skill-demand.png', views.skill_demand_chart, name='skill_demand_chart'),
    path('charts/exchange-status.png', views.exchange_status_chart, name='exchange_status_chart'),
]

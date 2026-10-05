from django.urls import path

from . import views


app_name = 'community'

urlpatterns = [
    path('discover/', views.discover, name='discover'),
    path('discover/matches/', views.matches, name='matches'),
    path('members/<int:user_id>/', views.member_detail, name='member_detail'),
]

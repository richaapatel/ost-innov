from django.urls import path

from . import views

app_name = 'skills'

urlpatterns = [
    path('skills/', views.skill_list, name='list'),
    path('skills/create/', views.skill_create, name='create'),
    path('skills/<int:skill_id>/offered/add/', views.add_offered, name='add_offered'),
    path('skills/<int:skill_id>/offered/remove/', views.remove_offered, name='remove_offered'),
    path('skills/<int:skill_id>/wanted/add/', views.add_wanted, name='add_wanted'),
    path('skills/<int:skill_id>/wanted/remove/', views.remove_wanted, name='remove_wanted'),
]

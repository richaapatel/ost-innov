from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('exchanges/', include('exchanges.urls')),
    path('', include('skills.urls')),
    path('', include('community.urls')),
    path('', include('core.urls')),
]

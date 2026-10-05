from django.contrib import admin

from .models import Exchange


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'teacher',
        'learner',
        'skill',
        'status',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'teacher__email',
        'teacher__name',
        'learner__email',
        'learner__name',
        'skill__name',
    )
    list_filter = ('status', 'skill', 'created_at')
    date_hierarchy = 'created_at'

from django.contrib import admin
from .models import TransferLog

@admin.register(TransferLog)
class TransferLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'fecha',
        'operador',
        'origen',
        'destino',
        'cantidad_pasajeros',
        'estado',
    )
    list_filter = ('estado', 'fecha')
    search_fields = ('reservas',)

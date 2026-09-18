from django.contrib import admin

from .models import MensajeContacto


@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'asunto', 'leido', 'created_at')
    list_filter = ('leido', 'created_at')
    readonly_fields = ('nombre', 'email', 'telefono', 'asunto', 'mensaje', 'created_at')

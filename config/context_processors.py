from django.conf import settings


def site_settings(request):
    context = {
        'whatsapp_number': settings.WHATSAPP_NUMBER,
        'whatsapp_message': settings.WHATSAPP_DEFAULT_MESSAGE,
        'maps_embed_url': settings.MAPS_EMBED_URL,
        # Versión de archivos estáticos: incrementar cuando cambie CSS/JS
        # para que el navegador descargue la versión nueva (cache busting).
        'static_version': '50',
    }
    if request.user.is_authenticated:
        from panel.decorators import es_admin
        from publico.models import MensajeContacto
        context['mensajes_sin_leer'] = MensajeContacto.objects.filter(leido=False).count()
        context['es_admin'] = es_admin(request.user)
    else:
        context['es_admin'] = False
    return context

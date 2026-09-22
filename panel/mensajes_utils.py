# Links mailto y WhatsApp desde la bandeja de mensajes.
import re
from urllib.parse import quote

from django.conf import settings


def normalizar_whatsapp(telefono):
    # Teléfono del formulario → dígitos para wa.me (51… si falta país).
    digitos = re.sub(r'\D', '', telefono or '')
    if not digitos:
        return ''

    pais = re.sub(r'\D', '', getattr(settings, 'WHATSAPP_COUNTRY_CODE', '51') or '51')

    if digitos.startswith('00'):
        digitos = digitos[2:]
    if digitos.startswith('0'):
        digitos = digitos.lstrip('0')

    if digitos.startswith(pais) and len(digitos) >= len(pais) + 8:
        return digitos

    # Móvil peruano típico: 9xxxxxxxx
    if len(digitos) == 9 and digitos[0] == '9':
        return f'{pais}{digitos}'

    # A veces dejan el número corto; le pegamos el código del .env
    if 7 <= len(digitos) <= 9:
        return f'{pais}{digitos}'

    if len(digitos) >= 10:
        return digitos

    return ''


def enlaces_respuesta_mensaje(mensaje):
    # (mailto, whatsapp) — whatsapp puede ser None si no hay teléfono usable.
    cuerpo = (
        f'Hola {mensaje.nombre},\n\n'
        f'Gracias por contactar a Granja Porkis.\n\n'
        f'---\n'
        f'Su consulta ({mensaje.created_at:%d/%m/%Y}):\n'
        f'{mensaje.mensaje}'
    )
    mailto = (
        f'mailto:{mensaje.email}'
        f'?subject={quote(f"Re: {mensaje.asunto}")}'
        f'&body={quote(cuerpo)}'
    )

    numero = normalizar_whatsapp(mensaje.telefono)
    wa_url = None
    if numero:
        texto = (
            f'Hola {mensaje.nombre}, gracias por escribirnos desde la web de Granja Porkis.\n\n'
            f'Su consulta sobre "{mensaje.asunto}" ({mensaje.created_at:%d/%m/%Y}):\n'
            f'{mensaje.mensaje}\n\n'
            f'Le respondemos:'
        )
        wa_url = f'https://wa.me/{numero}?text={quote(texto)}'

    return mailto, wa_url

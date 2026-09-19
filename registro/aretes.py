"""Generación de aretes por categoría (prefijo + correlativo)."""

import re
import unicodedata

from django.db import transaction

from .models import Cerdo, CorrelativoArete

_PREFIJO_SIN_CATEGORIA = 'SC'
_STOPWORDS = frozenset({'de', 'del', 'la', 'las', 'el', 'los', 'y', 'en', 'a', 'al'})


def _normalizar_texto(texto):
    texto = unicodedata.normalize('NFD', texto or '')
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.strip()


def _palabras_significativas(nombre):
    limpio = re.sub(r'[()[\]/,;]', ' ', _normalizar_texto(nombre))
    tokens = [t for t in limpio.split() if t]
    significativas = [t for t in tokens if t.lower() not in _STOPWORDS]
    return significativas or tokens


def prefijo_categoria(categoria):
    """
    Sin categoría → SC.
    Una palabra → dos primeras letras (Chanchilla → CH).
    Dos o más palabras → inicial de las dos primeras palabras significativas (Pie de cría → PC).
    """
    if categoria is None:
        return _PREFIJO_SIN_CATEGORIA

    palabras = _palabras_significativas(categoria.nombre)
    if not palabras:
        return _PREFIJO_SIN_CATEGORIA

    if len(palabras) >= 2:
        return (palabras[0][0] + palabras[1][0]).upper()

    palabra = palabras[0]
    if len(palabra) >= 2:
        return palabra[:2].upper()
    return (palabra[0] * 2).upper()


def _max_numero_en_aretes(prefijo):
    patron = re.compile(rf'^{re.escape(prefijo)}-(\d+)$', re.IGNORECASE)
    maximo = 0
    for arete in Cerdo.objects.filter(arete__istartswith=f'{prefijo}-').values_list('arete', flat=True):
        match = patron.match(arete)
        if match:
            maximo = max(maximo, int(match.group(1)))
    return maximo


def generar_arete(categoria=None):
    """Genera el siguiente arete, p. ej. CH-0001. Seguro ante concurrencia."""
    prefijo = prefijo_categoria(categoria)
    with transaction.atomic():
        correlativo, _ = (
            CorrelativoArete.objects
            .select_for_update()
            .get_or_create(prefijo=prefijo, defaults={'ultimo': 0})
        )
        max_existente = _max_numero_en_aretes(prefijo)
        if max_existente > correlativo.ultimo:
            correlativo.ultimo = max_existente
        correlativo.ultimo += 1
        correlativo.save(update_fields=['ultimo'])
        return f'{prefijo}-{correlativo.ultimo:04d}'


def remapear_arete_por_categoria(cerdo):
    """Asigna arete según la categoría actual (usado al cambiar categoría)."""
    cerdo.arete = generar_arete(cerdo.categoria)

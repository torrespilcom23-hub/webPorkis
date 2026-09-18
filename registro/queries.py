"""Consultas y filtros reutilizables para el stock de cerdos."""

from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import Cerdo, Corral


def _parse_decimal(val):
    if not val or not str(val).strip():
        return None
    try:
        return Decimal(str(val).strip().replace(',', '.'))
    except InvalidOperation:
        return None


def _parse_int(val):
    if not val or not str(val).strip():
        return None
    try:
        return int(val)
    except ValueError:
        return None


def filtrar_cerdos(params):
    """Aplica filtros GET sobre el queryset de cerdos. Retorna (qs, filtros dict)."""
    hoy = timezone.now().date()
    q = params.get('q', '').strip()
    sexo = params.get('sexo', '')
    categoria_id = params.get('categoria', '')
    raza = params.get('raza', '')
    corral_id = params.get('corral', '')
    edad = _parse_int(params.get('edad'))
    peso = _parse_decimal(params.get('peso'))
    sin_peso = params.get('sin_peso') == '1'
    sin_corral = params.get('sin_corral') == '1'
    ver_todos = params.get('ver_todos') == '1'
    estado = params.get('estado', '')

    # Por defecto: solo en granja en la primera visita (URL sin parámetros).
    # Si el usuario elige "Todos los estados" en el combo (estado=), mostrar todos.
    if 'estado' not in params and not ver_todos:
        estado = Cerdo.Estado.ACTIVO
    elif 'estado' in params and estado == '' and not ver_todos:
        ver_todos = True
        estado = ''

    cerdos = Cerdo.objects.select_related('lote', 'categoria', 'corral')
    if q:
        cerdos = cerdos.filter(
            Q(arete__icontains=q) | Q(nombre__icontains=q) | Q(raza__icontains=q)
            | Q(raza_otro__icontains=q)
        )
    if sexo:
        cerdos = cerdos.filter(sexo=sexo)
    if estado:
        cerdos = cerdos.filter(estado=estado)
    if raza:
        cerdos = cerdos.filter(raza=raza)
    if corral_id == 'sin':
        cerdos = cerdos.filter(corral__isnull=True)
    elif corral_id:
        cerdos = cerdos.filter(corral_id=corral_id)
    if categoria_id == 'sin':
        cerdos = cerdos.filter(categoria__isnull=True)
    elif categoria_id:
        cerdos = cerdos.filter(categoria_id=categoria_id)
    if edad is not None:
        if edad == 0:
            cerdos = cerdos.filter(fecha_nacimiento__gt=hoy - timedelta(days=30))
        else:
            cerdos = cerdos.filter(
                fecha_nacimiento__lte=hoy - timedelta(days=edad * 30),
                fecha_nacimiento__gt=hoy - timedelta(days=(edad + 1) * 30),
            )
    if peso is not None:
        cerdos = cerdos.filter(peso_actual=peso)
    if sin_peso:
        cerdos = cerdos.filter(peso_actual__isnull=True)
    if sin_corral:
        cerdos = cerdos.filter(corral__isnull=True)

    filtros = {
        'q': q,
        'sexo': sexo,
        'estado': estado,
        'categoria_id': categoria_id,
        'raza': raza,
        'corral_id': corral_id,
        'edad': params.get('edad', ''),
        'peso': params.get('peso', ''),
        'sin_peso': sin_peso,
        'sin_corral': sin_corral,
        'ver_todos': ver_todos,
    }
    return cerdos, filtros


def opciones_filtro_edad_peso():
    """Valores distintos de edad (meses) y peso (kg) para combos de filtro."""
    hoy = timezone.now().date()
    edades = set()
    for fn in Cerdo.objects.exclude(fecha_nacimiento__isnull=True).values_list(
        'fecha_nacimiento', flat=True,
    ):
        dias = (hoy - fn).days
        if dias >= 0:
            edades.add(dias // 30)
    pesos = list(
        Cerdo.objects.exclude(peso_actual__isnull=True)
        .values_list('peso_actual', flat=True)
        .distinct()
        .order_by('peso_actual')
    )
    return sorted(edades), pesos


def resumen_stock_activos():
    """Conteos de cerdos en granja por categoría, raza, sexo y corral."""
    base = Cerdo.objects.filter(estado=Cerdo.Estado.ACTIVO)
    hoy = timezone.now().date()

    conteos_categoria = (
        base.filter(categoria__isnull=False)
        .values('categoria_id', 'categoria__nombre')
        .annotate(total=Count('pk'))
        .order_by('categoria__nombre')
    )
    raza_labels = dict(Cerdo.Raza.choices)
    sexo_labels = dict(Cerdo.Sexo.choices)
    conteos_raza = [
        {
            'raza': row['raza'],
            'raza_nombre': raza_labels.get(row['raza'], row['raza']),
            'total': row['total'],
        }
        for row in base.values('raza').annotate(total=Count('pk')).order_by('raza')
    ]
    conteos_sexo = [
        {
            'sexo': row['sexo'],
            'sexo_nombre': sexo_labels.get(row['sexo'], row['sexo']),
            'total': row['total'],
        }
        for row in base.values('sexo').annotate(total=Count('pk'))
    ]
    conteos_corral = (
        base.filter(corral__isnull=False)
        .values('corral_id', 'corral__nombre')
        .annotate(total=Count('pk'))
        .order_by('corral__nombre')
    )
    sin_categoria = base.filter(categoria__isnull=True).count()
    sin_corral = base.filter(corral__isnull=True).count()
    sin_peso = base.filter(peso_actual__isnull=True).count()
    total_activos = base.count()
    total_vendidos = Cerdo.objects.filter(estado=Cerdo.Estado.VENDIDO).count()
    total_fallecidos = Cerdo.objects.filter(estado=Cerdo.Estado.FALLECIDO).count()
    peso_promedio = base.filter(peso_actual__isnull=False).aggregate(
        prom=Avg('peso_actual'),
    )['prom']

    return {
        'conteos_categoria': conteos_categoria,
        'conteos_raza': conteos_raza,
        'conteos_sexo': conteos_sexo,
        'conteos_corral': conteos_corral,
        'sin_categoria': sin_categoria,
        'sin_corral': sin_corral,
        'sin_peso': sin_peso,
        'total_activos': total_activos,
        'total_vendidos': total_vendidos,
        'total_fallecidos': total_fallecidos,
        'peso_promedio': peso_promedio,
        'corrales': Corral.objects.all(),
        'razas': Cerdo.Raza.choices,
        'hoy': hoy,
    }

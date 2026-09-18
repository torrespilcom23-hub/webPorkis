"""Consultas y filtros reutilizables para alimentos."""

from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import PlanAlimentacion, RegistroAlimentacion, TipoAlimento


def filtrar_registros(params):
    """Aplica filtros GET sobre consumo. Retorna (qs, filtros dict)."""
    q = params.get('q', '').strip()
    tipo_id = params.get('tipo', '')
    lote_id = params.get('lote', '')
    desde = params.get('desde', '').strip()
    hasta = params.get('hasta', '').strip()

    qs = RegistroAlimentacion.objects.select_related(
        'lote', 'tipo_alimento', 'registrado_por',
    )
    if q:
        qs = qs.filter(
            Q(lote__nombre__icontains=q)
            | Q(tipo_alimento__nombre__icontains=q)
            | Q(observaciones__icontains=q),
        )
    if tipo_id:
        qs = qs.filter(tipo_alimento_id=tipo_id)
    if lote_id:
        qs = qs.filter(lote_id=lote_id)
    if desde:
        qs = qs.filter(fecha__gte=desde)
    if hasta:
        qs = qs.filter(fecha__lte=hasta)

    filtros = {
        'q': q,
        'tipo_id': tipo_id,
        'lote_id': lote_id,
        'desde': desde,
        'hasta': hasta,
    }
    return qs, filtros


def filtrar_planes(params):
    """Aplica filtros GET sobre planes. Retorna (qs, filtros dict)."""
    q = params.get('q', '').strip()
    ver_todos = params.get('ver') == 'todos'

    qs = PlanAlimentacion.objects.select_related('lote', 'tipo_alimento')
    if not ver_todos:
        qs = qs.filter(activo=True)
    if q:
        qs = qs.filter(
            Q(lote__nombre__icontains=q)
            | Q(tipo_alimento__nombre__icontains=q),
        )

    return qs, {'q': q, 'ver_todos': ver_todos}


def resumen_alimentos():
    """Conteos para KPIs y pestañas del módulo."""
    hoy = timezone.now().date()
    mes_qs = RegistroAlimentacion.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month,
    )
    kg_mes = mes_qs.aggregate(total=Sum('cantidad_servida_kg'))['total']

    return {
        'total_tipos': TipoAlimento.objects.count(),
        'total_planes_activos': PlanAlimentacion.objects.filter(activo=True).count(),
        'total_planes': PlanAlimentacion.objects.count(),
        'total_registros': RegistroAlimentacion.objects.count(),
        'registros_mes': mes_qs.count(),
        'kg_servido_mes': kg_mes or 0,
        'tipos_catalogo': TipoAlimento.objects.annotate(
            num_planes=Count('planalimentacion', distinct=True),
        ).annotate(
            num_registros=Count('registroalimentacion', distinct=True),
        ),
        'hoy': hoy,
    }

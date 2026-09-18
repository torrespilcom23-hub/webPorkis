"""Consultas y filtros reutilizables para vacunas."""

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from registro.models import Cerdo

from .models import AplicacionVacuna, Vacuna

DIAS_ALERTA = 7


def filtrar_aplicaciones(params):
    """Aplica filtros GET sobre aplicaciones. Retorna (qs, filtros dict)."""
    hoy = timezone.now().date()
    limite = hoy + timedelta(days=DIAS_ALERTA)
    q = params.get('q', '').strip()
    vacuna_id = params.get('vacuna', '')
    desde = params.get('desde', '').strip()
    hasta = params.get('hasta', '').strip()
    vista = params.get('vista', 'historial')

    qs = AplicacionVacuna.objects.select_related('cerdo', 'vacuna', 'responsable')
    activos = Q(cerdo__estado=Cerdo.Estado.ACTIVO)

    if q:
        qs = qs.filter(
            Q(cerdo__arete__icontains=q)
            | Q(cerdo__nombre__icontains=q)
            | Q(vacuna__nombre__icontains=q),
        )
    if vacuna_id:
        qs = qs.filter(vacuna_id=vacuna_id)
    if desde:
        qs = qs.filter(fecha_aplicacion__gte=desde)
    if hasta:
        qs = qs.filter(fecha_aplicacion__lte=hasta)

    if vista == 'vencidas':
        qs = qs.filter(activos, proxima_dosis__isnull=False, proxima_dosis__lte=hoy)
    elif vista == 'proximas':
        qs = qs.filter(
            activos,
            proxima_dosis__isnull=False,
            proxima_dosis__gt=hoy,
            proxima_dosis__lte=limite,
        )

    filtros = {
        'q': q,
        'vacuna_id': vacuna_id,
        'desde': desde,
        'hasta': hasta,
        'vista': vista,
    }
    return qs, filtros


def resumen_vacunas():
    """Conteos para KPIs y pestañas del módulo."""
    hoy = timezone.now().date()
    limite = hoy + timedelta(days=DIAS_ALERTA)
    activos = Q(cerdo__estado=Cerdo.Estado.ACTIVO)
    base_activos = AplicacionVacuna.objects.filter(activos)

    return {
        'total_aplicaciones': AplicacionVacuna.objects.count(),
        'total_catalogo': Vacuna.objects.count(),
        'vencidas': base_activos.filter(
            proxima_dosis__isnull=False, proxima_dosis__lte=hoy,
        ).count(),
        'proximas_7d': base_activos.filter(
            proxima_dosis__isnull=False,
            proxima_dosis__gt=hoy,
            proxima_dosis__lte=limite,
        ).count(),
        'alertas_total': base_activos.filter(
            proxima_dosis__isnull=False,
            proxima_dosis__lte=limite,
        ).count(),
        'aplicaciones_mes': AplicacionVacuna.objects.filter(
            fecha_aplicacion__year=hoy.year,
            fecha_aplicacion__month=hoy.month,
        ).count(),
        'vacunas_catalogo': Vacuna.objects.annotate(
            num_aplicaciones=Count('aplicacionvacuna'),
        ),
        'hoy': hoy,
        'limite_alerta': limite,
        'dias_alerta': DIAS_ALERTA,
    }

"""Consultas y filtros reutilizables para inseminación."""

from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from registro.models import Cerdo

from .models import DiagnosticoPrenez, Inseminacion, Padrillo, Parto, DIAS_DIAGNOSTICO


def _limite_diagnostico(hoy=None):
    hoy = hoy or timezone.now().date()
    return hoy - timedelta(days=DIAS_DIAGNOSTICO)


def filtrar_inseminaciones(params):
    """Aplica filtros GET sobre inseminaciones. Retorna (qs, filtros dict)."""
    hoy = timezone.now().date()
    limite = _limite_diagnostico(hoy)
    q = params.get('q', '').strip()
    tipo = params.get('tipo', '')
    padrillo_id = params.get('padrillo', '')
    desde = params.get('desde', '').strip()
    hasta = params.get('hasta', '').strip()
    vista = params.get('vista', 'historial')
    resultado = params.get('resultado', '')

    qs = Inseminacion.objects.select_related(
        'cerda', 'padrillo', 'responsable', 'diagnostico',
    ).prefetch_related('partos')

    if q:
        qs = qs.filter(
            Q(cerda__arete__icontains=q)
            | Q(cerda__nombre__icontains=q)
            | Q(padrillo__codigo__icontains=q),
        )
    if tipo:
        qs = qs.filter(tipo=tipo)
    if padrillo_id:
        qs = qs.filter(padrillo_id=padrillo_id)
    if desde:
        qs = qs.filter(fecha__gte=desde)
    if hasta:
        qs = qs.filter(fecha__lte=hasta)

    if vista == 'pendientes':
        qs = qs.filter(fecha__lte=limite, diagnostico__isnull=True)
    elif resultado == 'sin':
        qs = qs.filter(diagnostico__isnull=True)
    elif resultado == 'preñadas':
        qs = qs.filter(
            diagnostico__resultado=DiagnosticoPrenez.Resultado.POSITIVO,
        ).annotate(num_partos=Count('partos')).filter(num_partos=0)
    elif resultado:
        qs = qs.filter(diagnostico__resultado=resultado)

    filtros = {
        'q': q,
        'tipo': tipo,
        'padrillo_id': padrillo_id,
        'desde': desde,
        'hasta': hasta,
        'vista': vista,
        'resultado': resultado,
    }
    return qs, filtros


def filtrar_partos(params):
    """Aplica filtros GET sobre partos. Retorna (qs, filtros dict)."""
    q = params.get('q', '').strip()
    desde = params.get('desde', '').strip()
    hasta = params.get('hasta', '').strip()

    qs = Parto.objects.select_related(
        'inseminacion__cerda',
        'inseminacion__padrillo',
        'inseminacion__diagnostico',
    ).annotate(
        num_lechones_reg=Count('lechones_registrados'),
    )

    if q:
        qs = qs.filter(
            Q(inseminacion__cerda__arete__icontains=q)
            | Q(inseminacion__cerda__nombre__icontains=q),
        )
    if desde:
        qs = qs.filter(fecha__gte=desde)
    if hasta:
        qs = qs.filter(fecha__lte=hasta)

    filtros = {'q': q, 'desde': desde, 'hasta': hasta}
    return qs, filtros


def resumen_inseminacion():
    """Conteos para KPIs y pestañas del módulo."""
    hoy = timezone.now().date()
    limite = _limite_diagnostico(hoy)
    inicio_mes = hoy.replace(day=1)

    partos_mes = Parto.objects.filter(
        fecha__year=hoy.year,
        fecha__month=hoy.month,
    )
    lechones_mes = partos_mes.aggregate(
        total=Sum('lechones_vivos'),
    )['total'] or 0

    return {
        'total_inseminaciones': Inseminacion.objects.count(),
        'inseminaciones_mes': Inseminacion.objects.filter(
            fecha__year=hoy.year,
            fecha__month=hoy.month,
        ).count(),
        'pendientes_diagnostico': Inseminacion.objects.filter(
            fecha__lte=limite,
            diagnostico__isnull=True,
        ).count(),
        'total_partos': Parto.objects.count(),
        'partos_mes': partos_mes.count(),
        'lechones_nacidos_mes': lechones_mes,
        'total_padrillos': Padrillo.objects.count(),
        'padrillos_bajo_stock': Padrillo.objects.filter(stock_pajuelas__lte=2).count(),
        'preñadas_activas': Inseminacion.objects.filter(
            diagnostico__resultado=DiagnosticoPrenez.Resultado.POSITIVO,
        ).annotate(num_partos=Count('partos')).filter(num_partos=0).count(),
        'padrillos_catalogo': Padrillo.objects.annotate(
            num_inseminaciones=Count('inseminacion'),
        ),
        'hoy': hoy,
        'limite_diagnostico': limite,
        'dias_diagnostico': DIAS_DIAGNOSTICO,
        'dias_gestacion': 114,
    }

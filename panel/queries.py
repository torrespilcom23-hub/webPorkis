"""Datos consolidados del dashboard principal del panel."""

from django.db.models import Count, F, Q

from alimentos.models import RegistroAlimentacion
from alimentos.queries import resumen_alimentos
from inseminacion.models import Inseminacion
from inseminacion.queries import resumen_inseminacion
from inventario.models import Producto
from publico.models import MensajeContacto
from registro.models import Cerdo, Corral
from registro.queries import resumen_stock_activos
from vacunas.models import AplicacionVacuna
from vacunas.queries import resumen_vacunas


def resumen_dashboard():
    """Métricas y listas del dashboard, alineadas con los módulos operativos."""
    stock = resumen_stock_activos()
    vacunas = resumen_vacunas()
    repro = resumen_inseminacion()
    alimentos = resumen_alimentos()
    hoy = stock['hoy']
    limite_vacunas = vacunas['limite_alerta']

    activos_vacuna = Q(cerdo__estado=Cerdo.Estado.ACTIVO)
    alertas_vacunas = (
        AplicacionVacuna.objects
        .filter(
            activos_vacuna,
            proxima_dosis__isnull=False,
            proxima_dosis__lte=limite_vacunas,
        )
        .select_related('cerdo', 'vacuna')
        .order_by('proxima_dosis')[:5]
    )

    alertas_stock = (
        Producto.objects
        .filter(stock_actual__lte=F('stock_minimo'))
        .order_by('stock_actual')[:5]
    )

    alertas_diagnostico = (
        Inseminacion.objects
        .filter(
            fecha__lte=repro['limite_diagnostico'],
            diagnostico__isnull=True,
        )
        .select_related('cerda')
        .order_by('fecha')[:5]
    )

    stock_por_corral = (
        Corral.objects
        .annotate(total=Count('cerdos', filter=Q(cerdos__estado=Cerdo.Estado.ACTIVO)))
        .filter(total__gt=0)
        .order_by('-total')[:8]
    )

    cerdos_sin_peso_lista = list(
        Cerdo.objects
        .filter(estado=Cerdo.Estado.ACTIVO, peso_actual__isnull=True)
        .order_by('arete')[:5]
        .values('pk', 'arete', 'nombre')
    )

    inseminaciones_recientes = (
        Inseminacion.objects
        .select_related('cerda', 'padrillo', 'diagnostico')
        .order_by('-fecha', '-pk')[:3]
    )

    registros_alimentacion = (
        RegistroAlimentacion.objects
        .select_related('lote', 'tipo_alimento')
        .order_by('-fecha', '-pk')[:3]
    )

    productos_stock_bajo = Producto.objects.filter(
        stock_actual__lte=F('stock_minimo'),
    ).count()
    mensajes_nuevos = MensajeContacto.objects.filter(leido=False).count()

    data = {
        'hoy': hoy,
        'dias_diagnostico': repro['dias_diagnostico'],
        'dias_alerta_vacunas': vacunas['dias_alerta'],
        # Stock / registro
        'total_activos': stock['total_activos'],
        'sin_corral': stock['sin_corral'],
        'sin_categoria': stock['sin_categoria'],
        'sin_peso': stock['sin_peso'],
        'peso_promedio': stock['peso_promedio'],
        'conteos_categoria': stock['conteos_categoria'],
        'stock_por_corral': stock_por_corral,
        'cerdos_sin_peso_lista': cerdos_sin_peso_lista,
        'cerdos_sin_peso_extra': max(0, stock['sin_peso'] - len(cerdos_sin_peso_lista)),
        # Inventario
        'productos_stock_bajo': productos_stock_bajo,
        'alertas_stock': alertas_stock,
        # Vacunas (solo cerdos activos, misma lógica que módulo Vacunas)
        'vacunas_vencidas': vacunas['vencidas'],
        'vacunas_proximas': vacunas['proximas_7d'],
        'vacunas_alertas': vacunas['alertas_total'],
        'alertas_vacunas': alertas_vacunas,
        # Reproducción
        'partos_mes': repro['partos_mes'],
        'lechones_nacidos_mes': repro['lechones_nacidos_mes'],
        'inseminaciones_mes': repro['inseminaciones_mes'],
        'pendientes_diagnostico': repro['pendientes_diagnostico'],
        'preñadas_activas': repro['preñadas_activas'],
        'padrillos_bajo_stock': repro['padrillos_bajo_stock'],
        'alertas_diagnostico': alertas_diagnostico,
        'inseminaciones_recientes': inseminaciones_recientes,
        # Alimentos
        'registros_alimentacion_mes': alimentos['registros_mes'],
        'kg_servido_mes': alimentos['kg_servido_mes'],
        'registros_alimentacion': registros_alimentacion,
        # Contacto
        'mensajes_nuevos': mensajes_nuevos,
    }

    data['panel_alert_corral'] = data['sin_corral'] > 0
    data['panel_alert_categoria'] = data['sin_categoria'] > 0
    data['panel_alert_sin_peso'] = data['sin_peso'] > 0
    data['panel_alert_stock'] = data['productos_stock_bajo'] > 0
    data['panel_alert_vacunas'] = data['vacunas_alertas'] > 0
    data['panel_alert_alimentacion'] = False
    data['panel_alert_repro'] = (
        data['pendientes_diagnostico'] > 0
        or data['padrillos_bajo_stock'] > 0
    )
    data['dashboard_any_alert'] = any([
        data['panel_alert_corral'],
        data['panel_alert_categoria'],
        data['panel_alert_sin_peso'],
        data['panel_alert_stock'],
        data['panel_alert_vacunas'],
        data['panel_alert_repro'],
        mensajes_nuevos > 0,
    ])
    return data

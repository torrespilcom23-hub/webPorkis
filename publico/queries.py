"""Datos operativos de la granja para el sitio web público."""

from django.db.models import Count, Q
from django.utils import timezone

from registro.models import CategoriaCerdo, Cerdo, Lote

SERVICIOS_PUBLICOS = [
    {
        'titulo': 'Venta de lechones',
        'descripcion': (
            'Lechones registrados desde partos en la granja, con trazabilidad '
            'de madre, lote y vacunas aplicadas.'
        ),
        'beneficios': (
            'Alta desde partos en Inseminación\n'
            'Arete y genealogía en Registro\n'
            'Control sanitario con Vacunas\n'
            'Lotes y corral identificados'
        ),
        'icono': '🐖',
    },
    {
        'titulo': 'Engorde en granja',
        'descripcion': (
            'Cerdos en engorde con lotes, pesajes, raciones diarias '
            'y consumo de alimento registrado en el panel.'
        ),
        'beneficios': (
            'Lotes y corrales en Registro\n'
            'Pesajes y seguimiento de peso\n'
            'Raciones y consumo en Alimentos\n'
            'Reportes de producción'
        ),
        'icono': '📈',
    },
    {
        'titulo': 'Sanidad y vacunas',
        'descripcion': (
            'Protocolo sanitario con catálogo de vacunas, aplicaciones '
            'por cerdo y alertas de refuerzos pendientes.'
        ),
        'beneficios': (
            'Catálogo de vacunas\n'
            'Historial por animal\n'
            'Refuerzos y vencimientos\n'
            'Reporte sanitario exportable'
        ),
        'icono': '💉',
    },
    {
        'titulo': 'Reproducción e inseminación',
        'descripcion': (
            'Control reproductivo: padrillos, inseminaciones, diagnóstico '
            'de preñez, partos y alta de lechones al Registro.'
        ),
        'beneficios': (
            'Catálogo de padrillos\n'
            'Diagnóstico a los 21 días\n'
            'Registro de partos\n'
            'Alta de camadas en Registro'
        ),
        'icono': '🧬',
    },
]


def servicios_para_plantilla():
    return [
        {
            **servicio,
            'beneficios_lista': [
                linea.strip()
                for linea in servicio['beneficios'].splitlines()
                if linea.strip()
            ],
        }
        for servicio in SERVICIOS_PUBLICOS
    ]


def _categoria(nombre):
    return CategoriaCerdo.objects.filter(nombre__iexact=nombre).first()


def resumen_operacion():
    """Conteos reales para cifras del sitio público."""
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    activos = Cerdo.objects.filter(estado=Cerdo.Estado.ACTIVO)
    cat_lechon = _categoria('Lechón')
    cat_engorde = _categoria('Engorde')

    from inseminacion.models import DiagnosticoPrenez, Inseminacion, Padrillo, Parto
    from vacunas.models import AplicacionVacuna, Vacuna

    preñadas = Inseminacion.objects.filter(
        diagnostico__resultado=DiagnosticoPrenez.Resultado.POSITIVO,
    ).annotate(num_partos=Count('partos')).filter(num_partos=0).count()

    return {
        'cerdos_activos': activos.count(),
        'lechones': activos.filter(categoria=cat_lechon).count() if cat_lechon else 0,
        'engorde': activos.filter(categoria=cat_engorde).count() if cat_engorde else 0,
        'lotes_activos': Lote.objects.annotate(
            n=Count('cerdos', filter=Q(cerdos__estado=Cerdo.Estado.ACTIVO)),
        ).filter(n__gt=0).count(),
        'vacunas_cat': Vacuna.objects.count(),
        'aplicaciones_mes': AplicacionVacuna.objects.filter(
            fecha_aplicacion__gte=inicio_mes,
        ).count(),
        'padrillos': Padrillo.objects.count(),
        'preñadas': preñadas,
        'partos_mes': Parto.objects.filter(
            fecha__year=hoy.year,
            fecha__month=hoy.month,
        ).count(),
        'inseminaciones_mes': Inseminacion.objects.filter(
            fecha__gte=inicio_mes,
        ).count(),
    }

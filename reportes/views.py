from django.contrib.auth.decorators import login_required
from django.db.models import Count, F
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from alimentos.models import RegistroAlimentacion
from inseminacion.models import Parto
from inventario.models import CategoriaProducto, Producto
from registro.models import CategoriaCerdo, Cerdo, Corral
from registro.queries import filtrar_cerdos, opciones_filtro_edad_peso
from vacunas.models import AplicacionVacuna, Vacuna
from vacunas.queries import filtrar_aplicaciones

from .utils import exportar_excel, exportar_pdf


REPORTES = {
    'inventario': {
        'nombre': 'Inventario de insumos',
        'descripcion': 'Stock de productos, materiales y medicamentos del almacén.',
        'icono': '📦',
    },
    'produccion': {
        'nombre': 'Cerdos en granja',
        'descripcion': 'Animales activos con edad, peso, corral y categoría. Exportable para inventario animal.',
        'icono': '🐖',
    },
    'sanitario': {
        'nombre': 'Sanitario (vacunas)',
        'descripcion': 'Historial de vacunaciones aplicadas a los cerdos.',
        'icono': '💉',
    },
    'alimentacion': {
        'nombre': 'Alimentación',
        'descripcion': 'Consumo diario de alimento por lote.',
        'icono': '🌾',
    },
    'reproductivo': {
        'nombre': 'Reproductivo',
        'descripcion': 'Partos registrados: camadas, nacidos vivos y origen de la inseminación.',
        'icono': '🧬',
    },
}


def _filtrar_fechas(qs, campo, params):
    desde = params.get('desde', '').strip()
    hasta = params.get('hasta', '').strip()
    if desde:
        qs = qs.filter(**{f'{campo}__gte': desde})
    if hasta:
        qs = qs.filter(**{f'{campo}__lte': hasta})
    return qs


def _conteo_reporte(tipo):
    """Conteo rápido para la tarjeta del índice."""
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    if tipo == 'inventario':
        return Producto.objects.count()
    if tipo == 'produccion':
        return Cerdo.objects.filter(estado=Cerdo.Estado.ACTIVO).count()
    if tipo == 'sanitario':
        return AplicacionVacuna.objects.count()
    if tipo == 'alimentacion':
        return RegistroAlimentacion.objects.filter(fecha__gte=inicio_mes).count()
    if tipo == 'reproductivo':
        return Parto.objects.filter(fecha__gte=inicio_mes).count()
    return 0


def _conteo_etiqueta(tipo):
    if tipo == 'produccion':
        return 'en granja'
    if tipo in ('alimentacion', 'reproductivo'):
        return 'este mes'
    return 'registros'


def _get_datos(tipo, params):
    """Retorna (titulo, encabezados, filas) aplicando filtros GET."""
    meta = REPORTES.get(tipo)
    if not meta:
        return None, [], []

    if tipo == 'inventario':
        qs = Producto.objects.all()
        categoria = params.get('categoria')
        if categoria:
            qs = qs.filter(categoria=categoria)
        encabezados = ['Código', 'Nombre', 'Categoría', 'Stock', 'Mínimo', 'Unidad', 'Estado']
        filas = []
        for p in qs:
            bajo = p.stock_actual <= p.stock_minimo
            filas.append([
                p.codigo,
                p.nombre,
                p.get_categoria_display(),
                float(p.stock_actual),
                float(p.stock_minimo),
                p.unidad,
                'Bajo mínimo' if bajo else 'OK',
            ])

    elif tipo == 'produccion':
        qs, _ = filtrar_cerdos(params)
        qs = qs.select_related('corral', 'categoria', 'lote')
        encabezados = [
            'Arete', 'Raza', 'Sexo', 'Edad', 'Peso (kg)',
            'Estado', 'Corral', 'Categoría', 'Lote',
        ]
        filas = [
            [
                c.arete,
                c.raza_display,
                c.get_sexo_display(),
                c.edad_display,
                float(c.peso_actual or 0) or '—',
                c.get_estado_display(),
                c.corral.nombre if c.corral else '—',
                c.categoria.nombre if c.categoria else '—',
                c.lote.nombre if c.lote else '—',
            ]
            for c in qs
        ]

    elif tipo == 'sanitario':
        qs, _ = filtrar_aplicaciones({**params, 'vista': 'historial'})
        encabezados = ['Cerdo', 'Vacuna', 'Fecha', 'Dosis', 'Próxima dosis', 'Responsable']
        filas = [
            [
                a.cerdo.arete,
                a.vacuna.nombre,
                a.fecha_aplicacion.strftime('%d/%m/%Y'),
                a.dosis,
                a.proxima_dosis.strftime('%d/%m/%Y') if a.proxima_dosis else '—',
                a.responsable.get_full_name() or a.responsable.username,
            ]
            for a in qs
        ]

    elif tipo == 'alimentacion':
        qs = _filtrar_fechas(
            RegistroAlimentacion.objects.select_related('lote', 'tipo_alimento'),
            'fecha', params,
        )
        encabezados = ['Fecha', 'Lote', 'Alimento', 'Servido (kg)', 'Sobrante (kg)']
        filas = [
            [
                r.fecha.strftime('%d/%m/%Y'),
                r.lote.nombre,
                r.tipo_alimento.nombre,
                float(r.cantidad_servida_kg),
                float(r.cantidad_sobrante_kg or 0),
            ]
            for r in qs
        ]

    elif tipo == 'reproductivo':
        qs = _filtrar_fechas(
            Parto.objects.select_related(
                'inseminacion__cerda',
                'inseminacion__padrillo',
            ).annotate(num_reg=Count('lechones_registrados')),
            'fecha', params,
        )
        encabezados = [
            'Cerda', 'Fecha parto', 'Vivos', 'Muertos', 'En Registro',
            'Tipo insem.', 'Padrillo',
        ]
        filas = [
            [
                p.inseminacion.cerda.arete,
                p.fecha.strftime('%d/%m/%Y'),
                p.lechones_vivos,
                p.lechones_muertos,
                f'{p.num_reg} / {p.lechones_vivos}',
                p.inseminacion.get_tipo_display(),
                p.inseminacion.padrillo.codigo if p.inseminacion.padrillo else '—',
            ]
            for p in qs
        ]

    else:
        return None, [], []

    return meta['nombre'], encabezados, filas


@login_required
def reportes_index(request):
    tarjetas = [
        {
            'key': key,
            'conteo': _conteo_reporte(key),
            'conteo_etiqueta': _conteo_etiqueta(key),
            **meta,
        }
        for key, meta in REPORTES.items()
    ]
    stock_bajo = Producto.objects.filter(stock_actual__lte=F('stock_minimo')).count()
    return render(request, 'panel/reportes/index.html', {
        'tarjetas': tarjetas,
        'stock_bajo': stock_bajo,
    })


@login_required
def reporte_ver(request, tipo):
    if tipo not in REPORTES:
        raise Http404

    meta = REPORTES[tipo]
    titulo, encabezados, filas = _get_datos(tipo, request.GET)

    context = {
        'meta': meta,
        'titulo': titulo,
        'tipo': tipo,
        'encabezados': encabezados,
        'filas': filas,
        'total_filas': len(filas),
        'params': request.GET,
        'query_string': request.GET.urlencode(),
        'desde': request.GET.get('desde', ''),
        'hasta': request.GET.get('hasta', ''),
    }
    if tipo == 'inventario':
        context['categorias'] = CategoriaProducto.choices
    if tipo == 'produccion':
        _, filtros = filtrar_cerdos(request.GET)
        context['estados'] = Cerdo.Estado.choices
        context['razas'] = Cerdo.Raza.choices
        context['sexos'] = Cerdo.Sexo.choices
        context['corrales'] = Corral.objects.all()
        context['categorias_cerdo'] = CategoriaCerdo.objects.all()
        context['edades_meses'], context['pesos_kg'] = opciones_filtro_edad_peso()
        context.update(filtros)
    if tipo == 'sanitario':
        _, filtros = filtrar_aplicaciones({**request.GET.dict(), 'vista': 'historial'})
        context['vacunas_cat'] = Vacuna.objects.all()
        context.update(filtros)
    return render(request, 'panel/reportes/ver.html', context)


@login_required
def reporte_exportar(request, tipo, formato):
    if tipo not in REPORTES or formato not in ('pdf', 'xlsx'):
        raise Http404
    titulo, encabezados, filas = _get_datos(tipo, request.GET)
    if formato == 'pdf':
        return exportar_pdf(titulo, encabezados, filas)
    return exportar_excel(titulo, encabezados, filas)

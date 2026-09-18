from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from inseminacion.models import Inseminacion
from panel.decorators import admin_required
from vacunas.models import AplicacionVacuna, Vacuna

from .forms import CategoriaCerdoForm, CerdoForm, CorralForm, LoteForm, PesajeForm
from .models import CategoriaCerdo, Cerdo, Corral, Lote, RegistroPeso
from .queries import filtrar_cerdos, opciones_filtro_edad_peso, resumen_stock_activos


def _query_sin_pagina(request):
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


def _query_sin_estado(request):
    """Parámetros GET conservando filtros pero sin estado/página (para pestañas)."""
    params = request.GET.copy()
    for key in ('page', 'estado', 'ver_todos'):
        params.pop(key, None)
    return params.urlencode()


@login_required
def cerdo_lista(request):
    cerdos, filtros = filtrar_cerdos(request.GET)
    paginator = Paginator(cerdos, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    resumen = resumen_stock_activos()
    edades_meses, pesos_kg = opciones_filtro_edad_peso()
    estado_actual = str(filtros.get('estado') or '')
    ver_todos = filtros.get('ver_todos', False)
    vista_granja = not ver_todos and estado_actual == Cerdo.Estado.ACTIVO

    return render(request, 'panel/registro/cerdos_lista.html', {
        'page_obj': page_obj,
        'cerdos': page_obj.object_list,
        'sexos': Cerdo.Sexo.choices,
        'estados': Cerdo.Estado.choices,
        'categorias': CategoriaCerdo.objects.all(),
        'query': _query_sin_pagina(request),
        'query_tabs': _query_sin_estado(request),
        'edades_meses': edades_meses,
        'pesos_kg': pesos_kg,
        'vista_granja': vista_granja,
        'vista_vendidos': estado_actual == Cerdo.Estado.VENDIDO,
        'vista_fallecidos': estado_actual == Cerdo.Estado.FALLECIDO,
        'vista_todos_estados': ver_todos and not estado_actual,
        **filtros,
        **resumen,
    })


@login_required
def cerdo_crear(request):
    if request.method == 'POST':
        form = CerdoForm(request.POST)
        if form.is_valid():
            cerdo = form.save()
            peso = form.cleaned_data.get('peso_actual')
            if peso is not None:
                RegistroPeso.objects.create(
                    cerdo=cerdo,
                    fecha=timezone.now().date(),
                    peso_kg=peso,
                    observaciones='Peso al registrar',
                )
            messages.success(request, f'Cerdo registrado con arete {cerdo.arete}.')
            return redirect('registro:cerdos')
    else:
        form = CerdoForm()
    return render(request, 'panel/registro/cerdo_form.html', {
        'form': form, 'titulo': 'Registrar cerdo',
    })


@login_required
def cerdo_editar(request, pk):
    cerdo = get_object_or_404(Cerdo, pk=pk)
    if request.method == 'POST':
        form = CerdoForm(request.POST, instance=cerdo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cerdo {cerdo.arete} actualizado correctamente.')
            return redirect('registro:cerdos')
    else:
        form = CerdoForm(instance=cerdo)
    return render(request, 'panel/registro/cerdo_form.html', {
        'form': form, 'titulo': 'Editar cerdo',
    })


@login_required
def cerdo_detalle(request, pk):
    cerdo = get_object_or_404(
        Cerdo.objects.select_related('corral', 'categoria', 'madre', 'parto'),
        pk=pk,
    )
    return render(request, 'panel/registro/cerdo_detalle.html', {
        'cerdo': cerdo,
        'pesajes': cerdo.pesajes.all()[:20],
        'vacunas': AplicacionVacuna.objects.filter(cerdo=cerdo).select_related('vacuna'),
        'vacunas_catalogo': Vacuna.objects.all(),
        'inseminaciones': Inseminacion.objects.filter(cerda=cerdo).select_related(
            'padrillo', 'diagnostico',
        ),
        'crias': cerdo.crias.select_related('categoria', 'corral').order_by('-fecha_nacimiento')[:20],
    })


@login_required
@admin_required
def cerdo_eliminar(request, pk):
    cerdo = get_object_or_404(Cerdo, pk=pk)
    if request.method == 'POST':
        cerdo.delete()
        messages.success(request, 'Cerdo eliminado.')
        return redirect('registro:cerdos')
    return render(request, 'panel/confirmar_eliminar.html', {'objeto': cerdo, 'volver': 'registro:cerdos'})


@login_required
def cerdo_cambiar_estado(request, pk):
    """Acción rápida: marcar un cerdo activo como vendido o fallecido (solo POST)."""
    cerdo = get_object_or_404(Cerdo, pk=pk)
    if request.method != 'POST':
        return redirect('registro:cerdos')

    nuevo = request.POST.get('estado', '')
    etiquetas = {'vendido': 'vendido', 'fallecido': 'fallecido'}
    volver = f"{reverse('registro:cerdos')}?{_query_sin_pagina(request)}"
    if nuevo not in etiquetas:
        messages.error(request, 'Estado no válido.')
        return redirect(volver)
    if cerdo.estado != 'activo':
        messages.error(
            request,
            f'El cerdo {cerdo.arete} ya figura como {cerdo.get_estado_display().lower()}; '
            'use Editar si necesita corregirlo.',
        )
        return redirect(volver)

    fecha_str = request.POST.get('fecha_salida', '').strip()
    try:
        fecha_salida = date.fromisoformat(fecha_str)
    except ValueError:
        messages.error(request, 'Indique una fecha válida.')
        return redirect(volver)
    hoy = timezone.now().date()
    if fecha_salida > hoy:
        messages.error(request, 'La fecha no puede ser futura.')
        return redirect(volver)
    if cerdo.fecha_nacimiento and fecha_salida < cerdo.fecha_nacimiento:
        messages.error(request, 'La fecha no puede ser anterior al nacimiento del cerdo.')
        return redirect(volver)

    precio = None
    if nuevo == 'vendido':
        precio_str = request.POST.get('precio_venta', '').strip().replace(',', '.')
        if precio_str:
            try:
                precio = Decimal(precio_str)
                if precio < 0:
                    raise InvalidOperation
            except InvalidOperation:
                messages.error(request, 'El precio de venta debe ser un número mayor o igual a 0.')
                return redirect(volver)

    cerdo.estado = nuevo
    cerdo.fecha_salida = fecha_salida
    cerdo.precio_venta = precio
    cerdo.save(update_fields=['estado', 'fecha_salida', 'precio_venta'])

    detalle = f'Cerdo {cerdo.arete} marcado como {etiquetas[nuevo]} el {fecha_salida:%d/%m/%Y}'
    if precio is not None:
        detalle += f' por S/. {precio:,.2f}'
    messages.success(request, detalle + '.')
    return redirect(volver)


@login_required
def cerdo_registrar_peso(request, pk):
    """Acción rápida: registrar un pesaje (solo POST, cerdos en granja)."""
    cerdo = get_object_or_404(Cerdo, pk=pk)
    volver = f"{reverse('registro:cerdos')}?{_query_sin_pagina(request)}"
    if request.method != 'POST':
        return redirect(volver)
    if cerdo.estado != Cerdo.Estado.ACTIVO:
        messages.error(request, f'Solo se puede pesar un cerdo en granja ({cerdo.arete}).')
        return redirect(volver)

    form = PesajeForm(request.POST, cerdo=cerdo)
    if form.is_valid():
        pesaje = form.save(commit=False)
        pesaje.cerdo = cerdo
        pesaje.save()
        messages.success(
            request,
            f'Pesaje registrado: {cerdo.arete} — {pesaje.peso_kg} kg '
            f'({pesaje.fecha:%d/%m/%Y}). Peso actual actualizado.',
        )
    else:
        err = next(iter(form.errors.values()))[0] if form.errors else 'Datos inválidos.'
        messages.error(request, err)
    return redirect(volver)


@login_required
@admin_required
def pesaje_eliminar(request, pk):
    pesaje = get_object_or_404(RegistroPeso.objects.select_related('cerdo'), pk=pk)
    cerdo = pesaje.cerdo
    cerdo_pk = cerdo.pk
    if request.method == 'POST':
        pesaje.delete()
        messages.success(request, f'Pesaje eliminado. Peso actual de {cerdo.arete} recalculado.')
        return redirect('registro:cerdo_detalle', pk=cerdo_pk)
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': pesaje,
        'volver': 'registro:cerdo_detalle',
        'cancel_href': reverse('registro:cerdo_detalle', args=[cerdo_pk]),
    })


@login_required
def lote_lista(request):
    lotes = Lote.objects.annotate(
        num_cerdos=Count(
            'cerdos',
            filter=Q(cerdos__estado=Cerdo.Estado.ACTIVO),
        ),
    )
    return render(request, 'panel/registro/lotes_lista.html', {'lotes': lotes})


@login_required
def lote_crear(request):
    if request.method == 'POST':
        form = LoteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lote creado.')
            return redirect('registro:lotes')
    else:
        form = LoteForm()
    return render(request, 'panel/registro/lote_form.html', {
        'form': form, 'titulo': 'Nuevo lote', 'cancel_url': 'registro:lotes',
    })


@login_required
def lote_editar(request, pk):
    lote = get_object_or_404(Lote, pk=pk)
    if request.method == 'POST':
        form = LoteForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lote actualizado.')
            return redirect('registro:lotes')
    else:
        form = LoteForm(instance=lote)
    return render(request, 'panel/registro/lote_form.html', {
        'form': form, 'titulo': 'Editar lote', 'cancel_url': 'registro:lotes',
    })


@login_required
def categoria_lista(request):
    categorias = CategoriaCerdo.objects.annotate(
        total_cerdos=Count(
            'cerdos',
            filter=Q(cerdos__estado=Cerdo.Estado.ACTIVO),
        )
    )
    return render(request, 'panel/registro/categorias_lista.html', {
        'categorias': categorias,
    })


@login_required
def categoria_crear(request):
    if request.method == 'POST':
        form = CategoriaCerdoForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada.')
            return redirect('registro:categorias')
    else:
        form = CategoriaCerdoForm()
    return render(request, 'panel/form_generic.html', {
        'form': form, 'titulo': 'Nueva categoría', 'cancel_url': 'registro:categorias',
    })


@login_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(CategoriaCerdo, pk=pk)
    if request.method == 'POST':
        form = CategoriaCerdoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" actualizada.')
            return redirect('registro:categorias')
    else:
        form = CategoriaCerdoForm(instance=categoria)
    return render(request, 'panel/form_generic.html', {
        'form': form, 'titulo': 'Editar categoría', 'cancel_url': 'registro:categorias',
    })


@login_required
@admin_required
def categoria_eliminar(request, pk):
    categoria = get_object_or_404(CategoriaCerdo, pk=pk)
    if request.method == 'POST':
        en_uso = categoria.cerdos.count()
        if en_uso:
            messages.error(
                request,
                f'No se puede eliminar "{categoria.nombre}": '
                f'tiene {en_uso} cerdo(s) asignados. Reasígnalos primero.',
            )
            return redirect('registro:categorias')
        categoria.delete()
        messages.success(request, 'Categoría eliminada.')
        return redirect('registro:categorias')
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': categoria, 'volver': 'registro:categorias',
    })


@login_required
def corral_lista(request):
    corrales = Corral.objects.annotate(
        total_cerdos=Count(
            'cerdos',
            filter=Q(cerdos__estado=Cerdo.Estado.ACTIVO),
        )
    )
    return render(request, 'panel/registro/corrales_lista.html', {
        'corrales': corrales,
    })


@login_required
def corral_crear(request):
    if request.method == 'POST':
        form = CorralForm(request.POST)
        if form.is_valid():
            corral = form.save()
            messages.success(request, f'Corral "{corral.nombre}" creado.')
            return redirect('registro:corrales')
    else:
        form = CorralForm()
    return render(request, 'panel/form_generic.html', {
        'form': form, 'titulo': 'Nuevo corral', 'cancel_url': 'registro:corrales',
    })


@login_required
def corral_editar(request, pk):
    corral = get_object_or_404(Corral, pk=pk)
    if request.method == 'POST':
        form = CorralForm(request.POST, instance=corral)
        if form.is_valid():
            form.save()
            messages.success(request, f'Corral "{corral.nombre}" actualizado.')
            return redirect('registro:corrales')
    else:
        form = CorralForm(instance=corral)
    return render(request, 'panel/form_generic.html', {
        'form': form, 'titulo': 'Editar corral', 'cancel_url': 'registro:corrales',
    })


@login_required
@admin_required
def corral_eliminar(request, pk):
    corral = get_object_or_404(Corral, pk=pk)
    if request.method == 'POST':
        en_uso = corral.cerdos.filter(estado=Cerdo.Estado.ACTIVO).count()
        if en_uso:
            messages.error(
                request,
                f'No se puede eliminar "{corral.nombre}": '
                f'tiene {en_uso} cerdo(s) en granja. Reasígnalos primero.',
            )
            return redirect('registro:corrales')
        corral.delete()
        messages.success(request, 'Corral eliminado.')
        return redirect('registro:corrales')
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': corral, 'volver': 'registro:corrales',
    })

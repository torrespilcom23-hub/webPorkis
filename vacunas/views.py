from datetime import timedelta

from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from panel.decorators import admin_required
from registro.models import Cerdo

from .forms import (
    AplicacionVacunaForm,
    AplicacionVacunaModalForm,
    RefuerzoVacunaForm,
    VacunaForm,
)
from .models import AplicacionVacuna, Vacuna
from .queries import filtrar_aplicaciones, resumen_vacunas


def _query_sin_pagina(request):
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


def _query_sin_vista(request):
    params = request.GET.copy()
    for key in ('page', 'vista'):
        params.pop(key, None)
    return params.urlencode()


@login_required
def vacuna_lista(request):
    resumen = resumen_vacunas()
    return render(request, 'panel/vacunas/vacunas_lista.html', {
        'vacunas': resumen['vacunas_catalogo'],
        'tab_activo': 'catalogo',
        **resumen,
    })


@login_required
def vacuna_crear(request):
    if request.method == 'POST':
        form = VacunaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vacuna registrada en catálogo.')
            return redirect('vacunas:catalogo')
    else:
        form = VacunaForm()
    return render(request, 'panel/vacunas/vacuna_form.html', {
        'form': form,
        'titulo': 'Agregar vacuna al catálogo',
        'cancel_url': 'vacunas:catalogo',
    })


@login_required
def vacuna_editar(request, pk):
    vacuna = get_object_or_404(Vacuna, pk=pk)
    if request.method == 'POST':
        form = VacunaForm(request.POST, instance=vacuna)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vacuna actualizada.')
            return redirect('vacunas:catalogo')
    else:
        form = VacunaForm(instance=vacuna)
    return render(request, 'panel/vacunas/vacuna_form.html', {
        'form': form,
        'titulo': 'Editar vacuna',
        'cancel_url': 'vacunas:catalogo',
    })


@login_required
@admin_required
def vacuna_eliminar(request, pk):
    vacuna = get_object_or_404(Vacuna, pk=pk)
    en_uso = AplicacionVacuna.objects.filter(vacuna=vacuna).count()
    if request.method == 'POST':
        if en_uso:
            messages.error(
                request,
                f'No se puede eliminar: hay {en_uso} aplicación(es) registrada(s) con esta vacuna.',
            )
            return redirect('vacunas:catalogo')
        try:
            vacuna.delete()
        except ProtectedError:
            messages.error(request, 'No se puede eliminar: la vacuna está en uso.')
            return redirect('vacunas:catalogo')
        messages.success(request, 'Vacuna eliminada del catálogo.')
        return redirect('vacunas:catalogo')
    nota = None
    if en_uso:
        nota = f'Hay {en_uso} aplicación(es) registrada(s). Eliminarlas primero o no podrá borrar esta vacuna.'
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': vacuna,
        'volver': 'vacunas:catalogo',
        'nota': nota,
    })


@login_required
def aplicacion_lista(request):
    aplicaciones, filtros = filtrar_aplicaciones(request.GET)
    paginator = Paginator(aplicaciones, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    resumen = resumen_vacunas()
    vista = filtros.get('vista', 'historial')

    return render(request, 'panel/vacunas/aplicaciones_lista.html', {
        'page_obj': page_obj,
        'aplicaciones': page_obj.object_list,
        'vacunas_cat': Vacuna.objects.all(),
        'query': _query_sin_pagina(request),
        'query_tabs': _query_sin_vista(request),
        'tab_activo': vista if vista in ('vencidas', 'proximas') else 'historial',
        'vista_historial': vista == 'historial',
        'vista_vencidas': vista == 'vencidas',
        'vista_proximas': vista == 'proximas',
        **filtros,
        **resumen,
    })


@login_required
def aplicacion_crear(request):
    cerdo = None
    cerdo_pk = request.GET.get('cerdo')
    if cerdo_pk:
        cerdo = get_object_or_404(Cerdo, pk=cerdo_pk)
    if request.method == 'POST':
        form = AplicacionVacunaForm(request.POST, cerdo=cerdo)
        if form.is_valid():
            aplicacion = form.save(commit=False)
            aplicacion.responsable = request.user
            aplicacion.save()
            messages.success(
                request,
                f'Vacuna {aplicacion.vacuna.nombre} aplicada a {aplicacion.cerdo.arete}.',
            )
            volver = request.POST.get('volver')
            if volver:
                return redirect(volver)
            return redirect('vacunas:aplicaciones')
    else:
        form = AplicacionVacunaForm(cerdo=cerdo)
    return render(request, 'panel/vacunas/aplicacion_form.html', {
        'form': form,
        'titulo': 'Registrar aplicación',
        'cancel_url': 'vacunas:aplicaciones',
        'cerdo': cerdo,
    })


@login_required
def aplicacion_refuerzo(request, pk):
    """Registra un refuerzo a partir de una aplicación anterior (mismo cerdo y vacuna)."""
    anterior = get_object_or_404(
        AplicacionVacuna.objects.select_related('cerdo', 'vacuna'),
        pk=pk,
    )
    cerdo = anterior.cerdo
    hoy = timezone.now().date()
    if cerdo.estado != Cerdo.Estado.ACTIVO:
        messages.error(
            request,
            f'El cerdo {cerdo.arete} ya no está en granja; no se puede registrar refuerzo.',
        )
        return redirect('vacunas:aplicaciones')

    if request.method == 'POST':
        form = RefuerzoVacunaForm(request.POST, anterior=anterior)
        if form.is_valid():
            aplicacion = form.save(commit=False)
            aplicacion.responsable = request.user
            aplicacion.save()
            detalle = (
                f'Refuerzo registrado: {aplicacion.vacuna.nombre} — {cerdo.arete} '
                f'({aplicacion.fecha_aplicacion:%d/%m/%Y}).'
            )
            if aplicacion.proxima_dosis:
                detalle += f' Próxima dosis: {aplicacion.proxima_dosis:%d/%m/%Y}.'
            messages.success(request, detalle)
            return redirect('vacunas:aplicaciones')
    else:
        form = RefuerzoVacunaForm(anterior=anterior)

    intervalo = anterior.vacuna.intervalo_dias
    puede_registrar = getattr(form, 'puede_registrar', True)
    fecha_refuerzo = (
        form.fields['fecha_aplicacion'].initial if puede_registrar else None
    )
    proxima_estimada = (
        fecha_refuerzo + timedelta(days=intervalo)
        if fecha_refuerzo and intervalo else None
    )

    return render(request, 'panel/vacunas/refuerzo_form.html', {
        'form': form,
        'anterior': anterior,
        'cerdo': cerdo,
        'hoy': hoy,
        'intervalo': intervalo,
        'proxima_estimada': proxima_estimada,
        'puede_registrar': puede_registrar,
        'min_fecha_refuerzo': getattr(form, 'min_fecha_refuerzo', None),
        'max_fecha_refuerzo': getattr(form, 'max_fecha_refuerzo', hoy),
    })


@login_required
def aplicacion_registrar_rapida(request, cerdo_pk):
    """Registro rápido desde ficha de cerdo (solo POST)."""
    cerdo = get_object_or_404(Cerdo, pk=cerdo_pk)
    volver = request.POST.get(
        'volver',
        reverse('registro:cerdo_detalle', args=[cerdo_pk]),
    )
    if request.method != 'POST':
        return redirect(volver)
    if cerdo.estado != Cerdo.Estado.ACTIVO:
        messages.error(request, f'Solo se puede vacunar un cerdo en granja ({cerdo.arete}).')
        return redirect(volver)

    form = AplicacionVacunaModalForm(request.POST, cerdo=cerdo)
    if form.is_valid():
        aplicacion = form.save(commit=False)
        aplicacion.responsable = request.user
        aplicacion.save()
        prox = ''
        if aplicacion.proxima_dosis:
            prox = f' Próxima dosis: {aplicacion.proxima_dosis:%d/%m/%Y}.'
        messages.success(
            request,
            f'Vacuna registrada: {aplicacion.vacuna.nombre} — {cerdo.arete}.{prox}',
        )
    else:
        err = next(iter(form.errors.values()))[0] if form.errors else 'Datos inválidos.'
        messages.error(request, err)
    return redirect(volver)


@login_required
def aplicacion_editar(request, pk):
    aplicacion = get_object_or_404(AplicacionVacuna, pk=pk)
    if request.method == 'POST':
        form = AplicacionVacunaForm(request.POST, instance=aplicacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aplicación actualizada.')
            return redirect('vacunas:aplicaciones')
    else:
        form = AplicacionVacunaForm(instance=aplicacion)
    return render(request, 'panel/vacunas/aplicacion_form.html', {
        'form': form,
        'titulo': 'Editar aplicación',
        'cancel_url': 'vacunas:aplicaciones',
    })


@login_required
@admin_required
def aplicacion_eliminar(request, pk):
    aplicacion = get_object_or_404(AplicacionVacuna, pk=pk)
    if request.method == 'POST':
        aplicacion.delete()
        messages.success(request, 'Aplicación eliminada.')
        return redirect('vacunas:aplicaciones')
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': aplicacion,
        'volver': 'vacunas:aplicaciones',
    })

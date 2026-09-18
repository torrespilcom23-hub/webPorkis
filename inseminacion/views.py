from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from panel.decorators import admin_required

from .forms import (
    DiagnosticoForm,
    InseminacionForm,
    LechonesRapidoForm,
    LechonItemFormSet,
    LechonesComunForm,
    PadrilloForm,
    PartoForm,
)
from .lechones import registrar_lechones
from .models import Inseminacion, Padrillo, Parto
from .queries import filtrar_inseminaciones, filtrar_partos, resumen_inseminacion


def _query_sin_pagina(request):
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


def _query_sin_vista(request):
    params = request.GET.copy()
    for key in ('page', 'vista'):
        params.pop(key, None)
    return params.urlencode()


def _ctx_lista(**extra):
    return {**resumen_inseminacion(), **extra}


def _redirect_next(request, default_view, *args, **kwargs):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
    ):
        return redirect(next_url)
    return redirect(default_view, *args, **kwargs)


def _parto_lechones_or_redirect(parto):
    if not parto.puede_dar_alta_lechones:
        return None
    return parto


def _items_desde_rapido(cleaned):
    items = []
    for _ in range(cleaned['machos']):
        items.append({'sexo': 'M'})
    for _ in range(cleaned['hembras']):
        items.append({'sexo': 'H'})
    return items


def _items_desde_formset(formset):
    items = []
    for form in formset:
        if not form.cleaned_data:
            continue
        items.append({
            'sexo': form.cleaned_data['sexo'],
            'peso_actual': form.cleaned_data.get('peso_actual'),
            'observaciones': form.cleaned_data.get('observaciones', ''),
        })
    return items


def _guardar_lechones(request, parto, cleaned_comun, items):
    creados = registrar_lechones(
        parto,
        items=items,
        raza=cleaned_comun['raza'],
        raza_otro=cleaned_comun.get('raza_otro', ''),
        categoria=cleaned_comun.get('categoria'),
        corral=cleaned_comun.get('corral'),
        lote=cleaned_comun.get('lote'),
        crear_lote_camada=cleaned_comun.get('crear_lote_camada', False),
    )
    messages.success(
        request,
        f'{len(creados)} lechón(es) dados de alta en Registro '
        f'({creados[0].arete} … {creados[-1].arete}).',
    )
    if parto.puede_dar_alta_lechones:
        messages.info(
            request,
            f'Quedan {parto.lechones_pendientes_alta} por registrar de este parto.',
        )
    return creados


@login_required
def inseminacion_index(request):
    inseminaciones, filtros = filtrar_inseminaciones(request.GET)
    paginator = Paginator(inseminaciones, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    vista = filtros.get('vista', 'historial')

    return render(request, 'panel/inseminacion/inseminaciones_lista.html', _ctx_lista(
        page_obj=page_obj,
        inseminaciones=page_obj.object_list,
        padrillos_cat=Padrillo.objects.all(),
        query=_query_sin_pagina(request),
        query_tabs=_query_sin_vista(request),
        tab_activo='pendientes' if vista == 'pendientes' else 'historial',
        vista_pendientes=vista == 'pendientes',
        vista_historial=vista != 'pendientes',
        **filtros,
    ))


@login_required
def partos_lista(request):
    partos, filtros = filtrar_partos(request.GET)
    paginator = Paginator(partos, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'panel/inseminacion/partos_lista.html', _ctx_lista(
        page_obj=page_obj,
        partos=page_obj.object_list,
        query=_query_sin_pagina(request),
        tab_activo='partos',
        **filtros,
    ))


@login_required
def padrillos_lista(request):
    resumen = resumen_inseminacion()
    return render(request, 'panel/inseminacion/padrillos_lista.html', {
        'padrillos': resumen['padrillos_catalogo'],
        'tab_activo': 'padrillos',
        **resumen,
    })


# --- Inseminaciones ----------------------------------------------------------

@login_required
def inseminacion_crear(request):
    cerda = None
    cerda_pk = request.GET.get('cerda')
    if cerda_pk:
        from registro.models import Cerdo
        cerda = get_object_or_404(Cerdo, pk=cerda_pk, sexo=Cerdo.Sexo.HEMBRA)

    if request.method == 'POST':
        form = InseminacionForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.responsable = request.user
            registro.save()
            messages.success(request, 'Inseminación registrada.')
            return redirect('inseminacion:index')
    else:
        initial = {'cerda': cerda} if cerda else {}
        form = InseminacionForm(initial=initial)

    return render(request, 'panel/inseminacion/inseminacion_form.html', {
        'form': form,
        'titulo': 'Nueva inseminación',
        'cancel_url': 'inseminacion:index',
    })


@login_required
def inseminacion_editar(request, pk):
    inseminacion = get_object_or_404(Inseminacion, pk=pk)
    if request.method == 'POST':
        form = InseminacionForm(request.POST, instance=inseminacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inseminación actualizada.')
            return redirect('inseminacion:index')
    else:
        form = InseminacionForm(instance=inseminacion)
    return render(request, 'panel/inseminacion/inseminacion_form.html', {
        'form': form,
        'titulo': 'Editar inseminación',
        'cancel_url': 'inseminacion:index',
    })


@login_required
@admin_required
def inseminacion_eliminar(request, pk):
    inseminacion = get_object_or_404(
        Inseminacion.objects.prefetch_related('partos'),
        pk=pk,
    )
    num_partos = inseminacion.partos.count()
    if request.method == 'POST':
        if num_partos:
            messages.error(
                request,
                f'No se puede eliminar: tiene {num_partos} parto(s) registrado(s). '
                'Elimine primero los partos.',
            )
            return redirect('inseminacion:index')
        try:
            inseminacion.delete()
        except ProtectedError:
            messages.error(
                request,
                'No se puede eliminar: hay registros vinculados a esta inseminación.',
            )
            return redirect('inseminacion:index')
        messages.success(request, 'Inseminación eliminada.')
        return redirect('inseminacion:index')
    nota = None
    if num_partos:
        nota = (
            f'Tiene {num_partos} parto(s) registrado(s). '
            'Debe eliminarlos antes de borrar la inseminación.'
        )
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': inseminacion,
        'volver': 'inseminacion:index',
        'nota': nota,
    })


# --- Diagnóstico de preñez ---------------------------------------------------

@login_required
def diagnostico_crear(request, pk):
    inseminacion = get_object_or_404(
        Inseminacion.objects.select_related('cerda', 'diagnostico'),
        pk=pk,
    )
    if inseminacion.tiene_diagnostico:
        messages.info(request, 'Esta inseminación ya tiene diagnóstico registrado.')
        return redirect('inseminacion:index')

    if request.method == 'POST':
        form = DiagnosticoForm(request.POST, inseminacion=inseminacion)
        if form.is_valid():
            diagnostico = form.save(commit=False)
            diagnostico.inseminacion = inseminacion
            diagnostico.save()
            messages.success(request, 'Diagnóstico registrado.')
            return redirect('inseminacion:index')
    else:
        form = DiagnosticoForm(inseminacion=inseminacion)

    return render(request, 'panel/inseminacion/diagnostico_form.html', {
        'form': form,
        'inseminacion': inseminacion,
        'cancel_url': 'inseminacion:index',
    })


# --- Partos ------------------------------------------------------------------

@login_required
def parto_crear(request):
    inseminacion_pk = request.GET.get('inseminacion')
    initial = {}
    if inseminacion_pk:
        inseminacion = get_object_or_404(Inseminacion, pk=inseminacion_pk)
        initial['inseminacion'] = inseminacion

    if request.method == 'POST':
        form = PartoForm(request.POST)
        if form.is_valid():
            parto = form.save()
            messages.success(request, 'Parto registrado.')
            if parto.puede_dar_alta_lechones:
                messages.info(
                    request,
                    'Puede dar de alta los lechones en Registro ahora.',
                )
                return redirect('inseminacion:parto_lechones', pk=parto.pk)
            return redirect('inseminacion:partos')
    else:
        form = PartoForm(initial=initial)

    return render(request, 'panel/inseminacion/parto_form.html', {
        'form': form,
        'titulo': 'Registrar parto',
        'cancel_url': 'inseminacion:partos',
    })


@login_required
def parto_editar(request, pk):
    parto = get_object_or_404(Parto, pk=pk)
    if request.method == 'POST':
        form = PartoForm(request.POST, instance=parto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Parto actualizado.')
            return redirect('inseminacion:partos')
    else:
        form = PartoForm(instance=parto)
    return render(request, 'panel/inseminacion/parto_form.html', {
        'form': form,
        'titulo': 'Editar parto',
        'cancel_url': 'inseminacion:partos',
    })


@login_required
@admin_required
def parto_eliminar(request, pk):
    parto = get_object_or_404(
        Parto.objects.select_related('inseminacion__cerda'),
        pk=pk,
    )
    en_registro = parto.lechones_en_registro
    if request.method == 'POST':
        parto.delete()
        messages.success(request, 'Parto eliminado.')
        return redirect('inseminacion:partos')
    nota = None
    if en_registro:
        nota = (
            f'Hay {en_registro} lechón(es) vinculados en Registro; '
            'se conservarán pero perderán el enlace a este parto.'
        )
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': parto,
        'volver': 'inseminacion:partos',
        'nota': nota,
    })


# --- Alta de lechones en Registro --------------------------------------------

@login_required
def parto_lechones(request, pk):
    parto = get_object_or_404(
        Parto.objects.select_related('inseminacion__cerda', 'inseminacion__padrillo').prefetch_related(
            'lechones_registrados__categoria',
            'lechones_registrados__corral',
        ),
        pk=pk,
    )
    if not _parto_lechones_or_redirect(parto):
        messages.info(request, 'Todos los lechones vivos de este parto ya están en Registro.')
        return redirect('inseminacion:partos')

    return render(request, 'panel/inseminacion/lechones_menu.html', {
        'parto': parto,
        'tab_activo': 'partos',
        **resumen_inseminacion(),
    })


@login_required
def parto_lechones_rapido(request, pk):
    parto = get_object_or_404(
        Parto.objects.select_related('inseminacion__cerda'),
        pk=pk,
    )
    if not _parto_lechones_or_redirect(parto):
        messages.info(request, 'No quedan lechones por dar de alta.')
        return redirect('inseminacion:partos')

    if request.method == 'POST':
        form = LechonesRapidoForm(request.POST, parto=parto)
        if form.is_valid():
            _guardar_lechones(
                request,
                parto,
                form.cleaned_data,
                _items_desde_rapido(form.cleaned_data),
            )
            if parto.puede_dar_alta_lechones:
                return redirect('inseminacion:parto_lechones', pk=parto.pk)
            return redirect('inseminacion:partos')
    else:
        form = LechonesRapidoForm(parto=parto)

    return render(request, 'panel/inseminacion/lechones_rapido.html', {
        'parto': parto,
        'form': form,
        'tab_activo': 'partos',
        **resumen_inseminacion(),
    })


def _initial_lechones(cantidad):
    return [
        {'sexo': 'M' if i % 2 == 0 else 'H'}
        for i in range(cantidad)
    ]


@login_required
def parto_lechones_detallado(request, pk):
    parto = get_object_or_404(
        Parto.objects.select_related('inseminacion__cerda'),
        pk=pk,
    )
    if not _parto_lechones_or_redirect(parto):
        messages.info(request, 'No quedan lechones por dar de alta.')
        return redirect('inseminacion:partos')

    pend = parto.lechones_pendientes_alta

    def _parse_cantidad(raw):
        try:
            return max(1, min(int(raw), pend))
        except (TypeError, ValueError):
            return pend

    if request.method == 'POST':
        accion = request.POST.get('accion', 'registrar')
        comun = LechonesComunForm(request.POST, parto=parto)
        cantidad = _parse_cantidad(request.POST.get('cantidad', pend))

        if accion == 'generar':
            formset = LechonItemFormSet(initial=_initial_lechones(cantidad))
        else:
            formset = LechonItemFormSet(request.POST)
            if comun.is_valid() and formset.is_valid():
                items = _items_desde_formset(formset)
                if not items:
                    messages.error(request, 'Indique al menos un lechón.')
                elif len(items) > pend:
                    messages.error(
                        request,
                        f'Solo puede registrar {pend} lechón(es) más.',
                    )
                else:
                    _guardar_lechones(request, parto, comun.cleaned_data, items)
                    if parto.puede_dar_alta_lechones:
                        return redirect('inseminacion:parto_lechones', pk=parto.pk)
                    return redirect('inseminacion:partos')
            cantidad = len(formset.forms)
    else:
        comun = LechonesComunForm(parto=parto)
        cantidad = pend
        formset = LechonItemFormSet(initial=_initial_lechones(cantidad))

    return render(request, 'panel/inseminacion/lechones_detallado.html', {
        'parto': parto,
        'comun': comun,
        'formset': formset,
        'cantidad': cantidad,
        'pendientes': pend,
        'tab_activo': 'partos',
        **resumen_inseminacion(),
    })


# --- Padrillos ---------------------------------------------------------------

@login_required
def padrillo_crear(request):
    if request.method == 'POST':
        form = PadrilloForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Padrillo registrado. Ya puede seleccionarlo en la inseminación.')
            return _redirect_next(request, 'inseminacion:padrillos')
    else:
        form = PadrilloForm()
    return render(request, 'panel/inseminacion/padrillo_form.html', {
        'form': form,
        'titulo': 'Nuevo padrillo',
        'cancel_url': 'inseminacion:padrillos',
        'next_url': request.GET.get('next', ''),
    })


@login_required
def padrillo_editar(request, pk):
    padrillo = get_object_or_404(Padrillo, pk=pk)
    if request.method == 'POST':
        form = PadrilloForm(request.POST, instance=padrillo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Padrillo actualizado.')
            return redirect('inseminacion:padrillos')
    else:
        form = PadrilloForm(instance=padrillo)
    return render(request, 'panel/inseminacion/padrillo_form.html', {
        'form': form,
        'titulo': 'Editar padrillo',
        'cancel_url': 'inseminacion:padrillos',
    })


@login_required
@admin_required
def padrillo_eliminar(request, pk):
    padrillo = get_object_or_404(Padrillo, pk=pk)
    en_uso = Inseminacion.objects.filter(padrillo=padrillo).count()
    if request.method == 'POST':
        if en_uso:
            messages.error(
                request,
                f'No se puede eliminar: hay {en_uso} inseminación(es) con este padrillo.',
            )
            return redirect('inseminacion:padrillos')
        try:
            padrillo.delete()
        except ProtectedError:
            messages.error(request, 'No se puede eliminar: el padrillo está en uso.')
            return redirect('inseminacion:padrillos')
        messages.success(request, 'Padrillo eliminado.')
        return redirect('inseminacion:padrillos')
    nota = None
    if en_uso:
        nota = f'Hay {en_uso} inseminación(es) registrada(s). No podrá eliminarlo mientras estén vinculadas.'
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': padrillo,
        'volver': 'inseminacion:padrillos',
        'nota': nota,
    })

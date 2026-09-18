from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from panel.decorators import admin_required
from registro.models import Lote

from .forms import PlanAlimentacionForm, RegistroAlimentacionForm, TipoAlimentoForm
from .models import PlanAlimentacion, RegistroAlimentacion, TipoAlimento
from .queries import filtrar_planes, filtrar_registros, resumen_alimentos


def _query_sin_pagina(request):
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


@login_required
def consumo_lista(request):
    registros, filtros = filtrar_registros(request.GET)
    paginator = Paginator(registros, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    resumen = resumen_alimentos()

    return render(request, 'panel/alimentos/consumo_lista.html', {
        'page_obj': page_obj,
        'registros': page_obj.object_list,
        'tipos_cat': TipoAlimento.objects.order_by('nombre'),
        'lotes_cat': Lote.objects.order_by('nombre'),
        'query': _query_sin_pagina(request),
        'tab_activo': 'consumo',
        **filtros,
        **resumen,
    })


@login_required
def catalogo_lista(request):
    resumen = resumen_alimentos()
    return render(request, 'panel/alimentos/catalogo_lista.html', {
        'tipos': resumen['tipos_catalogo'],
        'tab_activo': 'catalogo',
        **resumen,
    })


@login_required
def planes_lista(request):
    planes, filtros = filtrar_planes(request.GET)
    resumen = resumen_alimentos()

    return render(request, 'panel/alimentos/planes_lista.html', {
        'planes': planes,
        'tab_activo': 'planes',
        **filtros,
        **resumen,
    })


# --- Tipos de alimento (catálogo) --------------------------------------------

@login_required
def tipo_crear(request):
    if request.method == 'POST':
        form = TipoAlimentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de alimento agregado al catálogo.')
            return redirect('alimentos:catalogo')
    else:
        form = TipoAlimentoForm()
    return render(request, 'panel/alimentos/tipo_form.html', {
        'form': form,
        'titulo': 'Agregar alimento al catálogo',
        'cancel_url': 'alimentos:catalogo',
    })


@login_required
def tipo_editar(request, pk):
    tipo = get_object_or_404(TipoAlimento, pk=pk)
    if request.method == 'POST':
        form = TipoAlimentoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de alimento actualizado.')
            return redirect('alimentos:catalogo')
    else:
        form = TipoAlimentoForm(instance=tipo)
    return render(request, 'panel/alimentos/tipo_form.html', {
        'form': form,
        'titulo': 'Editar alimento',
        'cancel_url': 'alimentos:catalogo',
    })


@login_required
@admin_required
def tipo_eliminar(request, pk):
    tipo = get_object_or_404(TipoAlimento, pk=pk)
    en_planes = PlanAlimentacion.objects.filter(tipo_alimento=tipo).count()
    en_registros = RegistroAlimentacion.objects.filter(tipo_alimento=tipo).count()
    en_uso = en_planes + en_registros
    if request.method == 'POST':
        if en_uso:
            messages.error(
                request,
                f'No se puede eliminar: hay {en_uso} ración(es) o registro(s) con este alimento.',
            )
            return redirect('alimentos:catalogo')
        try:
            tipo.delete()
        except ProtectedError:
            messages.error(request, 'No se puede eliminar: el alimento está en uso.')
            return redirect('alimentos:catalogo')
        messages.success(request, 'Tipo de alimento eliminado del catálogo.')
        return redirect('alimentos:catalogo')
    nota = None
    if en_uso:
        nota = (
            f'Hay {en_planes} ración(es) y {en_registros} registro(s) con este alimento. '
            'Elimínelos o reasígnelos antes de borrar.'
        )
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': tipo,
        'volver': 'alimentos:catalogo',
        'nota': nota,
    })


# --- Planes de alimentación --------------------------------------------------

@login_required
def plan_crear(request):
    if request.method == 'POST':
        form = PlanAlimentacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ración por lote creada.')
            return redirect('alimentos:planes')
    else:
        form = PlanAlimentacionForm()
    return render(request, 'panel/alimentos/plan_form.html', {
        'form': form,
        'titulo': 'Nueva ración por lote',
        'cancel_url': 'alimentos:planes',
    })


@login_required
def plan_editar(request, pk):
    plan = get_object_or_404(PlanAlimentacion, pk=pk)
    if request.method == 'POST':
        form = PlanAlimentacionForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ración actualizada.')
            return redirect('alimentos:planes')
    else:
        form = PlanAlimentacionForm(instance=plan)
    return render(request, 'panel/alimentos/plan_form.html', {
        'form': form,
        'titulo': 'Editar ración',
        'cancel_url': 'alimentos:planes',
    })


@login_required
@admin_required
def plan_eliminar(request, pk):
    plan = get_object_or_404(PlanAlimentacion, pk=pk)
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Ración eliminada.')
        return redirect('alimentos:planes')
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': plan,
        'volver': 'alimentos:planes',
    })


# --- Registros de consumo ----------------------------------------------------

def _plan_sugerido_para_lote(lote):
    return (
        PlanAlimentacion.objects.filter(lote=lote, activo=True)
        .select_related('tipo_alimento')
        .order_by('-id')
        .first()
    )


@login_required
def registro_crear(request):
    lote = None
    plan_sugerido = None
    plan_pk = request.GET.get('plan')
    lote_pk = request.GET.get('lote')
    if plan_pk:
        plan_sugerido = get_object_or_404(
            PlanAlimentacion.objects.select_related('lote', 'tipo_alimento'),
            pk=plan_pk,
        )
        lote = plan_sugerido.lote
    elif lote_pk:
        lote = get_object_or_404(Lote, pk=lote_pk)
        plan_sugerido = _plan_sugerido_para_lote(lote)
    if request.method == 'POST':
        form = RegistroAlimentacionForm(request.POST, lote=lote, plan_sugerido=plan_sugerido)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.registrado_por = request.user
            registro.save()
            messages.success(
                request,
                f'Consumo registrado: {registro.lote.nombre} — '
                f'{registro.cantidad_servida_kg} kg ({registro.fecha:%d/%m/%Y}).',
            )
            return redirect('alimentos:index')
    else:
        form = RegistroAlimentacionForm(lote=lote, plan_sugerido=plan_sugerido)
    return render(request, 'panel/alimentos/registro_form.html', {
        'form': form,
        'titulo': 'Registrar consumo',
        'cancel_url': 'alimentos:index',
        'lote': lote,
        'plan_sugerido': plan_sugerido,
        'hoy': timezone.now().date(),
    })


@login_required
def registro_editar(request, pk):
    registro = get_object_or_404(RegistroAlimentacion, pk=pk)
    if request.method == 'POST':
        form = RegistroAlimentacionForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro de consumo actualizado.')
            return redirect('alimentos:index')
    else:
        form = RegistroAlimentacionForm(instance=registro)
    return render(request, 'panel/alimentos/registro_form.html', {
        'form': form,
        'titulo': 'Editar consumo',
        'cancel_url': 'alimentos:index',
        'hoy': timezone.now().date(),
    })


@login_required
@admin_required
def registro_eliminar(request, pk):
    registro = get_object_or_404(RegistroAlimentacion, pk=pk)
    if request.method == 'POST':
        registro.delete()
        messages.success(request, 'Registro eliminado.')
        return redirect('alimentos:index')
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': registro,
        'volver': 'alimentos:index',
    })

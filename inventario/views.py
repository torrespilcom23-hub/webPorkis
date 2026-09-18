from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from panel.decorators import admin_required

from .forms import MovimientoForm, ProductoForm
from .models import CategoriaProducto, MovimientoInventario, Producto


def _query_sin_pagina(request):
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


@login_required
def producto_lista(request):
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '')
    solo_stock_bajo = request.GET.get('stock_bajo') == '1'

    productos = Producto.objects.all()
    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
    if categoria:
        productos = productos.filter(categoria=categoria)
    if solo_stock_bajo:
        productos = productos.filter(stock_actual__lte=F('stock_minimo'))

    paginator = Paginator(productos, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    hoy = timezone.now().date()
    total_por_vencer = Producto.objects.filter(
        fecha_vencimiento__isnull=False,
        fecha_vencimiento__lte=hoy + timedelta(days=30),
    ).count()

    return render(request, 'panel/inventario/lista.html', {
        'page_obj': page_obj,
        'productos': page_obj.object_list,
        'q': q,
        'categoria': categoria,
        'categorias': CategoriaProducto.choices,
        'solo_stock_bajo': solo_stock_bajo,
        'total_por_vencer': total_por_vencer,
        'total_stock_bajo': Producto.objects.filter(stock_actual__lte=F('stock_minimo')).count(),
        'query': _query_sin_pagina(request),
    })


@login_required
def producto_detalle(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    movimientos = producto.movimientos.select_related('registrado_por')
    paginator = Paginator(movimientos, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'panel/inventario/detalle.html', {
        'producto': producto,
        'page_obj': page_obj,
        'movimientos': page_obj.object_list,
    })


@login_required
def producto_crear(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(
                request,
                f'Producto "{producto.nombre}" creado con código {producto.codigo}.',
            )
            return redirect('inventario:lista')
    else:
        form = ProductoForm()
    return render(request, 'panel/inventario/form.html', {'form': form, 'titulo': 'Nuevo producto'})


@login_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado correctamente.')
            return redirect('inventario:lista')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'panel/inventario/form.html', {'form': form, 'titulo': 'Editar producto'})


@login_required
@admin_required
def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('inventario:lista')
    return render(request, 'panel/confirmar_eliminar.html', {'objeto': producto, 'volver': 'inventario:lista'})


@login_required
def movimientos_lista(request):
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')

    movimientos = MovimientoInventario.objects.select_related('producto', 'registrado_por')
    if q:
        movimientos = movimientos.filter(
            Q(producto__nombre__icontains=q) | Q(producto__codigo__icontains=q) | Q(motivo__icontains=q)
        )
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)

    paginator = Paginator(movimientos, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'panel/inventario/movimientos.html', {
        'page_obj': page_obj,
        'movimientos': page_obj.object_list,
        'q': q,
        'tipo': tipo,
        'tipos': MovimientoInventario.TipoMovimiento.choices,
        'query': _query_sin_pagina(request),
    })


@login_required
def movimiento_crear(request):
    producto_fijo = None
    producto_id = request.GET.get('producto') or request.POST.get('producto')
    if producto_id:
        producto_fijo = Producto.objects.filter(pk=producto_id).first()

    if request.method == 'POST':
        form = MovimientoForm(request.POST, producto_fijo=producto_fijo)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.registrado_por = request.user
            movimiento.save()
            movimiento.producto.refresh_from_db(fields=['stock_actual'])
            messages.success(
                request,
                f'{movimiento.get_tipo_display()} registrada en "{movimiento.producto.nombre}". '
                f'Stock actual: {movimiento.producto.stock_actual} {movimiento.producto.unidad}.',
            )
            if producto_fijo:
                return redirect('inventario:detalle', pk=producto_fijo.pk)
            return redirect('inventario:movimientos')
    else:
        form = MovimientoForm(producto_fijo=producto_fijo)
    if producto_fijo:
        cancel_href = reverse('inventario:detalle', args=[producto_fijo.pk])
    else:
        cancel_href = reverse('inventario:movimientos')
    return render(request, 'panel/inventario/movimiento.html', {
        'form': form,
        'titulo': 'Registrar movimiento',
        'producto_fijo': producto_fijo,
        'cancel_href': cancel_href,
    })


@login_required
@admin_required
def movimiento_eliminar(request, pk):
    movimiento = get_object_or_404(MovimientoInventario, pk=pk)
    if request.method == 'POST':
        producto = movimiento.producto
        # Revertir una entrada no puede dejar el stock en negativo
        if (
            movimiento.tipo == MovimientoInventario.TipoMovimiento.ENTRADA
            and producto.stock_actual < movimiento.cantidad
        ):
            messages.error(
                request,
                f'No se puede eliminar esta entrada: el stock actual de '
                f'"{producto.nombre}" ({producto.stock_actual} {producto.unidad}) '
                f'es menor que la cantidad ingresada ({movimiento.cantidad}). '
                f'Quedaría stock negativo.',
            )
            return redirect('inventario:movimientos')
        movimiento.delete()  # revierte el stock automáticamente
        messages.success(request, 'Movimiento eliminado y stock revertido.')
        return redirect('inventario:movimientos')
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': movimiento,
        'volver': 'inventario:movimientos',
        'nota': 'Al eliminar este movimiento, su efecto sobre el stock será revertido.',
    })

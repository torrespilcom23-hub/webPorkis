from django.contrib import admin

from .models import MovimientoInventario, Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'stock_actual', 'stock_minimo')
    list_filter = ('categoria',)
    search_fields = ('codigo', 'nombre')
    readonly_fields = ('codigo',)


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'registrado_por', 'created_at')
    list_filter = ('tipo',)

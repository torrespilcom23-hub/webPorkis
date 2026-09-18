from django.contrib import admin

from .models import CategoriaCerdo, Cerdo, Corral, Lote, RegistroPeso


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'corral', 'fecha_ingreso')


@admin.register(Corral)
class CorralAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'capacidad')


@admin.register(CategoriaCerdo)
class CategoriaCerdoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)


@admin.register(Cerdo)
class CerdoAdmin(admin.ModelAdmin):
    list_display = ('arete', 'raza', 'sexo', 'estado', 'corral', 'peso_actual')
    list_filter = ('estado', 'sexo', 'raza', 'corral')
    search_fields = ('arete', 'nombre')


@admin.register(RegistroPeso)
class RegistroPesoAdmin(admin.ModelAdmin):
    list_display = ('cerdo', 'fecha', 'peso_kg')
    list_filter = ('fecha',)

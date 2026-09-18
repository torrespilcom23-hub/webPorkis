from django.urls import path

from . import views

app_name = 'registro'

urlpatterns = [
    path('cerdos/', views.cerdo_lista, name='cerdos'),
    path('cerdos/nuevo/', views.cerdo_crear, name='cerdo_crear'),
    path('cerdos/<int:pk>/', views.cerdo_detalle, name='cerdo_detalle'),
    path('cerdos/<int:pk>/editar/', views.cerdo_editar, name='cerdo_editar'),
    path('cerdos/<int:pk>/eliminar/', views.cerdo_eliminar, name='cerdo_eliminar'),
    path('cerdos/<int:pk>/estado/', views.cerdo_cambiar_estado, name='cerdo_estado'),
    path('cerdos/<int:pk>/peso/', views.cerdo_registrar_peso, name='cerdo_peso'),
    path('pesajes/<int:pk>/eliminar/', views.pesaje_eliminar, name='pesaje_eliminar'),
    path('corrales/', views.corral_lista, name='corrales'),
    path('corrales/nuevo/', views.corral_crear, name='corral_crear'),
    path('corrales/<int:pk>/editar/', views.corral_editar, name='corral_editar'),
    path('corrales/<int:pk>/eliminar/', views.corral_eliminar, name='corral_eliminar'),
    path('lotes/', views.lote_lista, name='lotes'),
    path('lotes/nuevo/', views.lote_crear, name='lote_crear'),
    path('lotes/<int:pk>/editar/', views.lote_editar, name='lote_editar'),
    path('categorias/', views.categoria_lista, name='categorias'),
    path('categorias/nueva/', views.categoria_crear, name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.categoria_eliminar, name='categoria_eliminar'),
]

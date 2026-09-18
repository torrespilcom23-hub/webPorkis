from django.urls import path

from . import views

app_name = 'alimentos'

urlpatterns = [
    path('', views.consumo_lista, name='index'),
    path('catalogo/', views.catalogo_lista, name='catalogo'),
    path('planes/', views.planes_lista, name='planes'),
    path('tipo/nuevo/', views.tipo_crear, name='tipo_crear'),
    path('tipo/<int:pk>/editar/', views.tipo_editar, name='tipo_editar'),
    path('tipo/<int:pk>/eliminar/', views.tipo_eliminar, name='tipo_eliminar'),
    path('plan/nuevo/', views.plan_crear, name='plan_crear'),
    path('plan/<int:pk>/editar/', views.plan_editar, name='plan_editar'),
    path('plan/<int:pk>/eliminar/', views.plan_eliminar, name='plan_eliminar'),
    path('registro/nuevo/', views.registro_crear, name='registro_crear'),
    path('registro/<int:pk>/editar/', views.registro_editar, name='registro_editar'),
    path('registro/<int:pk>/eliminar/', views.registro_eliminar, name='registro_eliminar'),
]

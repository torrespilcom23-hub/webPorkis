from django.urls import path

from . import views

app_name = 'vacunas'

urlpatterns = [
    path('', views.aplicacion_lista, name='aplicaciones'),
    path('aplicar/', views.aplicacion_crear, name='aplicacion_crear'),
    path('aplicar/cerdo/<int:cerdo_pk>/', views.aplicacion_registrar_rapida, name='aplicacion_cerdo'),
    path('aplicacion/<int:pk>/refuerzo/', views.aplicacion_refuerzo, name='aplicacion_refuerzo'),
    path('aplicacion/<int:pk>/editar/', views.aplicacion_editar, name='aplicacion_editar'),
    path('aplicacion/<int:pk>/eliminar/', views.aplicacion_eliminar, name='aplicacion_eliminar'),
    path('catalogo/', views.vacuna_lista, name='catalogo'),
    path('catalogo/nuevo/', views.vacuna_crear, name='vacuna_crear'),
    path('catalogo/<int:pk>/editar/', views.vacuna_editar, name='vacuna_editar'),
    path('catalogo/<int:pk>/eliminar/', views.vacuna_eliminar, name='vacuna_eliminar'),
]

from django.urls import path

from . import views

app_name = 'inseminacion'

urlpatterns = [
    path('', views.inseminacion_index, name='index'),
    path('partos/', views.partos_lista, name='partos'),
    path('padrillos/', views.padrillos_lista, name='padrillos'),
    path('nueva/', views.inseminacion_crear, name='crear'),
    path('<int:pk>/editar/', views.inseminacion_editar, name='editar'),
    path('<int:pk>/eliminar/', views.inseminacion_eliminar, name='eliminar'),
    path('<int:pk>/diagnostico/', views.diagnostico_crear, name='diagnostico'),
    path('parto/nuevo/', views.parto_crear, name='parto_crear'),
    path('parto/<int:pk>/editar/', views.parto_editar, name='parto_editar'),
    path('parto/<int:pk>/eliminar/', views.parto_eliminar, name='parto_eliminar'),
    path('parto/<int:pk>/lechones/', views.parto_lechones, name='parto_lechones'),
    path('parto/<int:pk>/lechones/rapido/', views.parto_lechones_rapido, name='parto_lechones_rapido'),
    path('parto/<int:pk>/lechones/detallado/', views.parto_lechones_detallado, name='parto_lechones_detallado'),
    path('padrillo/nuevo/', views.padrillo_crear, name='padrillo_crear'),
    path('padrillo/<int:pk>/editar/', views.padrillo_editar, name='padrillo_editar'),
    path('padrillo/<int:pk>/eliminar/', views.padrillo_eliminar, name='padrillo_eliminar'),
]

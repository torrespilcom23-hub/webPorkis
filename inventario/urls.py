from django.urls import path

from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.producto_lista, name='lista'),
    path('nuevo/', views.producto_crear, name='crear'),
    path('<int:pk>/', views.producto_detalle, name='detalle'),
    path('<int:pk>/editar/', views.producto_editar, name='editar'),
    path('<int:pk>/eliminar/', views.producto_eliminar, name='eliminar'),
    path('movimientos/', views.movimientos_lista, name='movimientos'),
    path('movimientos/nuevo/', views.movimiento_crear, name='movimiento'),
    path('movimientos/<int:pk>/eliminar/', views.movimiento_eliminar, name='movimiento_eliminar'),
]

from django.urls import path

from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.reportes_index, name='index'),
    path('<str:tipo>/', views.reporte_ver, name='ver'),
    path('<str:tipo>/export/<str:formato>/', views.reporte_exportar, name='exportar'),
]

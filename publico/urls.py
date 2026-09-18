from django.urls import path

from . import views

app_name = 'publico'

urlpatterns = [
    path('', views.InicioView.as_view(), name='inicio'),
    path('servicios/', views.ServiciosView.as_view(), name='servicios'),
    path('contacto/', views.contacto_view, name='contacto'),
    path('contacto/exito/', views.contacto_exito_view, name='contacto_exito'),
]

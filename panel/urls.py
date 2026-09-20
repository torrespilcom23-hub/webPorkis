from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

app_name = 'panel'

urlpatterns = [
    path('login/', views.PanelLoginView.as_view(), name='login'),
    path('logout/', views.PanelLogoutView.as_view(), name='logout'),
    path('cambiar-password/', login_required(views.CambiarPasswordView.as_view()), name='cambiar_password'),
    path('', login_required(views.DashboardView.as_view()), name='dashboard'),
    path('mensajes/', views.mensajes_lista, name='mensajes'),
    path('mensajes/<int:pk>/', views.mensaje_detalle, name='mensaje_detalle'),
    path('mensajes/<int:pk>/eliminar/', views.mensaje_eliminar, name='mensaje_eliminar'),
    path('usuarios/', views.usuarios_lista, name='usuarios'),
    path('usuarios/nuevo/', views.usuario_crear, name='usuario_crear'),
    path('usuarios/<int:pk>/password/', views.usuario_reset_password, name='usuario_reset_password'),
    path('usuarios/<int:pk>/activo/', views.usuario_toggle_activo, name='usuario_toggle_activo'),
]

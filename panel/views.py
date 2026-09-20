import re
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView

from publico.models import MensajeContacto

from .decorators import admin_required, puede_acceder_panel, rol_panel
from .forms import OperadorCreateForm, ResetPasswordAdminForm
from .queries import resumen_dashboard


def _usuarios_panel():
    return (
        User.objects
        .filter(Q(is_superuser=True) | Q(groups__name__in=['admin', 'operador']))
        .distinct()
        .order_by('username')
    )


class PanelLoginView(LoginView):
    template_name = 'panel/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if not puede_acceder_panel(self.request.user):
            logout(self.request)
            messages.error(
                self.request,
                'Su cuenta no tiene acceso al panel. Solicite acceso al administrador.',
            )
            return redirect('panel:login')
        return response


class PanelLogoutView(LogoutView):
    next_page = 'publico:inicio'


class CambiarPasswordView(PasswordChangeView):
    template_name = 'panel/cambiar_password.html'
    success_url = reverse_lazy('panel:dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'Contraseña actualizada correctamente.')
        return super().form_valid(form)


class DashboardView(TemplateView):
    template_name = 'panel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(resumen_dashboard())
        return context


# ---------------------------------------------------------------------------
# Bandeja de mensajes de contacto
# ---------------------------------------------------------------------------

def _whatsapp_numero(telefono):
    digitos = re.sub(r'\D', '', telefono or '')
    if len(digitos) == 9:
        digitos = f'51{digitos}'
    return digitos if len(digitos) >= 10 else ''


def _enlaces_respuesta(mensaje):
    cuerpo = (
        f'Hola {mensaje.nombre},\n\n'
        f'Gracias por contactar a Granja Porkis.\n\n'
        f'---\n'
        f'Su consulta ({mensaje.created_at:%d/%m/%Y}):\n'
        f'{mensaje.mensaje}'
    )
    mailto = (
        f'mailto:{mensaje.email}'
        f'?subject={quote(f"Re: {mensaje.asunto}")}'
        f'&body={quote(cuerpo)}'
    )
    wa_url = None
    numero = _whatsapp_numero(mensaje.telefono)
    if numero:
        texto = (
            f'Hola {mensaje.nombre}, gracias por escribirnos sobre '
            f'"{mensaje.asunto}". '
        )
        wa_url = f'https://wa.me/{numero}?text={quote(texto)}'
    return mailto, wa_url


@login_required
def mensajes_lista(request):
    qs = MensajeContacto.objects.all()
    return render(request, 'panel/mensajes_lista.html', {
        'mensajes': qs,
        'total_mensajes': qs.count(),
        'sin_leer': qs.filter(leido=False).count(),
        'contacto_url': request.build_absolute_uri(reverse('publico:contacto')),
    })


@login_required
def mensaje_detalle(request, pk):
    mensaje = get_object_or_404(MensajeContacto, pk=pk)
    if not mensaje.leido:
        mensaje.leido = True
        mensaje.save(update_fields=['leido'])
    mailto, wa_url = _enlaces_respuesta(mensaje)
    return render(request, 'panel/mensaje_detalle.html', {
        'mensaje': mensaje,
        'mailto_url': mailto,
        'whatsapp_url': wa_url,
    })


@login_required
@admin_required
def mensaje_eliminar(request, pk):
    mensaje = get_object_or_404(MensajeContacto, pk=pk)
    if request.method == 'POST':
        mensaje.delete()
        messages.success(request, 'Mensaje eliminado.')
        return redirect('panel:mensajes')
    return render(request, 'panel/confirmar_eliminar.html', {
        'objeto': mensaje,
        'volver': 'panel:mensajes',
    })


# ---------------------------------------------------------------------------
# Gestión de usuarios del panel (solo administrador)
# ---------------------------------------------------------------------------

@login_required
@admin_required
def usuarios_lista(request):
    filas = [
        {
            'usuario': u,
            'rol': rol_panel(u),
            'activo': u.is_active,
        }
        for u in _usuarios_panel()
    ]
    return render(request, 'panel/usuarios_lista.html', {
        'filas': filas,
        'total': len(filas),
    })


@login_required
@admin_required
def usuario_crear(request):
    if request.method == 'POST':
        form = OperadorCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Usuario «{user.username}» creado con rol {rol_panel(user).lower()}.',
            )
            return redirect('panel:usuarios')
    else:
        form = OperadorCreateForm()
    return render(request, 'panel/usuario_form.html', {
        'form': form,
        'titulo': 'Nuevo usuario del panel',
    })


@login_required
@admin_required
def usuario_reset_password(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No puede modificar un superusuario.')
        return redirect('panel:usuarios')
    if request.method == 'POST':
        form = ResetPasswordAdminForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contraseña actualizada para «{usuario.username}».')
            return redirect('panel:usuarios')
    else:
        form = ResetPasswordAdminForm(usuario)
    return render(request, 'panel/usuario_reset_password.html', {
        'form': form,
        'usuario': usuario,
        'rol': rol_panel(usuario),
    })


@login_required
@admin_required
def usuario_toggle_activo(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method != 'POST':
        return redirect('panel:usuarios')
    if usuario.pk == request.user.pk:
        messages.error(request, 'No puede desactivar su propia cuenta.')
        return redirect('panel:usuarios')
    if usuario.is_superuser:
        messages.error(request, 'No se puede desactivar un superusuario desde aquí.')
        return redirect('panel:usuarios')
    usuario.is_active = not usuario.is_active
    usuario.save(update_fields=['is_active'])
    estado = 'activada' if usuario.is_active else 'desactivada'
    messages.success(request, f'Cuenta «{usuario.username}» {estado}.')
    return redirect('panel:usuarios')


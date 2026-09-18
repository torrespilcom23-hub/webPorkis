import re
from datetime import timedelta
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView

from alimentos.models import RegistroAlimentacion
from inseminacion.models import DIAS_DIAGNOSTICO, Inseminacion, Parto
from inventario.models import Producto
from publico.models import MensajeContacto
from registro.models import Cerdo, Corral
from vacunas.models import AplicacionVacuna

from .decorators import admin_required


class PanelLoginView(LoginView):
    template_name = 'panel/login.html'
    redirect_authenticated_user = True


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
        hoy = timezone.now().date()
        proxima_semana = hoy + timedelta(days=7)
        limite_diagnostico = hoy - timedelta(days=DIAS_DIAGNOSTICO)

        context.update({
            'hoy': hoy,
            'dias_diagnostico': DIAS_DIAGNOSTICO,
            'total_cerdos': Cerdo.objects.filter(estado='activo').count(),
            'productos_stock_bajo': Producto.objects.filter(stock_actual__lte=F('stock_minimo')).count(),
            'vacunas_pendientes': AplicacionVacuna.objects.filter(
                proxima_dosis__lte=proxima_semana,
            ).count(),
            'partos_mes': Parto.objects.filter(
                fecha__year=hoy.year,
                fecha__month=hoy.month,
            ).count(),
            'mensajes_nuevos': MensajeContacto.objects.filter(leido=False).count(),
            'diagnosticos_pendientes': Inseminacion.objects.filter(
                fecha__lte=limite_diagnostico,
                diagnostico__isnull=True,
            ).count(),
            'alertas_stock': Producto.objects.filter(stock_actual__lte=F('stock_minimo'))[:5],
            'alertas_vacunas': AplicacionVacuna.objects.filter(
                proxima_dosis__lte=proxima_semana,
            ).select_related('cerdo', 'vacuna')[:5],
            'alertas_diagnostico': Inseminacion.objects.filter(
                fecha__lte=limite_diagnostico,
                diagnostico__isnull=True,
            ).select_related('cerda')[:5],
            'inseminaciones_recientes': Inseminacion.objects.select_related('cerda')[:5],
            'registros_alimentacion': RegistroAlimentacion.objects.select_related('lote')[:5],
            'stock_por_corral': (
                Corral.objects
                .annotate(total=Count('cerdos', filter=Q(cerdos__estado='activo')))
                .filter(total__gt=0)
                .order_by('-total')[:5]
            ),
            'cerdos_sin_peso': Cerdo.objects.filter(
                estado='activo', peso_actual__isnull=True,
            ).count(),
        })
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


from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from .forms import ContactoForm
from .queries import resumen_operacion, servicios_para_plantilla


class InicioView(TemplateView):
    template_name = 'public/inicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['servicios'] = servicios_para_plantilla()
        context['cifras'] = resumen_operacion()
        return context


class ServiciosView(TemplateView):
    template_name = 'public/servicios.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['servicios'] = servicios_para_plantilla()
        return context


def contacto_view(request):
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            mensaje = form.save()
            send_mail(
                subject=f'[Porkis] Contacto: {mensaje.asunto}',
                message=(
                    f'Nombre: {mensaje.nombre}\n'
                    f'Email: {mensaje.email}\n'
                    f'Teléfono: {mensaje.telefono}\n'
                    f'Asunto: {mensaje.get_asunto_display() if hasattr(mensaje, "get_asunto_display") else mensaje.asunto}\n\n'
                    f'{mensaje.mensaje}'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_RECIPIENT_EMAIL],
                fail_silently=True,
            )
            return redirect('publico:contacto_exito')
    else:
        form = ContactoForm()

    return render(request, 'public/contacto.html', {'form': form})


def contacto_exito_view(request):
    return render(request, 'public/contacto_exito.html')

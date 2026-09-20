from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect

from .decorators import puede_acceder_panel


class PanelAccessMiddleware:
    """Bloquea el panel a usuarios sin grupo admin/operador (salvo login/logout)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith('/panel/') and request.user.is_authenticated:
            public_paths = ('/panel/login/', '/panel/logout/')
            if not path.startswith(public_paths) and not puede_acceder_panel(request.user):
                logout(request)
                messages.error(
                    request,
                    'Su cuenta no tiene permiso para acceder al panel. '
                    'Contacte al administrador.',
                )
                return redirect('panel:login')
        return self.get_response(request)

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def es_admin(user):
    """Administrador = superusuario o miembro del grupo 'admin'."""
    return user.is_superuser or user.groups.filter(name='admin').exists()


def puede_acceder_panel(user):
    """Usuarios con acceso al panel: superusuario, admin u operador."""
    if not user.is_authenticated:
        return False
    if user.is_active is False:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['admin', 'operador']).exists()


def rol_panel(user):
    """Etiqueta legible del rol principal."""
    if not user.is_authenticated:
        return ''
    if user.is_superuser:
        return 'Superusuario'
    if user.groups.filter(name='admin').exists():
        return 'Administrador'
    if user.groups.filter(name='operador').exists():
        return 'Operador'
    return 'Sin rol'


def admin_required(view_func):
    """Restringe la vista a usuarios con rol administrador.

    Aplicar después de @login_required.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not es_admin(request.user):
            messages.error(
                request,
                'No tiene permisos para esta acción. Se requiere rol administrador.',
            )
            return redirect(request.META.get('HTTP_REFERER') or '/panel/')
        return view_func(request, *args, **kwargs)
    return wrapper

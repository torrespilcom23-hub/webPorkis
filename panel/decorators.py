from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def es_admin(user):
    """Administrador = superusuario o miembro del grupo 'admin'."""
    return user.is_superuser or user.groups.filter(name='admin').exists()


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

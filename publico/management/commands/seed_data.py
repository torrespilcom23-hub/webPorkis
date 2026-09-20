from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Carga datos iniciales de demostración'

    def handle(self, *args, **options):
        grupo_admin, _ = Group.objects.get_or_create(name='admin')
        grupo_operador, _ = Group.objects.get_or_create(name='operador')
        self.stdout.write('Grupos de roles: admin, operador')

        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                'admin', 'admin@granjaporkis.com', 'admin123',
            )
            self.stdout.write(self.style.SUCCESS('Superusuario creado: admin / admin123'))
        else:
            admin_user = User.objects.get(username='admin')
            self.stdout.write('Superusuario admin ya existe.')
        if not admin_user.is_superuser:
            admin_user.is_superuser = True
            admin_user.save(update_fields=['is_superuser'])
            self.stdout.write(self.style.WARNING('Se activó is_superuser en admin.'))
        if not admin_user.groups.filter(name='admin').exists():
            admin_user.groups.add(grupo_admin)
            self.stdout.write('Usuario admin asignado al grupo admin.')

        if not User.objects.filter(username='operador').exists():
            operador = User.objects.create_user('operador', 'operador@granjaporkis.com', 'operador123')
            operador.groups.add(grupo_operador)
            self.stdout.write(self.style.SUCCESS('Operador creado: operador / operador123'))
        else:
            self.stdout.write('Usuario operador ya existe.')

        self.stdout.write(self.style.SUCCESS('Datos iniciales cargados correctamente.'))

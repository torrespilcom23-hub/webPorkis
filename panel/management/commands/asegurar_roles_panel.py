from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Arregla grupos admin/operador y el usuario admin si quedó mal.'

    def handle(self, *args, **options):
        grupo_admin, _ = Group.objects.get_or_create(name='admin')
        Group.objects.get_or_create(name='operador')

        for user in User.objects.filter(is_superuser=True):
            if not user.groups.filter(name='admin').exists():
                user.groups.add(grupo_admin)
                self.stdout.write(f'Superusuario {user.username} asignado al grupo admin')

        admin = User.objects.filter(username='admin').first()
        if admin and not admin.is_superuser:
            admin.is_superuser = True
            admin.save(update_fields=['is_superuser'])
            self.stdout.write(self.style.WARNING('Usuario admin marcado como superusuario.'))

        self.stdout.write(self.style.SUCCESS('Roles del panel verificados.'))

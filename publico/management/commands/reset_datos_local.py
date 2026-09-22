from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Borra todos los datos de la BD (tablas intactas) y vuelve a crear admin/operador.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Obligatorio: confirma que desea borrar todos los datos.',
        )

    def handle(self, *args, **options):
        if not options['force']:
            raise CommandError('Pide confirmación: python manage.py reset_datos_local --force')

        db = settings.DATABASES['default']
        engine = db.get('ENGINE', '').split('.')[-1]
        self.stdout.write(
            self.style.WARNING(
                f'Reinicio total de datos en {db.get("NAME")} ({engine}, host {db.get("HOST")})'
            )
        )

        call_command('flush', interactive=False, verbosity=1)
        self.stdout.write(self.style.SUCCESS('Tablas vaciadas (estructura intacta).'))

        call_command('seed_data')
        self.stdout.write(
            self.style.SUCCESS(
                'Listo. Use admin (ver README) u operador/operador123; cargue catalogos desde el panel.'
            )
        )

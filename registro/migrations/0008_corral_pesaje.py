import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def migrar_corrales_texto(apps, schema_editor):
    Cerdo = apps.get_model('registro', 'Cerdo')
    Corral = apps.get_model('registro', 'Corral')

    cache = {}
    for cerdo in Cerdo.objects.exclude(corral_texto='').exclude(corral_texto__isnull=True):
        nombre = (cerdo.corral_texto or '').strip()
        if not nombre:
            continue
        if nombre not in cache:
            cache[nombre], _ = Corral.objects.get_or_create(nombre=nombre)
        cerdo.corral_id = cache[nombre].pk
        cerdo.save(update_fields=['corral_id'])


def migrar_pesos_iniciales(apps, schema_editor):
    Cerdo = apps.get_model('registro', 'Cerdo')
    RegistroPeso = apps.get_model('registro', 'RegistroPeso')

    hoy = django.utils.timezone.now().date()
    for cerdo in Cerdo.objects.exclude(peso_actual__isnull=True):
        RegistroPeso.objects.create(
            cerdo_id=cerdo.pk,
            fecha=cerdo.fecha_ingreso or cerdo.fecha_nacimiento or hoy,
            peso_kg=cerdo.peso_actual,
            observaciones='Migración: peso inicial',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('registro', '0007_cerdo_fecha_salida_cerdo_precio_venta_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Corral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('capacidad', models.PositiveIntegerField(blank=True, help_text='Opcional. Cantidad máxima de cerdos que caben en este corral.', null=True, verbose_name='Capacidad (animales)')),
                ('observaciones', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Corral',
                'verbose_name_plural': 'Corrales',
                'ordering': ['nombre'],
            },
        ),
        migrations.RenameField(
            model_name='cerdo',
            old_name='corral',
            new_name='corral_texto',
        ),
        migrations.AddField(
            model_name='cerdo',
            name='corral',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cerdos', to='registro.corral', verbose_name='Corral'),
        ),
        migrations.RunPython(migrar_corrales_texto, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='cerdo',
            name='corral_texto',
        ),
        migrations.CreateModel(
            name='RegistroPeso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(default=django.utils.timezone.now)),
                ('peso_kg', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Peso (kg)')),
                ('observaciones', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cerdo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pesajes', to='registro.cerdo', verbose_name='Cerdo')),
            ],
            options={
                'verbose_name': 'Registro de peso',
                'verbose_name_plural': 'Registros de peso',
                'ordering': ['-fecha', '-pk'],
                'constraints': [models.CheckConstraint(condition=models.Q(('peso_kg__gte', 0)), name='pesaje_peso_no_negativo')],
            },
        ),
        migrations.RunPython(migrar_pesos_iniciales, migrations.RunPython.noop),
    ]

from django.db import migrations


CATEGORIAS_PERU = [
    # (nombre, descripcion, edad_min_dias, edad_max_dias)
    ('Lechón', 'Del nacimiento al destete (lactancia).', 0, 28),
    ('Gorrino destetado', 'Del destete hasta ~25 kg (etapa de crianza).', 29, 70),
    ('Engorde (cebo)', 'De ~25 kg hasta peso de venta (90-100 kg).', 71, 210),
    ('Chanchilla', 'Hembra joven seleccionada como reemplazo reproductivo.', 150, 240),
    ('Pie de cría', 'Reproductores seleccionados: marranas y verracos.', 240, None),
    ('Remate', 'Listos para venta o camal.', None, None),
]


def sembrar_categorias(apps, schema_editor):
    CategoriaCerdo = apps.get_model('registro', 'CategoriaCerdo')
    for nombre, descripcion, edad_min, edad_max in CATEGORIAS_PERU:
        CategoriaCerdo.objects.get_or_create(
            nombre=nombre,
            defaults={
                'descripcion': descripcion,
                'edad_min_dias': edad_min,
                'edad_max_dias': edad_max,
            },
        )


def engorde_a_activo(apps, schema_editor):
    """'En engorde' deja de ser un estado: pasa a ser una categoría."""
    Cerdo = apps.get_model('registro', 'Cerdo')
    Cerdo.objects.filter(estado='engorde').update(estado='activo')


def revertir(apps, schema_editor):
    pass  # no se revierte la semilla ni la normalización


class Migration(migrations.Migration):

    dependencies = [
        ('registro', '0004_categoriacerdo_alter_cerdo_estado_cerdo_categoria'),
    ]

    operations = [
        migrations.RunPython(engorde_a_activo, revertir),
        migrations.RunPython(sembrar_categorias, revertir),
    ]

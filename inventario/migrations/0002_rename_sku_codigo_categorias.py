from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='producto',
            old_name='sku',
            new_name='codigo',
        ),
        migrations.AlterField(
            model_name='producto',
            name='codigo',
            field=models.CharField(max_length=50, unique=True, verbose_name='Código'),
        ),
        migrations.AlterField(
            model_name='producto',
            name='categoria',
            field=models.CharField(
                choices=[
                    ('alimento', 'Alimentos y concentrados'),
                    ('medicamento', 'Medicamentos y vacunas'),
                    ('bioseguridad', 'Bioseguridad y desinfección'),
                    ('equipo', 'Equipos y herramientas'),
                    ('limpieza', 'Limpieza e higiene'),
                    ('reproductivo', 'Material reproductivo'),
                    ('combustible', 'Combustibles'),
                    ('otro', 'Otros'),
                ],
                max_length=20,
            ),
        ),
    ]

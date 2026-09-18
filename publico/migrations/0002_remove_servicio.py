from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publico', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Servicio',
        ),
    ]

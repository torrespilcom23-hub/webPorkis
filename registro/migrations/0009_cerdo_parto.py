import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inseminacion', '0001_initial'),
        ('registro', '0008_corral_pesaje'),
    ]

    operations = [
        migrations.AddField(
            model_name='cerdo',
            name='parto',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lechones_registrados',
                to='inseminacion.parto',
                verbose_name='Parto origen',
            ),
        ),
    ]

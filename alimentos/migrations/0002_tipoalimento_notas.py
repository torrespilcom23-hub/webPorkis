from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alimentos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipoalimento',
            name='notas',
            field=models.TextField(
                blank=True,
                help_text='Notas de uso: edad recomendada, forma de servir, etc.',
                verbose_name='Indicaciones',
            ),
        ),
    ]

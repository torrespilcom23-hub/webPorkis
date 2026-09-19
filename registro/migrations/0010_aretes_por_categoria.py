import re
import unicodedata

from django.db import migrations, models

_PREFIJO_SIN_CATEGORIA = 'SC'
_STOPWORDS = frozenset({'de', 'del', 'la', 'las', 'el', 'los', 'y', 'en', 'a', 'al'})


def _normalizar_texto(texto):
    texto = unicodedata.normalize('NFD', texto or '')
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.strip()


def _palabras_significativas(nombre):
    limpio = re.sub(r'[()[\]/,;]', ' ', _normalizar_texto(nombre))
    tokens = [t for t in limpio.split() if t]
    significativas = [t for t in tokens if t.lower() not in _STOPWORDS]
    return significativas or tokens


def prefijo_categoria_nombre(nombre):
    if not nombre:
        return _PREFIJO_SIN_CATEGORIA
    palabras = _palabras_significativas(nombre)
    if not palabras:
        return _PREFIJO_SIN_CATEGORIA
    if len(palabras) >= 2:
        return (palabras[0][0] + palabras[1][0]).upper()
    palabra = palabras[0]
    if len(palabra) >= 2:
        return palabra[:2].upper()
    return (palabra[0] * 2).upper()


def remapear_aretes_existentes(apps, schema_editor):
    Cerdo = apps.get_model('registro', 'Cerdo')
    CategoriaCerdo = apps.get_model('registro', 'CategoriaCerdo')
    CorrelativoArete = apps.get_model('registro', 'CorrelativoArete')

    CorrelativoArete.objects.all().delete()

    categorias = {c.pk: c.nombre for c in CategoriaCerdo.objects.all()}
    grupos = {}

    for cerdo in Cerdo.objects.order_by('pk'):
        nombre_cat = categorias.get(cerdo.categoria_id) if cerdo.categoria_id else None
        prefijo = prefijo_categoria_nombre(nombre_cat)
        grupos.setdefault(prefijo, []).append(cerdo.pk)

    for prefijo, pks in grupos.items():
        for numero, pk in enumerate(pks, start=1):
            Cerdo.objects.filter(pk=pk).update(arete=f'{prefijo}-{numero:04d}')
        CorrelativoArete.objects.create(prefijo=prefijo, ultimo=len(pks))


class Migration(migrations.Migration):

    dependencies = [
        ('registro', '0009_cerdo_parto'),
    ]

    operations = [
        migrations.AddField(
            model_name='correlativoarete',
            name='prefijo',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
        migrations.RunPython(remapear_aretes_existentes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='correlativoarete',
            name='prefijo',
            field=models.CharField(max_length=10, unique=True),
        ),
        migrations.AlterField(
            model_name='cerdo',
            name='arete',
            field=models.CharField(
                blank=True,
                help_text='Se genera automáticamente según categoría (ej.: CH-0001).',
                max_length=50,
                unique=True,
                verbose_name='Arete / Código',
            ),
        ),
    ]

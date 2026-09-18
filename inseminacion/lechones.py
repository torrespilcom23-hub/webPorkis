"""Alta de lechones en Registro a partir de un parto."""

from django.db import transaction

from registro.models import CategoriaCerdo, Cerdo, Lote, RegistroPeso

from .models import Parto


def _categoria_lechon():
    return CategoriaCerdo.objects.filter(nombre__iexact='Lechón').first()


def _crear_lote_camada(parto):
    madre = parto.madre
    nombre = f'Camada {madre.arete} {parto.fecha:%d-%m-%Y}'
    return Lote.objects.create(
        nombre=nombre,
        corral=madre.corral.nombre if madre.corral else '',
        fecha_ingreso=parto.fecha,
        observaciones=f'Generado desde parto id={parto.pk}',
    )


@transaction.atomic
def registrar_lechones(
    parto,
    *,
    items,
    raza,
    raza_otro='',
    categoria=None,
    corral=None,
    lote=None,
    crear_lote_camada=False,
):
    """
    Crea cerdos en Registro vinculados al parto.

    items: lista de dicts con keys sexo (M/H), peso_actual (opcional), observaciones (opcional)
    Retorna lista de Cerdo creados.
    """
    if not parto.puede_dar_alta_lechones:
        raise ValueError('No quedan lechones por dar de alta para este parto.')

    pendientes = parto.lechones_pendientes_alta
    if len(items) > pendientes:
        raise ValueError(
            f'Solo puede registrar {pendientes} lechón(es) más '
            f'({parto.lechones_en_registro} de {parto.lechones_vivos} ya en Registro).',
        )

    madre = parto.madre
    categoria = categoria or _categoria_lechon()
    if crear_lote_camada and lote is None:
        lote = _crear_lote_camada(parto)
    elif lote is None:
        lote = madre.lote

    creados = []
    for item in items:
        cerdo = Cerdo(
            raza=raza,
            raza_otro=raza_otro if raza == Cerdo.Raza.OTRO else '',
            sexo=item['sexo'],
            fecha_nacimiento=parto.fecha,
            categoria=categoria,
            corral=corral if corral is not None else madre.corral,
            lote=lote,
            madre=madre,
            parto=parto,
            estado=Cerdo.Estado.ACTIVO,
            observaciones=item.get('observaciones', ''),
        )
        peso = item.get('peso_actual')
        if peso is not None:
            cerdo.peso_actual = peso
        cerdo.save()

        if peso is not None:
            RegistroPeso.objects.create(
                cerdo=cerdo,
                fecha=parto.fecha,
                peso_kg=peso,
                observaciones='Peso al nacer',
            )
        creados.append(cerdo)

    return creados

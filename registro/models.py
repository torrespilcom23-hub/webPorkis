from django.db import models
from django.utils import timezone


class CorrelativoArete(models.Model):
    """Contador por prefijo de categoría (CH-0001, LE-0002, SC-0001...)."""

    prefijo = models.CharField(max_length=10, unique=True)
    ultimo = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Correlativo de arete'
        verbose_name_plural = 'Correlativos de arete'

    def __str__(self):
        return f'{self.prefijo} (último {self.ultimo})'


class CategoriaCerdo(models.Model):
    """Categoría del cerdo según etapa/función (Lechón, Engorde, Pie de cría...).

    Catálogo administrable por el usuario desde el panel.
    """

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)
    edad_min_dias = models.PositiveIntegerField(
        'Edad mínima (días)', null=True, blank=True,
        help_text='Opcional. Referencia para saber cuándo un cerdo entra en esta categoría.',
    )
    edad_max_dias = models.PositiveIntegerField(
        'Edad máxima (días)', null=True, blank=True,
        help_text='Opcional. Referencia para saber cuándo un cerdo sale de esta categoría.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Categoría de cerdo'
        verbose_name_plural = 'Categorías de cerdos'

    def __str__(self):
        return self.nombre


class Corral(models.Model):
    """Catálogo de corrales / ubicaciones físicas en la granja."""

    nombre = models.CharField(max_length=100, unique=True)
    capacidad = models.PositiveIntegerField(
        'Capacidad (animales)', null=True, blank=True,
        help_text='Opcional. Cantidad máxima de cerdos que caben en este corral.',
    )
    observaciones = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Corral'
        verbose_name_plural = 'Corrales'

    def __str__(self):
        return self.nombre


class Lote(models.Model):
    nombre = models.CharField(max_length=100)
    corral = models.CharField(max_length=100, blank=True)
    fecha_ingreso = models.DateField()
    meta_peso = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_ingreso']
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'

    def __str__(self):
        return self.nombre


class Cerdo(models.Model):
    class Sexo(models.TextChoices):
        MACHO = 'M', 'Macho'
        HEMBRA = 'H', 'Hembra'

    class Estado(models.TextChoices):
        ACTIVO = 'activo', 'En granja'
        VENDIDO = 'vendido', 'Vendido'
        FALLECIDO = 'fallecido', 'Fallecido'

    class Raza(models.TextChoices):
        LANDRACE = 'landrace', 'Landrace'
        YORKSHIRE = 'yorkshire', 'Yorkshire'
        DUROC = 'duroc', 'Duroc'
        HAMPSHIRE = 'hampshire', 'Hampshire'
        PIETRAN = 'pietran', 'Pietrán'
        BERKSHIRE = 'berkshire', 'Berkshire'
        CRUCE = 'cruce', 'Cruce (mestizo)'
        CRIOLLO = 'criollo', 'Criollo'
        OTRO = 'otro', 'Otro'

    arete = models.CharField(
        'Arete / Código', max_length=50, unique=True, blank=True,
        help_text='Se genera automáticamente según categoría (ej.: CH-0001).',
    )
    nombre = models.CharField(max_length=100, blank=True)
    raza = models.CharField(max_length=20, choices=Raza.choices)
    raza_otro = models.CharField(
        '¿Cuál raza?', max_length=100, blank=True,
        help_text='Completar solo si elegiste "Otro".',
    )
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    fecha_nacimiento = models.DateField()
    fecha_ingreso = models.DateField(
        null=True, blank=True,
        help_text='Dejar vacío si nació en la granja.',
    )
    peso_actual = models.DecimalField('Peso actual (kg)', max_digits=8, decimal_places=2, null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ACTIVO,
        help_text=(
            'En granja: el animal vive en la granja. '
            'Vendido/Fallecido: ya no está en la granja.'
        ),
    )
    categoria = models.ForeignKey(
        CategoriaCerdo, on_delete=models.PROTECT, null=True, blank=True,
        related_name='cerdos', verbose_name='Categoría',
        help_text='Etapa o función del cerdo (Lechón, Engorde, Pie de cría...).',
    )
    corral = models.ForeignKey(
        Corral, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cerdos', verbose_name='Corral',
    )
    fecha_salida = models.DateField(
        'Fecha de salida', null=True, blank=True,
        help_text='Fecha de venta o fallecimiento (solo si ya no está en la granja).',
    )
    precio_venta = models.DecimalField(
        'Precio de venta (S/.)', max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Solo si el cerdo fue vendido.',
    )
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True, related_name='cerdos')
    parto = models.ForeignKey(
        'inseminacion.Parto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lechones_registrados',
        verbose_name='Parto origen',
    )
    madre = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='crias')
    padre = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='descendientes')
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['arete']
        verbose_name = 'Cerdo'
        verbose_name_plural = 'Cerdos'
        constraints = [
            models.CheckConstraint(
                check=models.Q(peso_actual__gte=0), name='cerdo_peso_no_negativo',
            ),
            models.CheckConstraint(
                check=models.Q(precio_venta__gte=0), name='cerdo_precio_venta_no_negativo',
            ),
        ]

    def __str__(self):
        return f'{self.arete} ({self.raza_display})'

    @property
    def raza_display(self):
        """Raza legible; si es 'Otro' muestra el texto personalizado."""
        if self.raza == self.Raza.OTRO and self.raza_otro:
            return self.raza_otro
        return self.get_raza_display()

    def save(self, *args, **kwargs):
        from .aretes import generar_arete

        categoria_cambio = False
        if self.pk:
            anterior = (
                Cerdo.objects
                .filter(pk=self.pk)
                .values_list('categoria_id', flat=True)
                .first()
            )
            categoria_cambio = anterior != self.categoria_id

        if not self.arete or categoria_cambio:
            self.arete = generar_arete(self.categoria)
        super().save(*args, **kwargs)

    @property
    def edad_dias(self):
        if not self.fecha_nacimiento:
            return None
        return (timezone.now().date() - self.fecha_nacimiento).days

    @property
    def edad_display(self):
        """Edad legible: '45 días', '3 meses', '1 año'."""
        dias = self.edad_dias
        if dias is None:
            return '—'
        if dias < 60:
            return f'{dias} días'
        meses = dias // 30
        if meses < 24:
            return f'{meses} mes' if meses == 1 else f'{meses} meses'
        anios = dias // 365
        return f'{anios} año' if anios == 1 else f'{anios} años'


class RegistroPeso(models.Model):
    """Historial de pesajes; el peso actual del cerdo se deriva del último por fecha."""

    cerdo = models.ForeignKey(
        Cerdo, on_delete=models.CASCADE, related_name='pesajes',
        verbose_name='Cerdo',
    )
    fecha = models.DateField(default=timezone.now)
    peso_kg = models.DecimalField('Peso (kg)', max_digits=8, decimal_places=2)
    observaciones = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-pk']
        verbose_name = 'Registro de peso'
        verbose_name_plural = 'Registros de peso'
        constraints = [
            models.CheckConstraint(
                check=models.Q(peso_kg__gte=0), name='pesaje_peso_no_negativo',
            ),
        ]

    def __str__(self):
        return f'{self.cerdo.arete} — {self.peso_kg} kg ({self.fecha})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        sincronizar_peso_actual(self.cerdo)

    def delete(self, *args, **kwargs):
        cerdo = self.cerdo
        super().delete(*args, **kwargs)
        sincronizar_peso_actual(cerdo)


def sincronizar_peso_actual(cerdo):
    """Actualiza Cerdo.peso_actual con el pesaje más reciente por fecha."""
    ultimo = (
        RegistroPeso.objects
        .filter(cerdo=cerdo)
        .order_by('-fecha', '-pk')
        .first()
    )
    nuevo = ultimo.peso_kg if ultimo else None
    if cerdo.peso_actual != nuevo:
        Cerdo.objects.filter(pk=cerdo.pk).update(peso_actual=nuevo)

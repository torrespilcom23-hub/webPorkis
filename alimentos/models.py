from django.conf import settings
from django.db import models


class TipoAlimento(models.Model):
    nombre = models.CharField(max_length=200)
    proteina_pct = models.DecimalField('Proteína (%)', max_digits=5, decimal_places=2, null=True, blank=True)
    proveedor = models.CharField(max_length=200, blank=True)
    costo_por_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notas = models.TextField(
        'Indicaciones',
        blank=True,
        help_text='Notas de uso: edad recomendada, forma de servir, etc.',
    )

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Tipo de alimento'
        verbose_name_plural = 'Tipos de alimento'

    def __str__(self):
        return self.nombre


class PlanAlimentacion(models.Model):
    class Etapa(models.TextChoices):
        DESTETE = 'destete', 'Destete'
        CRECIMIENTO = 'crecimiento', 'Crecimiento'
        ENGORDE = 'engorde', 'Engorde'
        GESTACION = 'gestacion', 'Gestación'
        LACTANCIA = 'lactancia', 'Lactancia'

    lote = models.ForeignKey('registro.Lote', on_delete=models.CASCADE, related_name='planes_alimentacion')
    tipo_alimento = models.ForeignKey(TipoAlimento, on_delete=models.PROTECT)
    cantidad_diaria_kg = models.DecimalField(max_digits=8, decimal_places=2)
    etapa = models.CharField(max_length=20, choices=Etapa.choices)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['lote', 'etapa']
        verbose_name = 'Plan de alimentación'
        verbose_name_plural = 'Planes de alimentación'

    def __str__(self):
        return f'{self.lote.nombre} — {self.get_etapa_display()}'


class RegistroAlimentacion(models.Model):
    fecha = models.DateField()
    lote = models.ForeignKey('registro.Lote', on_delete=models.CASCADE, related_name='registros_alimentacion')
    tipo_alimento = models.ForeignKey(TipoAlimento, on_delete=models.PROTECT)
    cantidad_servida_kg = models.DecimalField(max_digits=8, decimal_places=2)
    cantidad_sobrante_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Registro de alimentación'
        verbose_name_plural = 'Registros de alimentación'

    def __str__(self):
        return f'{self.lote.nombre} — {self.fecha}'

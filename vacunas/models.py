from django.conf import settings
from django.db import models


class Vacuna(models.Model):
    nombre = models.CharField(max_length=200)
    intervalo_dias = models.PositiveIntegerField(null=True, blank=True, help_text='Días hasta refuerzo')
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Vacuna'
        verbose_name_plural = 'Vacunas'

    def __str__(self):
        return self.nombre


class AplicacionVacuna(models.Model):
    cerdo = models.ForeignKey('registro.Cerdo', on_delete=models.CASCADE, related_name='vacunas')
    vacuna = models.ForeignKey(Vacuna, on_delete=models.PROTECT)
    fecha_aplicacion = models.DateField()
    dosis = models.CharField(max_length=100)
    lote_medicamento = models.CharField(max_length=100, blank=True)
    proxima_dosis = models.DateField(null=True, blank=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_aplicacion']
        verbose_name = 'Aplicación de vacuna'
        verbose_name_plural = 'Aplicaciones de vacuna'

    def __str__(self):
        return f'{self.vacuna.nombre} — {self.cerdo.arete}'

    @property
    def pendiente(self):
        if self.proxima_dosis:
            from django.utils import timezone
            return self.proxima_dosis <= timezone.now().date()
        return False

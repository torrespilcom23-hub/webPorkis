from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

GESTACION_DIAS = 114
DIAS_DIAGNOSTICO = 21


class Padrillo(models.Model):
    class Origen(models.TextChoices):
        INTERNO = 'interno', 'Interno'
        EXTERNO = 'externo', 'Externo'

    codigo = models.CharField(max_length=50, unique=True)
    raza = models.CharField(max_length=100)
    origen = models.CharField(max_length=20, choices=Origen.choices, default=Origen.INTERNO)
    stock_pajuelas = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['codigo']
        verbose_name = 'Padrillo'
        verbose_name_plural = 'Padrillos'

    def __str__(self):
        return f'{self.codigo} ({self.raza})'


class Inseminacion(models.Model):
    class Tipo(models.TextChoices):
        NATURAL = 'natural', 'Natural'
        ARTIFICIAL = 'artificial', 'Artificial'

    cerda = models.ForeignKey('registro.Cerdo', on_delete=models.PROTECT, related_name='inseminaciones')
    fecha = models.DateField()
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    padrillo = models.ForeignKey(Padrillo, on_delete=models.PROTECT, null=True, blank=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Inseminación'
        verbose_name_plural = 'Inseminaciones'

    def __str__(self):
        return f'{self.cerda.arete} — {self.fecha}'

    @property
    def dias_desde_servicio(self):
        return (timezone.now().date() - self.fecha).days

    @property
    def tiene_diagnostico(self):
        try:
            self.diagnostico
        except DiagnosticoPrenez.DoesNotExist:
            return False
        return True

    @property
    def requiere_diagnostico(self):
        return self.dias_desde_servicio >= DIAS_DIAGNOSTICO and not self.tiene_diagnostico

    @property
    def estado_diagnostico(self):
        """espera | vencido | positivo | negativo | dudoso"""
        if self.tiene_diagnostico:
            return self.diagnostico.resultado
        if self.dias_desde_servicio >= DIAS_DIAGNOSTICO:
            return 'vencido'
        return 'espera'

    @property
    def fecha_parto_estimada(self):
        try:
            diag = self.diagnostico
        except DiagnosticoPrenez.DoesNotExist:
            return None
        if diag.resultado == DiagnosticoPrenez.Resultado.POSITIVO:
            return self.fecha + timedelta(days=GESTACION_DIAS)
        return None

    @property
    def pendiente_parto(self):
        return self.fecha_parto_estimada is not None and not self.partos.exists()

    @property
    def dias_restantes_diagnostico(self):
        """Días que faltan para el control recomendado (21 d). None si ya hay diagnóstico."""
        if self.tiene_diagnostico:
            return None
        return max(0, DIAS_DIAGNOSTICO - self.dias_desde_servicio)

    @property
    def dias_restantes_parto(self):
        """Días hasta la fecha estimada de parto. Negativo = pasó la fecha sin registrar parto."""
        if not self.fecha_parto_estimada or self.partos.exists():
            return None
        return (self.fecha_parto_estimada - timezone.now().date()).days

    @property
    def puede_registrar_diagnostico(self):
        """True mientras no exista registro de diagnóstico."""
        return not self.tiene_diagnostico


class DiagnosticoPrenez(models.Model):
    class Resultado(models.TextChoices):
        POSITIVO = 'positivo', 'Positivo'
        NEGATIVO = 'negativo', 'Negativo'
        DUDOSO = 'dudoso', 'Dudoso'

    inseminacion = models.OneToOneField(Inseminacion, on_delete=models.CASCADE, related_name='diagnostico')
    fecha = models.DateField()
    resultado = models.CharField(max_length=20, choices=Resultado.choices)
    metodo = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Diagnóstico de preñez'
        verbose_name_plural = 'Diagnósticos de preñez'

    def __str__(self):
        return f'{self.inseminacion} — {self.get_resultado_display()}'


class Parto(models.Model):
    inseminacion = models.ForeignKey(Inseminacion, on_delete=models.PROTECT, related_name='partos')
    fecha = models.DateField()
    lechones_vivos = models.PositiveIntegerField()
    lechones_muertos = models.PositiveIntegerField(default=0)
    lechones_destetados = models.PositiveIntegerField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Parto'
        verbose_name_plural = 'Partos'

    def __str__(self):
        return f'Parto {self.fecha} — {self.inseminacion.cerda.arete}'

    @property
    def lechones_en_registro(self):
        return self.lechones_registrados.count()

    @property
    def lechones_pendientes_alta(self):
        return max(0, self.lechones_vivos - self.lechones_en_registro)

    @property
    def puede_dar_alta_lechones(self):
        return self.lechones_pendientes_alta > 0

    @property
    def madre(self):
        return self.inseminacion.cerda

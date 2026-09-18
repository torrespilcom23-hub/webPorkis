from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class CategoriaProducto(models.TextChoices):
    ALIMENTO = 'alimento', 'Alimentos y concentrados'
    MEDICAMENTO = 'medicamento', 'Medicamentos y vacunas'
    BIOSEGURIDAD = 'bioseguridad', 'Bioseguridad y desinfección'
    EQUIPO = 'equipo', 'Equipos y herramientas'
    LIMPIEZA = 'limpieza', 'Limpieza e higiene'
    REPRODUCTIVO = 'reproductivo', 'Material reproductivo'
    COMBUSTIBLE = 'combustible', 'Combustibles'
    OTRO = 'otro', 'Otros'


PREFIJOS_CATEGORIA = {
    'alimento': 'ALM',
    'medicamento': 'MED',
    'bioseguridad': 'BIO',
    'equipo': 'EQP',
    'limpieza': 'LIM',
    'reproductivo': 'REP',
    'combustible': 'COM',
    'otro': 'OTR',
}


class CorrelativoCodigo(models.Model):
    """Contador por categoría para autogenerar códigos de producto."""

    categoria = models.CharField(max_length=20, unique=True)
    ultimo = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Correlativo de código'
        verbose_name_plural = 'Correlativos de código'


def generar_codigo(categoria):
    """Genera el siguiente código para la categoría, p. ej. ALM-0001.

    Usa select_for_update para ser seguro ante registros concurrentes.
    """
    prefijo = PREFIJOS_CATEGORIA.get(categoria, 'OTR')
    with transaction.atomic():
        correlativo, _ = (
            CorrelativoCodigo.objects
            .select_for_update()
            .get_or_create(categoria=categoria)
        )
        correlativo.ultimo += 1
        correlativo.save(update_fields=['ultimo'])
        return f'{prefijo}-{correlativo.ultimo:04d}'


class Producto(models.Model):
    codigo = models.CharField(
        'Código', max_length=50, unique=True, blank=True,
        help_text='Se genera automáticamente según la categoría.',
    )
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=20, choices=CategoriaProducto.choices)
    unidad = models.CharField(max_length=20, default='unidad')
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proveedor = models.CharField(max_length=200, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        constraints = [
            models.CheckConstraint(
                check=models.Q(stock_actual__gte=0), name='producto_stock_actual_no_negativo',
            ),
            models.CheckConstraint(
                check=models.Q(stock_minimo__gte=0), name='producto_stock_minimo_no_negativo',
            ),
        ]

    def __str__(self):
        return f'{self.codigo} — {self.nombre}'

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = generar_codigo(self.categoria)
        super().save(*args, **kwargs)

    @property
    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo

    @property
    def valor_total(self):
        """Valorización: stock actual × precio unitario."""
        if self.precio_unitario is not None:
            return self.stock_actual * self.precio_unitario
        return None

    @property
    def vencido(self):
        if self.fecha_vencimiento:
            return self.fecha_vencimiento < timezone.now().date()
        return False

    @property
    def por_vencer(self):
        """Vence dentro de los próximos 30 días."""
        if self.fecha_vencimiento and not self.vencido:
            delta = (self.fecha_vencimiento - timezone.now().date()).days
            return delta <= 30
        return False


class MovimientoInventario(models.Model):
    class TipoMovimiento(models.TextChoices):
        ENTRADA = 'entrada', 'Entrada'
        SALIDA = 'salida', 'Salida'

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TipoMovimiento.choices)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    motivo = models.CharField(max_length=300, blank=True, default='')
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Movimiento de inventario'
        verbose_name_plural = 'Movimientos de inventario'
        constraints = [
            models.CheckConstraint(
                check=models.Q(cantidad__gt=0), name='movimiento_cantidad_positiva',
            ),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.producto.nombre}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self._ajustar_stock(revertir=False)

    def delete(self, *args, **kwargs):
        """Al eliminar un movimiento se revierte su efecto en el stock."""
        self._ajustar_stock(revertir=True)
        super().delete(*args, **kwargs)

    def _ajustar_stock(self, revertir):
        producto = self.producto
        entrada = self.tipo == self.TipoMovimiento.ENTRADA
        if entrada != revertir:
            producto.stock_actual += self.cantidad
        else:
            producto.stock_actual -= self.cantidad
        producto.save(update_fields=['stock_actual', 'updated_at'])

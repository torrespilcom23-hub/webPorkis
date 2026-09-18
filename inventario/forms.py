from django import forms
from django.core.exceptions import ValidationError

from .models import MovimientoInventario, Producto


class ProductoForm(forms.ModelForm):
    """El código se autogenera según la categoría; no se edita manualmente."""

    class Meta:
        model = Producto
        fields = [
            'nombre', 'categoria', 'unidad', 'stock_actual',
            'stock_minimo', 'precio_unitario', 'proveedor', 'fecha_vencimiento',
        ]
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'stock_actual': forms.NumberInput(attrs={'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'min': '0'}),
            'precio_unitario': forms.NumberInput(attrs={
                'min': '0', 'inputmode': 'decimal', 'placeholder': '0.00',
            }),
        }


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['producto', 'tipo', 'cantidad', 'motivo']
        labels = {
            'tipo': '¿Qué desea registrar?',
            'motivo': 'Motivo (opcional)',
        }
        widgets = {
            'motivo': forms.TextInput(attrs={
                'placeholder': 'Ej.: Compra en agroveterinaria, uso en corral 2...',
            }),
        }

    def __init__(self, *args, producto_fijo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].choices = [
            ('entrada', '➕ Entrada — compra o ingreso de stock'),
            ('salida', '➖ Salida — uso o consumo'),
        ]
        self.fields['motivo'].required = False
        if producto_fijo is not None:
            # El producto ya viene elegido desde su ficha: se oculta el selector
            self.fields['producto'].widget = forms.HiddenInput()
            self.fields['producto'].initial = producto_fijo.pk
            self.fields['cantidad'].label = f'Cantidad ({producto_fijo.unidad})'
            self.fields['cantidad'].help_text = (
                f'Cuántas {producto_fijo.unidad} ingresan (entrada) '
                f'o se consumen (salida).'
            )

    def clean(self):
        cleaned = super().clean()
        producto = cleaned.get('producto')
        tipo = cleaned.get('tipo')
        cantidad = cleaned.get('cantidad')

        if cantidad is not None and cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor a cero.')

        if producto and tipo == MovimientoInventario.TipoMovimiento.SALIDA and cantidad:
            if cantidad > producto.stock_actual:
                raise ValidationError(
                    f'Stock insuficiente para "{producto.nombre}". '
                    f'Disponible: {producto.stock_actual} {producto.unidad}.'
                )
        return cleaned

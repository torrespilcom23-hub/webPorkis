from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import CategoriaCerdo, Cerdo, Corral, Lote, RegistroPeso


class CategoriaCerdoForm(forms.ModelForm):
    class Meta:
        model = CategoriaCerdo
        fields = ['nombre', 'descripcion', 'edad_min_dias', 'edad_max_dias']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej.: Lechón, Engorde, Pie de cría...'}),
            'descripcion': forms.TextInput(attrs={
                'placeholder': 'Ej.: Del nacimiento al destete (lactancia).',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        edad_min = cleaned.get('edad_min_dias')
        edad_max = cleaned.get('edad_max_dias')
        if edad_min is not None and edad_max is not None and edad_max < edad_min:
            raise ValidationError(
                'La edad máxima no puede ser menor que la edad mínima.'
            )
        return cleaned


class CorralForm(forms.ModelForm):
    class Meta:
        model = Corral
        fields = ['nombre', 'capacidad', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej.: Corral 1, Gestación, Engorde...'}),
            'capacidad': forms.NumberInput(attrs={'min': '1', 'placeholder': 'Opcional'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Ubicación, notas...'}),
        }


class PesajeForm(forms.ModelForm):
    class Meta:
        model = RegistroPeso
        fields = ['fecha', 'peso_kg', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'peso_kg': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Opcional'}),
        }

    def __init__(self, *args, cerdo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cerdo = cerdo

    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get('fecha')
        if self.cerdo and fecha:
            hoy = timezone.now().date()
            if fecha > hoy:
                self.add_error('fecha', 'La fecha no puede ser futura.')
            elif self.cerdo.fecha_nacimiento and fecha < self.cerdo.fecha_nacimiento:
                self.add_error('fecha', 'La fecha no puede ser anterior al nacimiento.')
        return cleaned


class CerdoForm(forms.ModelForm):
    """El arete se autogenera por categoría (CH-0001, LE-0001…); no se edita manualmente."""

    class Meta:
        model = Cerdo
        fields = [
            'nombre', 'raza', 'raza_otro', 'sexo', 'categoria', 'fecha_nacimiento',
            'fecha_ingreso', 'peso_actual', 'estado', 'fecha_salida', 'precio_venta',
            'corral', 'lote', 'observaciones',
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_salida': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'peso_actual': forms.NumberInput(attrs={'min': '0', 'placeholder': '0.00'}),
            'precio_venta': forms.NumberInput(attrs={
                'min': '0', 'step': '0.01', 'placeholder': '0.00', 'inputmode': 'decimal',
            }),
            'raza_otro': forms.TextInput(attrs={'placeholder': 'Escribe la raza, ej.: Large White'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].empty_label = '— Sin categoría —'
        self.fields['categoria'].help_text = (
            'Define el prefijo del arete (ej. Chanchilla → CH-0001). Sin categoría usa SC. '
            'Al cambiar la categoría en edición, el arete se actualiza automáticamente.'
        )
        self.fields['corral'].empty_label = '— Sin corral —'
        self.fields['corral'].help_text = (
            'Ubicación física del cerdo. Administre corrales desde '
            'Registro → Corrales.'
        )
        self.fields['lote'].empty_label = '— Sin lote —'
        if Lote.objects.exists():
            self.fields['lote'].help_text = (
                'Grupo de cerdos que ingresaron juntos y se manejan como unidad '
                '(ej.: "Engorde Setiembre"). Sirve para el control de alimentación '
                'por grupo en el módulo Alimentos.'
            )
        else:
            self.fields['lote'].help_text = (
                'Aún no hay lotes registrados. Un lote es un grupo de cerdos que '
                'ingresaron juntos (ej.: "Engorde Setiembre"); sirve para el control '
                'de alimentación por grupo.'
            )
        if self.instance.pk:
            self.fields['peso_actual'].disabled = True
            self.fields['peso_actual'].help_text = (
                'Use el botón “Pesar” en la lista para registrar pesajes.'
            )

    def clean(self):
        cleaned = super().clean()
        nacimiento = cleaned.get('fecha_nacimiento')
        ingreso = cleaned.get('fecha_ingreso')
        raza = cleaned.get('raza')
        raza_otro = (cleaned.get('raza_otro') or '').strip()

        if nacimiento and nacimiento > timezone.now().date():
            raise ValidationError('La fecha de nacimiento no puede ser futura.')

        if nacimiento and ingreso and ingreso < nacimiento:
            raise ValidationError(
                'La fecha de ingreso no puede ser anterior a la de nacimiento.'
            )

        if raza == Cerdo.Raza.OTRO:
            if not raza_otro:
                self.add_error('raza_otro', 'Especifique la raza.')
            else:
                cleaned['raza_otro'] = raza_otro
        else:
            cleaned['raza_otro'] = ''

        estado = cleaned.get('estado')
        salida = cleaned.get('fecha_salida')
        if estado == Cerdo.Estado.ACTIVO:
            cleaned['fecha_salida'] = None
            cleaned['precio_venta'] = None
        else:
            if not salida:
                self.add_error(
                    'fecha_salida',
                    'Indique la fecha de venta o fallecimiento.',
                )
            else:
                hoy = timezone.now().date()
                if salida > hoy:
                    self.add_error('fecha_salida', 'La fecha de salida no puede ser futura.')
                elif nacimiento and salida < nacimiento:
                    self.add_error(
                        'fecha_salida',
                        'La fecha de salida no puede ser anterior a la de nacimiento.',
                    )
            if estado == Cerdo.Estado.FALLECIDO:
                cleaned['precio_venta'] = None
        return cleaned


class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['nombre', 'corral', 'fecha_ingreso', 'meta_peso', 'observaciones']
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'meta_peso': forms.NumberInput(attrs={'min': '0', 'placeholder': '0.00'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

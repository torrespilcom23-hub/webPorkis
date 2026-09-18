from django import forms
from django.utils import timezone

from registro.models import Lote

from .models import PlanAlimentacion, RegistroAlimentacion, TipoAlimento


def configure_html5_date(
    field,
    *,
    initial=None,
    min_date=None,
    max_date=None,
    css_class='input-compact',
    required=True,
):
    """DateField compatible con input HTML5 type=date (ISO yyyy-mm-dd)."""
    field.input_formats = ['%Y-%m-%d']
    field.required = required
    if initial is not None:
        field.initial = initial
    attrs = {'type': 'date', 'class': css_class}
    if min_date is not None:
        attrs['min'] = min_date.isoformat()
    if max_date is not None:
        attrs['max'] = max_date.isoformat()
    field.widget = forms.DateInput(attrs=attrs, format='%Y-%m-%d')


class TipoAlimentoForm(forms.ModelForm):
    class Meta:
        model = TipoAlimento
        fields = ['nombre', 'proteina_pct', 'proveedor', 'costo_por_kg', 'notas']
        labels = {
            'nombre': 'Nombre',
            'proteina_pct': 'Proteína',
            'proveedor': 'Proveedor',
            'costo_por_kg': 'Costo por kg',
            'notas': 'Indicaciones',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej. Pre-inicio, Crecimiento, Gestación…',
                'class': 'input-compact',
            }),
            'proteina_pct': forms.NumberInput(attrs={
                'min': '0', 'max': '100', 'step': '0.01',
                'placeholder': 'Ej. 18',
                'class': 'input-compact input-compact--short',
            }),
            'proveedor': forms.TextInput(attrs={
                'placeholder': 'Opcional',
                'class': 'input-compact',
            }),
            'costo_por_kg': forms.NumberInput(attrs={
                'min': '0', 'step': '0.01',
                'placeholder': 'S/',
                'class': 'input-compact input-compact--short',
            }),
            'notas': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': (
                    'Notas para el equipo: edad o peso recomendado, '
                    'frecuencia, mezcla con agua, observaciones del nutricionista…'
                ),
                'class': 'input-indicaciones',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('proteina_pct', 'proveedor', 'costo_por_kg', 'notas'):
            self.fields[name].required = False
        self.fields['proteina_pct'].help_text = 'Porcentaje de proteína bruta (opcional).'
        self.fields['notas'].help_text = (
            'Solo referencia interna; no afecta planes ni registros de consumo.'
        )


class PlanAlimentacionForm(forms.ModelForm):
    class Meta:
        model = PlanAlimentacion
        fields = ['lote', 'tipo_alimento', 'cantidad_diaria_kg', 'etapa', 'activo']
        labels = {
            'cantidad_diaria_kg': 'Cantidad diaria',
            'tipo_alimento': 'Alimento',
        }
        widgets = {
            'cantidad_diaria_kg': forms.NumberInput(attrs={
                'min': '0.01', 'step': '0.01',
                'placeholder': 'kg/día',
                'class': 'input-compact input-compact--short',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lote'].queryset = Lote.objects.order_by('nombre')
        self.fields['tipo_alimento'].queryset = TipoAlimento.objects.order_by('nombre')
        self.fields['activo'].help_text = 'Desactive la ración si el lote ya no usa esta cantidad o alimento.'

    def clean(self):
        cleaned = super().clean()
        cantidad = cleaned.get('cantidad_diaria_kg')
        if cantidad is not None and cantidad <= 0:
            self.add_error('cantidad_diaria_kg', 'Debe ser mayor a cero.')
        return cleaned


class RegistroAlimentacionForm(forms.ModelForm):
    class Meta:
        model = RegistroAlimentacion
        fields = [
            'fecha', 'lote', 'tipo_alimento', 'cantidad_servida_kg',
            'cantidad_sobrante_kg', 'observaciones',
        ]
        labels = {
            'cantidad_servida_kg': 'Servido',
            'cantidad_sobrante_kg': 'Sobrante',
            'tipo_alimento': 'Alimento',
        }
        widgets = {
            'cantidad_servida_kg': forms.NumberInput(attrs={
                'min': '0.01', 'step': '0.01',
                'placeholder': 'kg',
                'class': 'input-compact input-compact--short',
            }),
            'cantidad_sobrante_kg': forms.NumberInput(attrs={
                'min': '0', 'step': '0.01',
                'placeholder': 'kg',
                'class': 'input-compact input-compact--short',
            }),
            'observaciones': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Incidencias, cambio de ración, etc. (opcional)',
                'class': 'input-indicaciones',
            }),
        }

    def __init__(self, *args, lote=None, plan_sugerido=None, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = timezone.now().date()
        self.plan_sugerido = plan_sugerido
        self.fields['lote'].queryset = Lote.objects.order_by('nombre')
        self.fields['tipo_alimento'].queryset = TipoAlimento.objects.order_by('nombre')
        if lote:
            self.fields['lote'].initial = lote.pk
        if plan_sugerido:
            self.fields['tipo_alimento'].initial = plan_sugerido.tipo_alimento_id
            self.fields['cantidad_servida_kg'].initial = plan_sugerido.cantidad_diaria_kg
        configure_html5_date(
            self.fields['fecha'],
            initial=hoy,
            max_date=hoy,
            css_class='input-compact refuerzo-fecha-input',
        )
        self.fields['cantidad_sobrante_kg'].required = False
        self.fields['observaciones'].required = False

    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get('fecha')
        hoy = timezone.now().date()
        servida = cleaned.get('cantidad_servida_kg')
        sobrante = cleaned.get('cantidad_sobrante_kg')

        if fecha and fecha > hoy:
            self.add_error('fecha', 'La fecha no puede ser futura.')
        if servida is not None and servida <= 0:
            self.add_error('cantidad_servida_kg', 'Debe ser mayor a cero.')
        if sobrante is not None and servida is not None:
            if sobrante < 0:
                self.add_error('cantidad_sobrante_kg', 'No puede ser negativo.')
            elif sobrante > servida:
                self.add_error('cantidad_sobrante_kg', 'No puede superar lo servido.')
        return cleaned

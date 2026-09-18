from datetime import timedelta

from django import forms
from django.utils import timezone

from registro.models import Cerdo

from .models import AplicacionVacuna, Vacuna


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


class VacunaForm(forms.ModelForm):
    class Meta:
        model = Vacuna
        fields = ['nombre', 'intervalo_dias', 'descripcion']
        labels = {
            'nombre': 'Nombre',
            'intervalo_dias': 'Intervalo de refuerzo',
            'descripcion': 'Indicaciones',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej. Circovirus, Mycoplasma, Parvovirus…',
                'class': 'input-compact',
            }),
            'intervalo_dias': forms.NumberInput(attrs={
                'min': '1',
                'placeholder': 'Ej. 21',
                'class': 'input-compact input-compact--short',
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': (
                    'Notas de uso en la granja: dosis habitual, vía de aplicación, '
                    'edad o peso recomendado, observaciones del veterinario…'
                ),
                'class': 'input-indicaciones',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['intervalo_dias'].required = False
        self.fields['descripcion'].required = False
        self.fields['intervalo_dias'].help_text = (
            'Días hasta el refuerzo. Si lo deja vacío, la próxima dosis deberá indicarse manualmente.'
        )
        self.fields['descripcion'].help_text = (
            'Solo referencia para el equipo; no afecta el cálculo automático de refuerzos.'
        )


class AplicacionVacunaForm(forms.ModelForm):
    class Meta:
        model = AplicacionVacuna
        fields = [
            'cerdo', 'vacuna', 'fecha_aplicacion', 'dosis',
            'lote_medicamento', 'proxima_dosis', 'observaciones',
        ]
        widgets = {
            'fecha_aplicacion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'proxima_dosis': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'dosis': forms.TextInput(attrs={'placeholder': 'Ej. 2 ml, 1 dosis'}),
            'lote_medicamento': forms.TextInput(attrs={'placeholder': 'Lote del medicamento — opcional'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, cerdo=None, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = timezone.now().date()
        self.fields['cerdo'].queryset = Cerdo.objects.filter(
            estado=Cerdo.Estado.ACTIVO,
        ).order_by('arete')
        if cerdo:
            self.fields['cerdo'].initial = cerdo.pk
        configure_html5_date(
            self.fields['fecha_aplicacion'],
            initial=hoy,
            max_date=hoy,
        )
        configure_html5_date(
            self.fields['proxima_dosis'],
            required=False,
        )
        self.fields['proxima_dosis'].help_text = (
            'Opcional. Si se deja vacío y la vacuna tiene intervalo, se calcula automáticamente.'
        )

    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get('fecha_aplicacion')
        cerdo = cleaned.get('cerdo')
        hoy = timezone.now().date()
        if fecha and fecha > hoy:
            self.add_error('fecha_aplicacion', 'La fecha no puede ser futura.')
        if cerdo and cerdo.estado != Cerdo.Estado.ACTIVO:
            self.add_error('cerdo', 'Solo se pueden vacunar cerdos en granja.')
        return cleaned

    def save(self, commit=True):
        inst = super().save(commit=False)
        if not inst.proxima_dosis and inst.vacuna_id and inst.fecha_aplicacion:
            if inst.vacuna.intervalo_dias:
                inst.proxima_dosis = inst.fecha_aplicacion + timedelta(
                    days=inst.vacuna.intervalo_dias,
                )
        if commit:
            inst.save()
        return inst


class RefuerzoVacunaForm(forms.ModelForm):
    """Registro de refuerzo: cerdo y vacuna vienen de la aplicación anterior."""

    class Meta:
        model = AplicacionVacuna
        fields = ['fecha_aplicacion', 'dosis', 'lote_medicamento', 'observaciones']
        labels = {
            'fecha_aplicacion': 'Fecha de este refuerzo',
            'dosis': 'Dosis aplicada',
            'lote_medicamento': 'Lote del medicamento',
            'observaciones': 'Observaciones',
        }
        widgets = {
            'fecha_aplicacion': forms.DateInput(format='%Y-%m-%d'),
            'dosis': forms.TextInput(attrs={'placeholder': 'Ej. 2 ml', 'class': 'input-compact'}),
            'lote_medicamento': forms.TextInput(attrs={'placeholder': 'Opcional', 'class': 'input-compact'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Opcional', 'class': 'input-compact'}),
        }

    def __init__(self, *args, anterior=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.anterior = anterior
        hoy = timezone.now().date()
        if anterior:
            min_fecha = anterior.fecha_aplicacion + timedelta(days=1)
        else:
            min_fecha = hoy
        self.min_fecha_refuerzo = min_fecha
        self.max_fecha_refuerzo = hoy
        self.puede_registrar = min_fecha <= hoy
        if self.puede_registrar:
            configure_html5_date(
                self.fields['fecha_aplicacion'],
                initial=hoy,
                min_date=min_fecha,
                max_date=hoy,
                css_class='input-compact refuerzo-fecha-input',
            )
        self.fields['dosis'].initial = anterior.dosis if anterior else ''
        self.fields['lote_medicamento'].required = False
        self.fields['observaciones'].required = False

    def clean(self):
        cleaned = super().clean()
        if not self.puede_registrar:
            raise forms.ValidationError(
                f'El refuerzo puede registrarse a partir del '
                f'{self.min_fecha_refuerzo:%d/%m/%Y} (un día después de la última dosis).',
            )
        fecha = cleaned.get('fecha_aplicacion')
        hoy = timezone.now().date()
        if fecha and fecha > hoy:
            self.add_error('fecha_aplicacion', 'La fecha no puede ser futura.')
        if fecha and fecha < self.min_fecha_refuerzo:
            self.add_error(
                'fecha_aplicacion',
                f'No puede ser anterior al {self.min_fecha_refuerzo:%d/%m/%Y}.',
            )
        if self.anterior and fecha and fecha <= self.anterior.fecha_aplicacion:
            self.add_error(
                'fecha_aplicacion',
                f'Debe ser posterior a la última aplicación ({self.anterior.fecha_aplicacion:%d/%m/%Y}).',
            )
        if self.anterior and self.anterior.cerdo.estado != Cerdo.Estado.ACTIVO:
            raise forms.ValidationError('El cerdo ya no está en granja; no se puede registrar refuerzo.')
        return cleaned

    def save(self, commit=True):
        inst = super().save(commit=False)
        inst.cerdo = self.anterior.cerdo
        inst.vacuna = self.anterior.vacuna
        if not inst.proxima_dosis and inst.vacuna.intervalo_dias and inst.fecha_aplicacion:
            inst.proxima_dosis = inst.fecha_aplicacion + timedelta(
                days=inst.vacuna.intervalo_dias,
            )
        if commit:
            inst.save()
        return inst


class AplicacionVacunaModalForm(forms.ModelForm):
    """Formulario reducido para registro rápido desde ficha de cerdo."""

    class Meta:
        model = AplicacionVacuna
        fields = ['vacuna', 'fecha_aplicacion', 'dosis', 'lote_medicamento', 'observaciones']
        widgets = {
            'fecha_aplicacion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'dosis': forms.TextInput(attrs={'placeholder': 'Ej. 2 ml'}),
            'lote_medicamento': forms.TextInput(attrs={'placeholder': 'Opcional'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Opcional', 'maxlength': '200'}),
        }

    def __init__(self, *args, cerdo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cerdo = cerdo
        hoy = timezone.now().date()
        configure_html5_date(
            self.fields['fecha_aplicacion'],
            initial=hoy,
            max_date=hoy,
        )

    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get('fecha_aplicacion')
        hoy = timezone.now().date()
        if fecha and fecha > hoy:
            self.add_error('fecha_aplicacion', 'La fecha no puede ser futura.')
        if self.cerdo and self.cerdo.estado != Cerdo.Estado.ACTIVO:
            raise forms.ValidationError('Solo se pueden vacunar cerdos en granja.')
        return cleaned

    def save(self, commit=True):
        inst = super().save(commit=False)
        inst.cerdo = self.cerdo
        if not inst.proxima_dosis and inst.vacuna_id and inst.fecha_aplicacion:
            if inst.vacuna.intervalo_dias:
                inst.proxima_dosis = inst.fecha_aplicacion + timedelta(
                    days=inst.vacuna.intervalo_dias,
                )
        if commit:
            inst.save()
        return inst

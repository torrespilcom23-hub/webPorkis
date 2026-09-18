from django import forms
from django.db.models import Count
from django.utils import timezone

from registro.models import CategoriaCerdo, Cerdo, Corral, Lote

from .models import DiagnosticoPrenez, Inseminacion, Padrillo, Parto


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


class PadrilloForm(forms.ModelForm):
    class Meta:
        model = Padrillo
        fields = ['codigo', 'raza', 'origen', 'stock_pajuelas']
        labels = {
            'codigo': 'Código',
            'stock_pajuelas': 'Stock de pajuelas',
        }
        help_texts = {
            'codigo': 'Identificador del padrillo o lote de semen (ej. DU-001).',
            'stock_pajuelas': 'Solo aplica a padrillos externos o semen congelado.',
        }


class InseminacionForm(forms.ModelForm):
    class Meta:
        model = Inseminacion
        fields = ['cerda', 'fecha', 'tipo', 'padrillo', 'observaciones']
        labels = {
            'cerda': 'Cerda',
            'padrillo': 'Padrillo / semen',
        }
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'input-compact'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hembras = Cerdo.objects.filter(
            sexo=Cerdo.Sexo.HEMBRA,
            estado=Cerdo.Estado.ACTIVO,
        ).order_by('arete')
        if self.instance.pk and self.instance.cerda_id:
            hembras = hembras | Cerdo.objects.filter(pk=self.instance.cerda_id)
        self.fields['cerda'].queryset = hembras.distinct().order_by('arete')
        self.fields['padrillo'].queryset = Padrillo.objects.order_by('codigo')
        self.fields['padrillo'].required = False
        configure_html5_date(
            self.fields['fecha'],
            initial=timezone.now().date() if not self.instance.pk else None,
            max_date=timezone.now().date(),
        )

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')
        padrillo = cleaned.get('padrillo')
        if tipo == Inseminacion.Tipo.ARTIFICIAL and not padrillo:
            self.add_error(
                'padrillo',
                'Indique el padrillo o lote de semen para inseminación artificial.',
            )
        return cleaned


class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = DiagnosticoPrenez
        fields = ['fecha', 'resultado', 'metodo']
        labels = {
            'metodo': 'Método (opcional)',
        }
        help_texts = {
            'fecha': 'Suele realizarse entre 21 y 30 días después de la inseminación.',
        }

    def __init__(self, *args, inseminacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.inseminacion = inseminacion
        min_fecha = inseminacion.fecha if inseminacion else None
        configure_html5_date(
            self.fields['fecha'],
            initial=timezone.now().date() if not self.instance.pk else None,
            min_date=min_fecha,
            max_date=timezone.now().date(),
        )

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if self.inseminacion and fecha < self.inseminacion.fecha:
            raise forms.ValidationError(
                'La fecha del diagnóstico no puede ser anterior a la inseminación.',
            )
        return fecha


class PartoForm(forms.ModelForm):
    class Meta:
        model = Parto
        fields = [
            'inseminacion', 'fecha', 'lechones_vivos',
            'lechones_muertos', 'lechones_destetados', 'observaciones',
        ]
        labels = {
            'inseminacion': 'Inseminación origen',
            'lechones_vivos': 'Lechones nacidos vivos',
            'lechones_muertos': 'Nacidos muertos',
            'lechones_destetados': 'Destetados (opcional)',
        }
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'input-compact'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        positivas = Inseminacion.objects.filter(
            diagnostico__resultado=DiagnosticoPrenez.Resultado.POSITIVO,
        ).select_related('cerda', 'diagnostico').order_by('-fecha')
        if self.instance.pk:
            qs = positivas | Inseminacion.objects.filter(pk=self.instance.inseminacion_id)
            self.fields['inseminacion'].queryset = qs.distinct().order_by('-fecha')
        else:
            self.fields['inseminacion'].queryset = positivas.annotate(
                num_partos=Count('partos'),
            ).filter(num_partos=0)
        configure_html5_date(
            self.fields['fecha'],
            initial=timezone.now().date() if not self.instance.pk else None,
            max_date=timezone.now().date(),
        )
        self.fields['inseminacion'].label_from_instance = (
            lambda obj: f'{obj.cerda.arete} — insem. {obj.fecha:%d/%m/%Y}'
        )

    def clean(self):
        cleaned = super().clean()
        inseminacion = cleaned.get('inseminacion')
        fecha = cleaned.get('fecha')
        vivos = cleaned.get('lechones_vivos')
        muertos = cleaned.get('lechones_muertos') or 0
        destetados = cleaned.get('lechones_destetados')

        if inseminacion and fecha:
            if fecha < inseminacion.fecha:
                self.add_error(
                    'fecha',
                    'La fecha del parto no puede ser anterior a la inseminación.',
                )
            try:
                diag = inseminacion.diagnostico
            except DiagnosticoPrenez.DoesNotExist:
                self.add_error(
                    'inseminacion',
                    'La inseminación seleccionada no tiene diagnóstico positivo.',
                )
            else:
                if diag.resultado != DiagnosticoPrenez.Resultado.POSITIVO:
                    self.add_error(
                        'inseminacion',
                        'Solo puede registrar parto de inseminaciones con diagnóstico positivo.',
                    )
                elif fecha < diag.fecha:
                    self.add_error(
                        'fecha',
                        'La fecha del parto no puede ser anterior al diagnóstico de preñez.',
                    )

        if vivos is not None and destetados is not None and destetados > vivos:
            self.add_error(
                'lechones_destetados',
                'No puede destetar más lechones que los nacidos vivos.',
            )
        if vivos is not None and muertos < 0:
            self.add_error('lechones_muertos', 'Valor inválido.')
        if self.instance.pk and vivos is not None:
            registrados = self.instance.lechones_en_registro
            if vivos < registrados:
                self.add_error(
                    'lechones_vivos',
                    f'Ya hay {registrados} lechón(es) en Registro; '
                    'no puede indicar menos nacidos vivos.',
                )
        return cleaned


class LechonesComunForm(forms.Form):
    """Campos compartidos al dar de alta lechones desde un parto."""

    raza = forms.ChoiceField(
        choices=Cerdo.Raza.choices,
        label='Raza',
        widget=forms.Select(attrs={'class': 'input-compact'}),
    )
    raza_otro = forms.CharField(
        required=False,
        label='¿Cuál raza?',
        widget=forms.TextInput(attrs={
            'class': 'input-compact',
            'placeholder': 'Ej.: Large White',
        }),
    )
    categoria = forms.ModelChoiceField(
        queryset=CategoriaCerdo.objects.all(),
        required=False,
        label='Categoría',
        empty_label='— Sin categoría —',
        widget=forms.Select(attrs={'class': 'input-compact'}),
    )
    corral = forms.ModelChoiceField(
        queryset=Corral.objects.all(),
        required=False,
        label='Corral',
        empty_label='— Sin corral —',
        widget=forms.Select(attrs={'class': 'input-compact'}),
    )
    lote = forms.ModelChoiceField(
        queryset=Lote.objects.all(),
        required=False,
        label='Lote',
        empty_label='— Usar lote de la madre —',
        widget=forms.Select(attrs={'class': 'input-compact'}),
    )
    crear_lote_camada = forms.BooleanField(
        required=False,
        initial=True,
        label='Crear lote «Camada …» para estos lechones',
    )

    def __init__(self, *args, parto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parto = parto
        if parto:
            madre = parto.madre
            self.fields['raza'].initial = madre.raza
            self.fields['raza_otro'].initial = madre.raza_otro
            self.fields['corral'].initial = madre.corral_id
            self.fields['lote'].initial = madre.lote_id
            lechon = CategoriaCerdo.objects.filter(nombre__iexact='Lechón').first()
            if lechon:
                self.fields['categoria'].initial = lechon.pk

    def clean(self):
        cleaned = super().clean()
        raza = cleaned.get('raza')
        raza_otro = (cleaned.get('raza_otro') or '').strip()
        if raza == Cerdo.Raza.OTRO:
            if not raza_otro:
                self.add_error('raza_otro', 'Especifique la raza.')
            else:
                cleaned['raza_otro'] = raza_otro
        else:
            cleaned['raza_otro'] = ''
        if cleaned.get('crear_lote_camada') and cleaned.get('lote'):
            self.add_error(
                'lote',
                'Desmarque «Crear lote camada» o deje el lote vacío para generar uno nuevo.',
            )
        return cleaned


class LechonesRapidoForm(LechonesComunForm):
    cantidad = forms.IntegerField(
        min_value=1,
        label='Cantidad a registrar',
        widget=forms.NumberInput(attrs={'class': 'input-compact'}),
    )
    machos = forms.IntegerField(
        min_value=0,
        label='Machos',
        widget=forms.NumberInput(attrs={'class': 'input-compact'}),
    )
    hembras = forms.IntegerField(
        min_value=0,
        label='Hembras',
        widget=forms.NumberInput(attrs={'class': 'input-compact'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.parto:
            pend = self.parto.lechones_pendientes_alta
            self.fields['cantidad'].max_value = pend
            self.fields['cantidad'].initial = pend
            self.fields['cantidad'].widget.attrs['max'] = pend
            mitad = pend // 2
            self.fields['machos'].initial = mitad
            self.fields['hembras'].initial = pend - mitad

    def clean(self):
        cleaned = super().clean()
        cantidad = cleaned.get('cantidad')
        machos = cleaned.get('machos')
        hembras = cleaned.get('hembras')
        if self.parto and cantidad is not None:
            if cantidad > self.parto.lechones_pendientes_alta:
                self.add_error(
                    'cantidad',
                    f'Máximo {self.parto.lechones_pendientes_alta} '
                    f'(ya hay {self.parto.lechones_en_registro} en Registro).',
                )
        if machos is not None and hembras is not None and cantidad is not None:
            if machos + hembras != cantidad:
                raise forms.ValidationError(
                    'Machos + hembras debe ser igual a la cantidad total.',
                )
        return cleaned


class LechonItemForm(forms.Form):
    sexo = forms.ChoiceField(
        choices=Cerdo.Sexo.choices,
        label='Sexo',
        widget=forms.Select(attrs={'class': 'input-compact'}),
    )
    peso_actual = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=8,
        decimal_places=2,
        label='Peso (kg)',
        widget=forms.NumberInput(
            attrs={'class': 'input-compact', 'step': '0.01', 'inputmode': 'decimal'},
        ),
    )
    observaciones = forms.CharField(
        required=False,
        label='Observaciones',
        widget=forms.TextInput(
            attrs={'class': 'input-compact', 'placeholder': 'Opcional'},
        ),
    )


LechonItemFormSet = forms.formset_factory(LechonItemForm, extra=0)

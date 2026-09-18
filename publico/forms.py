from django import forms

from .models import MensajeContacto


class ContactoForm(forms.ModelForm):
    ASUNTO_CHOICES = [
        ('', 'Seleccione un asunto'),
        ('venta', 'Venta de lechones'),
        ('engorde', 'Engorde en granja'),
        ('sanidad', 'Sanidad y vacunas'),
        ('reproduccion', 'Reproducción e inseminación'),
        ('visita', 'Visita a la granja'),
        ('otro', 'Otro'),
    ]

    asunto = forms.ChoiceField(choices=ASUNTO_CHOICES)

    class Meta:
        model = MensajeContacto
        fields = ['nombre', 'email', 'telefono', 'asunto', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Su nombre completo'}),
            'email': forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'placeholder': '300 123 4567'}),
            'mensaje': forms.Textarea(attrs={'placeholder': 'Escriba su mensaje...', 'rows': 5}),
        }

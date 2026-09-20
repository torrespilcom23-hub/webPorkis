from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User


class OperadorCreateForm(UserCreationForm):
    email = forms.EmailField(required=False, label='Correo')
    rol = forms.ChoiceField(
        label='Rol en el panel',
        choices=[
            ('operador', 'Operador de granja'),
            ('admin', 'Administrador'),
        ],
        initial='operador',
        widget=forms.RadioSelect,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        compact = {'class': 'input-compact'}
        self.fields['username'].widget.attrs.update(compact)
        self.fields['username'].widget.attrs.setdefault('autocomplete', 'username')
        self.fields['username'].help_text = 'Máx. 150 caracteres · letras, números y @ . + - _'
        self.fields['email'].widget.attrs.update(compact)
        self.fields['email'].widget.attrs.setdefault('autocomplete', 'email')
        self.fields['email'].widget.attrs.setdefault('placeholder', 'opcional@correo.com')
        self.fields['password1'].widget.attrs.update(compact)
        self.fields['password1'].help_text = 'Mínimo 8 caracteres.'
        self.fields['password2'].widget.attrs.update(compact)
        self.fields['password2'].help_text = ''
        self.fields['password2'].label = 'Confirmar contraseña'

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.is_staff = False
            user.is_superuser = False
            user.save(update_fields=['is_staff', 'is_superuser'])
            self._asignar_rol(user)
        return user

    def _asignar_rol(self, user):
        from django.contrib.auth.models import Group

        rol = self.cleaned_data['rol']
        user.groups.clear()
        grupo, _ = Group.objects.get_or_create(name=rol)
        user.groups.add(grupo)


class ResetPasswordAdminForm(SetPasswordForm):
    """Contraseña nueva definida por el administrador."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        compact = {'class': 'input-compact'}
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password2'].label = 'Confirmar contraseña'
        self.fields['new_password1'].widget.attrs.update(compact)
        self.fields['new_password2'].widget.attrs.update(compact)
        self.fields['new_password1'].help_text = 'Mínimo 8 caracteres.'
        self.fields['new_password2'].help_text = ''

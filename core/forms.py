from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm


class LoginForm(AuthenticationForm):
    """Formulario de login base (estilizado en el template)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            campo.widget.attrs.update({'class': 'form-control form-control-lg', 'autocomplete': 'off'})
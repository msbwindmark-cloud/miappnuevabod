from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import inlineformset_factory

from .models import CierreCaja, PagoPersonal, Empleado


class CierreCajaForm(forms.ModelForm):
    class Meta:
        model = CierreCaja
        fields = ['fecha', 'servicio', 'fondo_caja', 'efectivo_total_caja', 'total_tpv_bizum', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'servicio': forms.Select(attrs={'class': 'form-select'}),
            'fondo_caja': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'efectivo_total_caja': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_tpv_bizum': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            hoy = timezone.localdate()
            semana = hoy.weekday()
            if semana in (4, 5):  # viernes o sabado
                servicio = 'viernes' if semana == 4 else 'sabado'
            else:
                servicio = 'viernes'
            self.fields['fecha'].initial = hoy
            self.fields['servicio'].initial = servicio


class PagoPersonalForm(forms.ModelForm):
    class Meta:
        model = PagoPersonal
        fields = ['empleado', 'importe']
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'importe': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


PagoPersonalFormSet = inlineformset_factory(
    CierreCaja, PagoPersonal,
    form=PagoPersonalForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)
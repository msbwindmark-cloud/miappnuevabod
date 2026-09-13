from django import forms

from .models import Categoria, Producto, Proveedor


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'proveedor', 'unidad', 'stock_minimo', 'stock_actual',
                  'precio_medio_copa', 'copas_por_botella', 'es_alcohol', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'precio_medio_copa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'copas_por_botella': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'es_alcohol': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'orden', 'icono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'icono': forms.TextInput(attrs={'class': 'form-control'}),
        }
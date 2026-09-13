"""
Modelos del Módulo 3: Generador de pedidos a proveedores.
Unidades a Pedir = MAX(0, Stock Mínimo Deseado − Stock Actual Contado)
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse


class Pedido(models.Model):
    """Pedido generado para un proveedor a partir de un conteo de stock."""

    ESTADOS = [
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado al proveedor'),
        ('recibido', 'Recibido'),
        ('cancelado', 'Cancelado'),
    ]

    fecha = models.DateField(auto_now_add=True)
    proveedor = models.ForeignKey(
        'inventario.Proveedor', on_delete=models.PROTECT, related_name='pedidos'
    )
    conteo = models.ForeignKey(
        'inventario.ConteoStock', on_delete=models.PROTECT, related_name='pedidos',
        null=True, blank=True, help_text='Conteo del que se deriva este pedido.'
    )
    estado = models.CharField(max_length=12, choices=ESTADOS, default='borrador')
    notas = models.TextField(blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    @property
    def total_unidades(self):
        return sum((l.unidades_a_pedir for l in self.lineas.all()), 0)

    def __str__(self):
        return f'Pedido {self.pk} · {self.proveedor.nombre} · {self.fecha:%d/%m/%Y}'

    def get_absolute_url(self):
        return reverse('pedidos:pedido_detail', args=[self.pk])


class PedidoLinea(models.Model):
    """Línea de pedido: producto y unidades a pedir."""

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='lineas')
    producto = models.ForeignKey('inventario.Producto', on_delete=models.PROTECT, related_name='lineas_pedido')
    unidades_a_pedir = models.PositiveIntegerField()

    class Meta:
        ordering = ['producto__categoria__orden', 'producto__nombre']
        unique_together = [('pedido', 'producto')]
        verbose_name = 'Línea de pedido'
        verbose_name_plural = 'Líneas de pedido'

    def __str__(self):
        return f'{self.producto.nombre}: {self.unidades_a_pedir}'
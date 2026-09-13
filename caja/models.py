"""
Modelos del Módulo 1: Cierre de Caja diario y pagos al personal.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse


class Empleado(models.Model):
    """Personal del bar al que se realizan pagos en efectivo."""

    nombre = models.CharField(max_length=120, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        return self.nombre


class CierreCaja(models.Model):
    """Cierre de la noche: viernes o sábado. Calcula facturación y efectivo restante."""

    SERVICIOS = [
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
    ]

    fecha = models.DateField('Fecha del servicio')
    servicio = models.CharField('Servicio', max_length=10, choices=SERVICIOS)
    fondo_caja = models.DecimalField('Fondo de caja inicial (€)', max_digits=10, decimal_places=2, default=Decimal('200.00'))
    efectivo_total_caja = models.DecimalField('Efectivo total en caja (€)', max_digits=12, decimal_places=2)
    total_tpv_bizum = models.DecimalField('Total TPV / Bizum (€)', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = 'Cierre de caja'
        verbose_name_plural = 'Cierres de caja'

    # -------------------- Cálculos automáticos del documento --------------------
    @property
    def facturacion_efectivo_neto(self):
        """Facturación Efectivo Neto = Efectivo Total en Caja − Fondo de Caja Inicial."""
        return self.efectivo_total_caja - self.fondo_caja

    @property
    def facturacion_total(self):
        """Facturación Total Noche = Efectivo Neto + TPV/Bizum."""
        return self.facturacion_efectivo_neto + self.total_tpv_bizum

    @property
    def total_pagos_personal(self):
        return sum((p.importe for p in self.pagos.all()), Decimal('0.00'))

    @property
    def efectivo_final_requerido(self):
        """Efectivo Final Requerido = Efectivo Total − ∑(Pagos a Personal)."""
        return self.efectivo_total_caja - self.total_pagos_personal

    @property
    def resumen_whatsapp(self):
        """Resumen formateado para el grupo familiar de WhatsApp."""
        return (
            f'Cierre {self.fecha:%d/%m/%Y} | Facturación Total: {self.facturacion_total:.0f}€ '
            f'(TPV: {self.total_tpv_bizum:.0f}€ | Efectivo Neto: {self.facturacion_efectivo_neto:.0f}€) '
            f'| Pagos Personal: {self.total_pagos_personal:.0f}€ | '
            f'Caja Restante: {self.efectivo_final_requerido:.0f}€'
        )

    def __str__(self):
        return f'Cierre {self.fecha:%d/%m/%Y} ({self.get_servicio_display()})'

    def get_absolute_url(self):
        return reverse('caja:cierre_detail', args=[self.pk])


class PagoPersonal(models.Model):
    """Pago realizado a un empleado en efectivo esa noche."""

    cierre = models.ForeignKey(CierreCaja, on_delete=models.CASCADE, related_name='pagos')
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='pagos')
    importe = models.DecimalField('Importe pagado (€)', max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']
        verbose_name = 'Pago al personal'
        verbose_name_plural = 'Pagos al personal'

    def __str__(self):
        return f'{self.empleado.nombre}: {self.importe}€'
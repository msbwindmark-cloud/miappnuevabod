"""
Modelos de inventario: Proveedor, Categoria, Producto y registro de conteo de stock
(recuento físico del almacén, domingo por la mañana).
"""

from django.db import models
from django.urls import reverse
from django.conf import settings


class Proveedor(models.Model):
    """Proveedor al que se vinculan los productos (Ej: Distribución Bebidas, Tabacos, Hielo)."""

    nombre = models.CharField(max_length=120, unique=True)
    contacto = models.CharField('Contacto (tel/email/comercial)', max_length=200, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('inventario:proveedor_list')


class Categoria(models.Model):
    """Categorías de producto usadas como pestañas en el inventario táctil."""

    nombre = models.CharField(max_length=80, unique=True)
    orden = models.PositiveSmallIntegerField(default=0)
    icono = models.CharField(max_length=60, blank=True, help_text='Icono CSS/FontAwesome')

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Artículo del catálogo. Unidades enteras: botellas, paquetes, cajas, latas..."""

    UNIDADES = [
        ('botella', 'Botella'),
        ('paquete', 'Paquete'),
        ('caja', 'Caja'),
        ('lata', 'Lata'),
        ('botellin', 'Botellín'),
        ('unidad', 'Unidad'),
        ('cazoleta', 'Cazoleta'),
    ]

    nombre = models.CharField(max_length=120, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='productos')
    unidad = models.CharField(max_length=20, choices=UNIDADES, default='botella')
    stock_minimo = models.PositiveIntegerField('Stock mínimo deseado', default=0)
    stock_actual = models.PositiveIntegerField('Stock actual', default=0)
    precio_medio_copa = models.DecimalField(
        'Precio medio por copa (€)', max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Solo para alcohol: usado en la auditoría de rendimiento.'
    )
    copas_por_botella = models.PositiveIntegerField('Copas por botella', default=8)
    es_alcohol = models.BooleanField('Es alcohol', default=False)
    activo = models.BooleanField(default=True)
    fecha_alta = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['categoria__orden', 'nombre']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return self.nombre

    @property
    def a_pedir(self):
        return max(0, self.stock_minimo - self.stock_actual)

    def get_absolute_url(self):
        return reverse('inventario:producto_list')


class ConteoStock(models.Model):
    """Sesión de recuento físico (una por domingo por la mañana)."""

    fecha = models.DateField(unique=True)
    nota = models.CharField(max_length=200, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, editable=False
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Conteo de stock'
        verbose_name_plural = 'Conteos de stock'

    def __str__(self):
        return f'Conteo {self.fecha:%d/%m/%Y}'

    def get_absolute_url(self):
        return reverse('inventario:conteo_detail', args=[self.pk])


class ConteoStockLinea(models.Model):
    """Línea de recuento: cantidad contada de un producto."""

    conteo = models.ForeignKey(ConteoStock, on_delete=models.CASCADE, related_name='lineas')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='conteos')
    cantidad_contada = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['producto__categoria__orden', 'producto__nombre']
        unique_together = [('conteo', 'producto')]
        verbose_name = 'Línea de conteo'
        verbose_name_plural = 'Líneas de conteo'

    def __str__(self):
        return f'{self.producto.nombre}: {self.cantidad_contada}'
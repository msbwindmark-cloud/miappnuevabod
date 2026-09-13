# Chill Out La Bodeguita - Documentación de la Aplicación

## Descripción general

Aplicación web de gestión interna para el bar **Chill Out La Bodeguita** (Córdoba).
Desarrollada con Django 5.2, Python 3.11 y Bootstrap 5 (Bootswatch Flatly).

---

## Usuarios y acceso

| Usuario  | Contraseña  | Rol          |
|----------|-------------|--------------|
| admin    | Moha.93345900  | Superusuario |
| jefe     | Moha.93345900   | Superusuario |

Superusuarios ven: **Trazabilidad** y **Panel Admin** en la barra de navegación.

Si creas un usuario desde el admin Django (`/admin/`), solo tendrá acceso a la
aplicación si `is_staff=True`. Solo los `is_superuser=True` ven el menú admin.

### Bloqueo por intentos fallidos

- Máximo 5 intentos de login consecutivos
- Tras superar el límite, el usuario queda bloqueado 30 minutos
- Historial visible en `/actividad/`
- Opción "Cerrar otras sesiones" desde el menú de usuario

### Recuperación de contraseña

URL: `/reset/` — envía un email con enlace de restablecimiento (requiere SMTP configurado).

---

## Estructura del proyecto

```
mitpvnuevo/
  config/           # Proyecto Django (settings, urls, wsgi)
  core/             # Login, trazabilidad CRUD, seguridad, modelos de auditoría
  core/sites.py     # Sitio admin personalizado (solo superusers) + registro de modelos
  caja/             # Módulo 1: cierres de caja y pagos al personal
  inventario/       # Módulo 2: productos, proveedores, conteo táctil de stock
  pedidos/          # Módulo 3: generador de pedidos a proveedores
  auditoria/        # Módulo 4: auditoría de rendimiento teórico vs real
  templates/        # Plantillas HTML (Bootswatch 5 + SweetAlert2)
  seed.py           # Poblar catálogo + datos demo
  smoke_test.py     # Test de humo (18 chequeos)
  verif_pdf.py      # Verificación contra el documento funcional (20 puntos)
```

---

## Módulo 1 — Cierre de Caja (`/caja/`)

### Qué hace

Registra el cierre diario de la noche (viernes o sábado) y calcula automáticamente
los importes según el **Documento Funcional EFD-2026-v1.0**.

### Fórmulas

```
Facturación Efectivo Neto  = Efectivo Total en Caja − Fondo de Caja Inicial
Facturación Total Noche    = Efectivo Neto + TPV / Bizum
Caja Restante              = Efectivo Total − Suma(Pagos a Personal)
```

### Cómo probarlo

1. Entrar con `admin / admin12345`
2. Ir a **Caja > Nuevo cierre** (`/caja/nuevo/`)
3. Rellenar: fecha, servicio (viernes/sábado), fondo de caja, efectivo total, TPV
4. Añadir pagos al personal (botón "Añadir pago")
5. Guardar → se muestra el detalle con el resumen WhatsApp formateado

### URLs

| URL                          | Acción                        |
|------------------------------|-------------------------------|
| `/caja/`                     | Listado histórico de cierres  |
| `/caja/nuevo/`               | Crear nuevo cierre            |
| `/caja/<id>/`                | Detalle de un cierre          |
| `/caja/<id>/editar/`         | Editar cierre                 |
| `/caja/<id>/eliminar/`       | Eliminar cierre               |
| `/caja/<id>/whatsapp/`       | Resumen en texto para WA      |
| `/caja/empleados/`           | Gestión de empleados          |
| `/caja/excel/`               | Exportar cierres a Excel      |

---

## Módulo 2 — Inventario Táctil (`/inventario/`)

### Qué hace

Conteo físico de stock cada domingo por la mañana. Interfaz táctil con botones +/- de
al menos 48px de alto (requisito mobile-first del PDF). Pestañas por categoría.

### Fórmula

```
Unidades a Pedir = MAX(0, Stock Mínimo Deseado − Stock Contado)
```

### Catálogo precargado

- **40 productos** (alcohol: rones, whiskys, ginebras, licores; refrescos; cachimbas; mojitos)
- **3 proveedores**: Distribución de Bebidas, Tabacos y Cachimbas, Hielo y Varios
- **7 categorías** como pestañas en el inventario

### Cómo probarlo

1. Ir a **Inventario > Contar stock (táctil)** (`/inventario/conteo/nuevo/`)
2. Seleccionar pestaña de categoría
3. Usar botones +/- para ajustar la cantidad contada de cada producto
4. Guardar → se genera el conteo
5. Ir a **Pedidos > Generar** desde el conteo para ver las unidades a pedir

### URLs

| URL                            | Acción                            |
|--------------------------------|-----------------------------------|
| `/inventario/`                 | Listado de productos              |
| `/inventario/nuevo/`           | Crear producto                    |
| `/inventario/conteo/nuevo/`    | Conteo táctil (interfaz +/-)      |
| `/inventario/conteos/`         | Listado de conteos realizados     |
| `/inventario/proveedores/`     | Gestión de proveedores            |
| `/inventario/stock-excel/`     | Exportar stock a Excel            |

---

## Módulo 3 — Pedidos a Proveedores (`/pedidos/`)

### Qué hace

A partir de un conteo de stock, genera automáticamente pedidos agrupados por proveedor.
Calcula las unidades a pedir usando la fórmula del Módulo 2.

### Funcionalidades

- Generación automática de pedidos por proveedor
- Estados: Borrador → Enviado al proveedor → Recibido / Cancelado
- Al marcar como "Enviado": envía email de notificación al responsable
- Exportación a Excel
- Generación de PDF con reportlab
- Texto plano listo para copiar y pegar en WhatsApp

### Cómo probarlo

1. Crear un conteo en **Inventario > Contar stock** o usar uno existente
2. Ir a **Inventario > Conteos realizados** → entrar en un conteo
3. Botón **Generar pedidos** (URL: `/pedidos/generar/<id_conteo>/`)
4. Los pedidos aparecen en **Pedidos > Pedidos generados**
5. Abrir un pedido → ver detalle, cambiar estado, descargar PDF, copiar texto WhatsApp

### URLs

| URL                             | Acción                          |
|---------------------------------|---------------------------------|
| `/pedidos/`                     | Listado de pedidos              |
| `/pedidos/generar/<id>/`        | Generar desde un conteo         |
| `/pedidos/<id>/`                | Detalle de un pedido            |
| `/pedidos/<id>/estado/`         | Cambiar estado (POST)           |
| `/pedidos/<id>/texto/`          | Texto plano (WhatsApp)          |
| `/pedidos/<id>/pdf/`            | Descargar PDF                   |
| `/pedidos/excel/`               | Exportar pedidos a Excel        |

---

## Módulo 4 — Auditoría de Rendimiento (`/auditoria/`)

### Qué hace

Cruza conteos consecutivos de stock para calcular el consumo teórico de alcohol
y refrescos, y lo compara con la facturación real del cierre de caja.

### Fórmulas

```
Copas Teóricas        = Δ Botellas consumidas × Copas por Botella (8)
Facturación Teórica   = Copas × Precio Medio por Copa (€)
Desviación            = Facturación Teórica − Facturación Real del cierre
Ratio Refresco/Copa   = Refrescos consumidos / Copas teóricas
```

### Cómo probarlo

1. Asegurarse de que existen al menos 2 conteos consecutivos y cierres entre ellos
2. Ir a **Auditoría** (`/auditoria/`)
3. Se muestra el desglose por semana: botellas, copas, facturación, desviación

---

## Seguridad

- **Login con bloqueo**: 5 intentos → bloqueo 30 minutos
- **Admin restringido**: solo `is_superuser=True` accede a `/admin/`
- **Contraseña mínima**: 8 caracteres, 1 minúscula, 1 mayúscula, 1 dígito
- **Recordarme**: cookie 30 días si se marca el checkbox
- **Cerrar otras sesiones**: cierra todas las sesiones activas del usuario
- **Trazabilidad automática**: cada creación, modificación y eliminación de registro
  se guarda en `core.RegistroAuditoria` (visible en `/registro/` solo para superusers)

---

## Exportaciones

| Módulo    | Formato | URL                      |
|-----------|---------|--------------------------|
| Caja      | Excel   | `/caja/excel/`           |
| Inventario| Excel   | `/inventario/stock-excel/`|
| Pedidos   | Excel   | `/pedidos/excel/`        |
| Pedidos   | PDF     | `/pedidos/<id>/pdf/`     |
| Auditoría | Excel   | `/auditoria/excel/`      |

---

## Email / Notificaciones

Configuración en `.env`:

```
EMAIL_BACKEND=smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password
EMAIL_NOTIFY_TO=destinatario@correo.com
```

Se envía un email automáticamente cuando un pedido cambia a estado "Enviado al proveedor".

---

## Live Reload

El desarrollo en vivo está activo. Al guardar cambios en plantillas o código, el
navegador recarga automáticamente la página.

Para arrancarlo:

```
.\venv\Scripts\python.exe manage.py livereload
```

En otra terminal:

```
.\venv\Scripts\python.exe manage.py runserver
```

---

## Cómo probar la aplicación paso a paso

### Paso 1: Arrancar el servidor

```powershell
cd C:\wamp64\www\ProyectosDjango\mitpvnuevo
.\venv\Scripts\python.exe manage.py runserver
```

### Paso 2: Entrar al login

Abrir http://127.0.0.1:8000/ — redirige al login.

### Paso 3: Iniciar sesión

- Usuario: `admin`
- Contraseña: `admin12345`
- Marcar "Recordarme" si quieres cookie persistente

### Paso 4: Explorar Caja

1. Ir a Caja > Nuevo cierre
2. Introducir datos de ejemplo (mismos que el PDF):
   - Fecha: 12/09/2026, Servicio: viernes
   - Fondo de caja: 200€, Efectivo total: 1000€, TPV: 800€
   - Añadir pago: Antonio, 150€
3. Guardar → ver resumen: Facturación Total 1600€, Caja Restante 850€

### Paso 5: Probar el inventario táctil

1. Ir a Inventario > Contar stock (táctil)
2. Seleccionar pestaña "Rones"
3. Usar botones +/- para ajustar cantidades (botones grandes, táctiles)
4. Guardar el conteo

### Paso 6: Generar un pedido

1. Ir a Inventario > Conteos realizados
2. Entrar en el conteo acabado de crear
3. Pulsar "Generar pedidos"
4. Ir a Pedidos > Ver el pedido generado
5. Cambiar estado a "Enviado al proveedor" → se envía email automático

### Paso 7: Ver la auditoría

1. Ir a Auditoría
2. Se muestra el cruce de conteos: botellas consumidas, copas teóricas, facturación

### Paso 8: Trazabilidad (solo superusers)

1. Ir a Trazabilidad (`/registro/`)
2. Ver todas las acciones CRUD realizadas en el sistema

---

## Poblar datos con seed.py

### Ejecutar siempre (catálogo + demo)

```powershell
.\venv\Scripts\python.exe seed.py
```

### Solo catálogo base (sin datos demo)

```powershell
.\venv\Scripts\python.exe seed.py --solo-catalogo
```

### Qué crea

**Catálogo** (siempre):
- 40 productos, 3 proveedores, 7 categorías, 3 empleados
- Superusuarios: `admin / admin12345` y `jefe / jefe12345`

**Datos demo** (sin `--solo-catalogo`):
- 6 cierres de caja de los últimos 3 fines de semana
- 3 conteos de stock dominicales con líneas para todos los productos
- 4 pedidos generados a partir del último conteo

Es idempotente: ejecutarlo varias veces no duplica datos.

---

## Comandos útiles

```powershell
# Verificar que todo está OK
.\venv\Scripts\python.exe manage.py check

# Ejecutar test de humo (18 chequeos)
.\venv\Scripts\python.exe smoke_test.py

# Verificar contra el documento funcional (20 puntos)
.\venv\Scripts\python.exe verif_pdf.py

# Crear superusuario interactivo
.\venv\Scripts\python.exe manage.py createsuperuser

# Shell de Django
.\venv\Scripts\python.exe manage.py shell
```

---

## Documento funcional de referencia

El archivo `Documento_Funcional_Chill_Out_La_Bodeguita.pdf` contiene el
específico completo. Esta aplicación implementa el 100% de sus requisitos,
verificado por `verif_pdf.py` (20/20 puntos OK).

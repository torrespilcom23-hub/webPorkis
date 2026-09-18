# Prompt de Especificación — Web Porkis (Granja Porcina)

> **Rol:** Actúa como desarrollador full-stack senior en Python/Django. Construye una aplicación web para una granja de cerdos con sitio público informativo (HTML/CSS) y panel de administración interno funcional.

---

## 1. Contexto del proyecto

**Nombre del producto:** Web Porkis  
**Dominio de negocio:** Granja porcina comercial  
**Versión actual:** v1.0 — Prioridad en la **web informativa pública**; el **backend debe ser completamente funcional** desde el inicio.

**Objetivo:**
- Ofrecer presencia digital profesional al público (clientes, proveedores, visitantes).
- Centralizar la operación interna de la granja en un panel de control seguro.

**Usuarios:**

| Tipo | Descripción |
|------|-------------|
| Visitante | Navega el sitio público, consulta servicios y contacta vía formulario o WhatsApp |
| Administrador | Accede al panel con credenciales, gestiona inventario, registros y reportes |
| Operador de granja | Registra vacunas, alimentación, inseminaciones y movimientos de inventario |

---

## 2. Stack tecnológico (obligatorio)

| Capa | Tecnología |
|------|------------|
| Lenguaje backend | **Python 3.11+** |
| Framework | **Django 5.x** |
| Base de datos | **PostgreSQL 15** |
| Frontend público | **HTML5 + CSS3** (Django Templates) |
| Frontend admin | Django Templates + HTML/CSS (panel personalizado) |
| ORM | Django ORM (models, migrations) |
| Autenticación | Django Auth (`django.contrib.auth`) + grupos/permisos |
| Formularios | Django Forms / ModelForms |
| Reportes | **ReportLab** (PDF) + **openpyxl** (Excel) |
| Email | Django `send_mail` + SMTP |
| Archivos estáticos | Django `static/` + `collectstatic` |
| Servidor producción | Gunicorn + Nginx (o similar) |

**No usar:** Next.js, React, Vue, Node.js, Prisma ni frameworks JS pesados.

**JavaScript permitido (mínimo):**
- Vanilla JS para: menú móvil, carrusel, contadores animados, FAQ colapsable, validación UX del formulario de contacto.
- Sin bundlers obligatorios en v1 (opcional: un solo archivo `main.js`).

> Prioriza diseño responsive mobile-first, semántica HTML y accesibilidad WCAG 2.1 AA.

---

## 3. Alcance v1.0

### Prioridad 1 — Web informativa (entregar primero)
- Página **Inicio**
- Página **Servicios**
- Página **Contacto**
- Botón flotante de **WhatsApp** (inferior derecha, en todas las páginas)
- Layout compartido: header, footer, estilos globales

### Prioridad 2 — Backend funcional (en paralelo o inmediatamente después)
Panel de control completo y operativo con:
- Inventario
- Formulario de registro (cerdos, lotes)
- Reportes
- Seguimiento de vacunas
- Alimentos
- Inseminación

> En v1 el sitio público es estático/informativo con contenido editable desde admin. El panel admin es la herramienta operativa real de la granja.

---

## 4. FRONTEND — Sitio público informativo

### 4.1 Arquitectura de templates Django

```
templates/
├── base.html              # Layout maestro (header, footer, WhatsApp)
├── public/
│   ├── inicio.html
│   ├── servicios.html
│   └── contacto.html
└── partials/
    ├── header.html
    ├── footer.html
    └── whatsapp_button.html

static/
├── css/
│   ├── base.css
│   ├── inicio.css
│   ├── servicios.css
│   └── contacto.css
├── js/
│   └── main.js
└── images/
    ├── hero/
    ├── gallery/
    └── icons/
```

### 4.2 Rutas públicas

| URL | Vista Django | Template |
|-----|--------------|----------|
| `/` | `InicioView` | `public/inicio.html` |
| `/servicios/` | `ServiciosView` | `public/servicios.html` |
| `/contacto/` | `ContactoView` | `public/contacto.html` |

### 4.3 Estructura de navegación

```
┌─────────────────────────────────────────────┐
│  LOGO    Inicio | Servicios | Contacto      │  ← Header fijo
├─────────────────────────────────────────────┤
│                                             │
│              CONTENIDO DE PÁGINA            │
│                                             │
├─────────────────────────────────────────────┤
│  Footer: dirección, teléfono, redes         │
└─────────────────────────────────────────────┘
                                    [WhatsApp] ← flotante, inferior derecha
```

### 4.4 Página: Inicio (`/`)

**Secciones obligatorias:**
1. **Hero** — Imagen de la granja, titular, subtítulo, CTA → `/servicios/`
2. **Sobre nosotros** — Historia, misión, visión, valores
3. **Cifras clave** — Contadores animados (años, cerdos, hectáreas, clientes)
4. **Galería** — Grid de fotos de instalaciones y procesos
5. **Testimonios** — Carrusel con opiniones
6. **CTA final** — Invitación a contactar → `/contacto/`

**Requisitos:**
- `{% block meta %}` en base para SEO por página
- Lazy loading: `loading="lazy"` en imágenes
- Animaciones CSS/JS sutiles al scroll

### 4.5 Página: Servicios (`/servicios/`)

- Cards de servicios: icono, título, descripción, beneficios
- FAQ colapsable (HTML + JS vanilla o `<details>`)
- Banner CTA hacia contacto
- Contenido editable desde modelo `Servicio` en admin (opcional en v1, hardcode aceptable con estructura preparada)

### 4.6 Página: Contacto (`/contacto/`)

- Formulario Django: nombre, email, teléfono, asunto (select), mensaje
- Validación server-side (Django Form) + feedback visual
- Mapa embebido (iframe Google Maps / OpenStreetMap)
- Datos de contacto: dirección, teléfono, email, horario
- Al enviar: guardar en BD (`MensajeContacto`) + email vía SMTP
- Mensajes flash con Django messages framework

### 4.7 Botón flotante de WhatsApp

```css
/* static/css/base.css */
.whatsapp-float {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 50;
  /* verde #25D366, animación pulse */
}
```

```
Comportamiento: https://wa.me/{NUMERO}?text={MENSAJE_URL_ENCODED}
Accesibilidad: aria-label="Contactar por WhatsApp"
Visible en: base.html → partial whatsapp_button.html
```

**Configuración (`settings.py` / `.env`):**
```env
WHATSAPP_NUMBER=573001234567
WHATSAPP_DEFAULT_MESSAGE=Hola, me interesa conocer más sobre sus servicios en la granja.
```

### 4.8 Diseño visual (CSS puro)

- **Paleta:** verdes (#2D5016, #4A7C23), tierra (#8B6914), blanco, grises neutros
- **Tipografía:** Google Fonts — Inter o Poppins
- **Layout:** CSS Grid + Flexbox
- **Responsive:** mobile-first con media queries (640px, 768px, 1024px, 1280px)
- **Sin frameworks CSS obligatorios** (Bootstrap/Tailwind opcionales; preferir CSS propio en v1)

---

## 5. BACKEND — Panel de control (`/panel/`)

> Usar prefijo `/panel/` para el admin personalizado. Reservar `/admin/` para Django Admin nativo (superusuarios / respaldo técnico).

### 5.1 Autenticación y seguridad

- Login en `/panel/login/` con `AuthenticationForm` de Django
- `@login_required` en todas las vistas del panel
- Grupos Django:
  - `admin` — acceso total
  - `operador` — registro y consulta, sin gestión de usuarios
- CSRF en todos los formularios
- `LoginRequiredMixin` en Class-Based Views
- Auditoría: campos `created_by`, `updated_by`, `created_at`, `updated_at` en modelos críticos

### 5.2 Layout del panel

```
templates/panel/
├── base_panel.html        # Sidebar + header + content block
├── dashboard.html
├── inventario/
├── registro/
├── reportes/
├── vacunas/
├── alimentos/
└── inseminacion/
```

```
┌──────────┬────────────────────────────────────┐
│          │  Header: usuario, cerrar sesión    │
│ SIDEBAR  ├────────────────────────────────────┤
│          │                                    │
│ Dashboard│         ÁREA DE CONTENIDO          │
│ Inventario│                                   │
│ Registro │                                    │
│ Reportes │                                    │
│ Vacunas  │                                    │
│ Alimentos│                                    │
│ Inseminac│                                    │
└──────────┴────────────────────────────────────┘
```

**Dashboard:** KPIs (total cerdos, vacunas pendientes, stock bajo, partos del mes). Gráficos con Chart.js vía CDN (única dependencia JS externa permitida en panel).

---

### 5.3 App Django: `inventario`

**Modelos:**

```python
class CategoriaProducto(models.TextChoices):
    MEDICAMENTO = 'medicamento'
    INSUMO = 'insumo'
    EQUIPO = 'equipo'
    ALIMENTO = 'alimento'
    OTRO = 'otro'

class Producto(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=20, choices=CategoriaProducto.choices)
    unidad = models.CharField(max_length=20)  # kg, L, unidad
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proveedor = models.CharField(max_length=200, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    # timestamps + auditoría

class MovimientoInventario(models.Model):
    ENTRADA = 'entrada'
    SALIDA = 'salida'
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=[(ENTRADA,'Entrada'),(SALIDA,'Salida')])
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    motivo = models.CharField(max_length=300)
    registrado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Vistas:** listado con filtros, crear/editar producto, registrar movimiento, alerta visual si `stock_actual <= stock_minimo`.

---

### 5.4 App Django: `registro`

**Modelo `Cerdo`:**

| Campo | Tipo Django | Obligatorio |
|-------|-------------|-------------|
| arete | CharField unique | Sí |
| raza | CharField / FK | Sí |
| sexo | CharField (M/H) | Sí |
| fecha_nacimiento | DateField | Sí |
| peso_actual | DecimalField | No |
| estado | CharField choices | Sí |
| corral | CharField | No |
| madre | ForeignKey(self) | No |
| padre | ForeignKey(self) | No |
| observaciones | TextField | No |

**Modelo `Lote`:** nombre, corral, fecha_ingreso, meta_peso, cerdos (M2M o FK inversa).

**Vistas:** CRUD cerdos, CRUD lotes, detalle de cerdo con tabs (vacunas, alimentos, inseminaciones), import CSV con `django-import-export` (opcional).

---

### 5.5 App Django: `reportes`

| Reporte | Vista | Export |
|---------|-------|--------|
| Inventario general | `/panel/reportes/inventario/` | PDF / Excel |
| Producción (cerdos) | `/panel/reportes/produccion/` | PDF / Excel |
| Sanitario (vacunas) | `/panel/reportes/sanitario/` | PDF / Excel |
| Alimentación | `/panel/reportes/alimentacion/` | PDF / Excel |
| Reproductivo | `/panel/reportes/reproductivo/` | PDF / Excel |

**Implementación:**
- Filtros via GET (fecha desde/hasta, corral, raza, etc.)
- Vista previa HTML con tablas
- Export PDF: ReportLab
- Export Excel: openpyxl
- `HttpResponse` con content-type correcto

---

### 5.6 App Django: `vacunas`

```python
class Vacuna(models.Model):
    nombre = models.CharField(max_length=200)
    intervalo_dias = models.PositiveIntegerField(null=True, blank=True)
    descripcion = models.TextField(blank=True)

class AplicacionVacuna(models.Model):
    cerdo = models.ForeignKey('registro.Cerdo', on_delete=models.CASCADE, related_name='vacunas')
    vacuna = models.ForeignKey(Vacuna, on_delete=models.PROTECT)
    fecha_aplicacion = models.DateField()
    dosis = models.CharField(max_length=100)
    lote_medicamento = models.CharField(max_length=100, blank=True)
    proxima_dosis = models.DateField(null=True, blank=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True)
```

**Funcionalidades:**
- CRUD catálogo de vacunas
- Registro de aplicaciones
- Listado de pendientes (`proxima_dosis <= hoy`)
- Alertas en dashboard
- Descuento opcional de stock al aplicar (signal post_save → MovimientoInventario)

---

### 5.7 App Django: `alimentos`

```python
class TipoAlimento(models.Model):
    nombre = models.CharField(max_length=200)
    proteina_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    proveedor = models.CharField(max_length=200, blank=True)
    costo_por_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

class PlanAlimentacion(models.Model):
    ETAPAS = [('destete','Destete'),('crecimiento','Crecimiento'),('engorde','Engorde'),
              ('gestacion','Gestación'),('lactancia','Lactancia')]
    lote = models.ForeignKey('registro.Lote', on_delete=models.CASCADE)
    tipo_alimento = models.ForeignKey(TipoAlimento, on_delete=models.PROTECT)
    cantidad_diaria_kg = models.DecimalField(max_digits=8, decimal_places=2)
    etapa = models.CharField(max_length=20, choices=ETAPAS)

class RegistroAlimentacion(models.Model):
    fecha = models.DateField()
    lote = models.ForeignKey('registro.Lote', on_delete=models.CASCADE)
    tipo_alimento = models.ForeignKey(TipoAlimento, on_delete=models.PROTECT)
    cantidad_servida_kg = models.DecimalField(max_digits=8, decimal_places=2)
    cantidad_sobrante_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    registrado_por = models.ForeignKey(User, on_delete=models.PROTECT)
```

---

### 5.8 App Django: `inseminacion`

```python
class Padrillo(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    raza = models.CharField(max_length=100)
    origen = models.CharField(max_length=20, choices=[('interno','Interno'),('externo','Externo')])
    stock_pajuelas = models.PositiveIntegerField(default=0)

class Inseminacion(models.Model):
    cerda = models.ForeignKey('registro.Cerdo', on_delete=models.PROTECT, related_name='inseminaciones')
    fecha = models.DateField()
    tipo = models.CharField(max_length=20, choices=[('natural','Natural'),('artificial','Artificial')])
    padrillo = models.ForeignKey(Padrillo, on_delete=models.PROTECT, null=True, blank=True)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True)

class DiagnosticoPrenez(models.Model):
    inseminacion = models.OneToOneField(Inseminacion, on_delete=models.CASCADE)
    fecha = models.DateField()
    resultado = models.CharField(max_length=20, choices=[
        ('positivo','Positivo'),('negativo','Negativo'),('dudoso','Dudoso')])
    metodo = models.CharField(max_length=100, blank=True)

class Parto(models.Model):
    inseminacion = models.ForeignKey(Inseminacion, on_delete=models.PROTECT)
    fecha = models.DateField()
    lechones_vivos = models.PositiveIntegerField()
    lechones_muertos = models.PositiveIntegerField(default=0)
    lechones_destetados = models.PositiveIntegerField(null=True, blank=True)
```

**Flujo:** Inseminación → Diagnóstico (21-28 días) → Parto → registro de lechones en `Cerdo`.

---

### 5.9 App Django: `publico` (sitio informativo)

```python
class Servicio(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, blank=True)  # clase CSS o emoji
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

class MensajeContacto(models.Model):
    nombre = models.CharField(max_length=200)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 6. Estructura del proyecto Django

```
webPorkis/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── config/                          # Proyecto Django
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── publico/                     # Web informativa
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── models.py
│   │   └── forms.py
│   ├── panel/                       # Dashboard + layout panel
│   ├── inventario/
│   ├── registro/
│   ├── vacunas/
│   ├── alimentos/
│   ├── inseminacion/
│   └── reportes/
├── templates/
│   ├── base.html
│   ├── public/
│   ├── panel/
│   └── partials/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── media/                           # uploads (galería, etc.)
```

---

## 7. URLs principales

```python
# config/urls.py
urlpatterns = [
    path('', include('apps.publico.urls')),          # /, /servicios/, /contacto/
    path('panel/', include('apps.panel.urls')),       # dashboard
    path('panel/inventario/', include('apps.inventario.urls')),
    path('panel/registro/', include('apps.registro.urls')),
    path('panel/vacunas/', include('apps.vacunas.urls')),
    path('panel/alimentos/', include('apps.alimentos.urls')),
    path('panel/inseminacion/', include('apps.inseminacion.urls')),
    path('panel/reportes/', include('apps.reportes.urls')),
    path('admin/', admin.site.urls),                  # Django Admin nativo
]
```

---

## 8. Base de datos — PostgreSQL 15

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=webporkis
DB_USER=webporkis_user
DB_PASSWORD=changeme
DB_HOST=localhost
DB_PORT=5432
```

**Diagrama relacional simplificado:**

```
auth_user ────────────────────────────────────────┐
                                                  │
registro_cerdo ◄── vacunas_aplicacionvacuna ──► vacunas_vacuna
  │                                               │
  ├── alimentos_registroalimentacion ──► alimentos_tipoalimento
  │                                               │
  ├── inseminacion_inseminacion ──► DiagnosticoPrenez
  │         │                                     │
  │         └──► Parto ──► registro_cerdo (lechones)
  │                                               │
  └── inventario_movimientoinventario ◄── inventario_producto
                                                  │
publico_mensajecontacto                           │
publico_servicio                                  │
```

**Comandos iniciales:**
```bash
python -m venv venv
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 9. requirements.txt (referencia)

```
Django>=5.0,<6.0
psycopg2-binary>=2.9
python-decouple>=3.8
Pillow>=10.0
reportlab>=4.0
openpyxl>=3.1
gunicorn>=21.0
whitenoise>=6.6
django-import-export>=3.3   # opcional, CSV
```

---

## 10. Variables de entorno (.env.example)

```env
DEBUG=True
SECRET_KEY=generar-clave-secreta-django
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL 15
DB_NAME=webporkis
DB_USER=webporkis_user
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

# WhatsApp
WHATSAPP_NUMBER=573001234567
WHATSAPP_DEFAULT_MESSAGE=Hola, me interesa conocer más sobre la granja.

# Email contacto
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=info@granja.com
CONTACT_RECIPIENT_EMAIL=info@granja.com

# Maps
MAPS_EMBED_URL=https://maps.google.com/maps?q=...&output=embed
```

---

## 11. Fases de implementación

### Fase 1 — Web informativa v1 (prioridad)
- [ ] Setup Django + PostgreSQL 15 + estructura de apps
- [ ] `base.html`, CSS global, header, footer
- [ ] Página Inicio (todas las secciones)
- [ ] Página Servicios
- [ ] Página Contacto + formulario funcional
- [ ] Botón WhatsApp en todas las páginas
- [ ] Responsive mobile/tablet/desktop
- [ ] Modelos `Servicio` y `MensajeContacto` + Django Admin básico

### Fase 2 — Backend funcional
- [ ] Auth panel (`/panel/login/`)
- [ ] Layout panel con sidebar
- [ ] Dashboard con KPIs
- [ ] Módulo Inventario (CRUD + movimientos + alertas)
- [ ] Módulo Registro (cerdos + lotes)
- [ ] Módulo Vacunas
- [ ] Módulo Alimentos
- [ ] Módulo Inseminación
- [ ] Módulo Reportes (PDF + Excel)

### Fase 3 — Pulido
- [ ] Importación CSV de cerdos
- [ ] SEO: sitemap.xml, robots.txt, schema.org LocalBusiness
- [ ] Tests unitarios (models, forms, vistas críticas)
- [ ] `collectstatic`, Gunicorn, documentación despliegue
- [ ] Fixtures de datos demo

---

## 12. Criterios de aceptación v1

**Web informativa:**
- [ ] 3 páginas accesibles: `/`, `/servicios/`, `/contacto/`
- [ ] Diseño profesional agrícola, responsive
- [ ] Botón WhatsApp funcional en esquina inferior derecha
- [ ] Formulario contacto valida, guarda en BD y envía email
- [ ] HTML semántico, CSS organizado, sin dependencias JS pesadas

**Panel admin:**
- [ ] Login requerido en `/panel/`
- [ ] CRUD funcional: Inventario, Registro, Vacunas, Alimentos, Inseminación
- [ ] Reportes exportan PDF y Excel
- [ ] Dashboard muestra alertas de stock bajo y vacunas pendientes
- [ ] PostgreSQL 15 como única base de datos

---

## 13. Instrucción final para el agente/desarrollador

> Implementa el proyecto **Web Porkis** con **Python + Django + PostgreSQL 15 + HTML + CSS**. **Empieza por la web informativa** (Inicio, Servicios, Contacto + botón WhatsApp) usando Django Templates y CSS propio responsive. En paralelo o a continuación, construye el **panel de control funcional** en `/panel/` con todos los módulos: Inventario, Registro, Reportes, Vacunas, Alimentos e Inseminación. Usa Django ORM, Forms, Auth y migraciones. No uses Next.js, React ni Node. Incluye `requirements.txt`, `.env.example`, fixtures opcionales y README con setup local (venv, PostgreSQL 15, migrate, runserver). Código limpio, apps Django separadas por dominio, y templates reutilizables con herencia (`{% extends %}`).

---

*Documento actualizado — Web Porkis v1.0 | Django + PostgreSQL 15 + HTML/CSS*

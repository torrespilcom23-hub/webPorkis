# Web Porkis — Granja Porcina

Aplicación web con sitio informativo público y panel de administración para gestión de granja porcina.

## Stack

- Python 3.11+
- Django 5.x
- PostgreSQL 15 (producción) / SQLite (desarrollo local)
- HTML5 + CSS3 + Django Templates

## Instalación local

### 1. Clonar e instalar dependencias

```bash
cd webPorkis
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configurar entorno

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
```

Editar `.env` según necesidad:

- **Desarrollo rápido (SQLite):** `USE_SQLITE=True`
- **PostgreSQL 15:** `USE_SQLITE=False` y configurar `DB_*`

### 3. PostgreSQL 15 (producción local — ya desplegado)

La base de datos `porkis` ya está creada en el servidor PostgreSQL 15 local
(puerto **5433**), con usuario dedicado `porkis_user` (dueño solo de esa BD).

Configuración actual en `.env`:

```env
USE_SQLITE=False
DB_NAME=porkis
DB_USER=porkis_user
DB_PASSWORD=Porkis2026Secure
DB_HOST=localhost
DB_PORT=5433
```

> Nota: el PostgreSQL 15 local escucha en el puerto **5433** (no 5432).

### 4. Migrar y cargar datos

```bash
python manage.py migrate
python manage.py seed_data
```

### 5. Ejecutar servidor

```bash
python manage.py runserver
```

## URLs

| URL | Descripción |
|-----|-------------|
| http://localhost:8000/ | Inicio |
| http://localhost:8000/servicios/ | Servicios |
| http://localhost:8000/contacto/ | Contacto |
| http://localhost:8000/panel/ | Panel de control |
| http://localhost:8000/admin/ | Django Admin |

## Credenciales demo

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin` | `admin123` | Administrador (acceso total) |
| `operador` | `operador123` | Operador (registro y consulta, sin eliminar) |

## Módulos del panel

- Inventario (productos, movimientos, alertas stock)
- Registro (cerdos, lotes)
- Vacunas (catálogo, aplicaciones, pendientes)
- Alimentos (tipos, planes, consumo)
- Inseminación (padrillos, inseminaciones, diagnósticos, partos)
- Reportes (PDF y Excel, con filtros)
- Mensajes de contacto (bandeja de entrada)
- Servicios web (gestión del contenido público)

## WhatsApp

Configurar en `.env`:

```env
WHATSAPP_NUMBER=51904013194
WHATSAPP_DEFAULT_MESSAGE=Hola, me interesa conocer más sobre la granja Porkis.
```

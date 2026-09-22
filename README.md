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

**Reiniciar datos de prueba (local):** vacía todas las tablas y deja solo usuarios demo:

```bash
python manage.py reset_datos_local --force
```

No borra migraciones ni la estructura; elimina cerdos, inventario, vacunas, mensajes, etc.

### 5. Ejecutar servidor

```bash
python manage.py runserver
```

En Windows también puedes usar `iniciar_servidor.bat` (escucha en `0.0.0.0:8000` para pruebas en red).

### Pruebas en red local (otro PC en la misma LAN)

1. En `.env`, incluye tu IP LAN en `ALLOWED_HOSTS` y en `CSRF_TRUSTED_ORIGINS` (ver `.env.example`).
2. Arranca el servidor escuchando en todas las interfaces:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
3. En el **Firewall de Windows**, permite entrantes TCP en el puerto **8000** (solo mientras pruebas):
   ```powershell
   netsh advfirewall firewall add rule name="Porkis Django 8000" dir=in action=allow protocol=TCP localport=8000
   ```
4. El otro usuario abre en su navegador: `http://TU_IP_LAN:8000/panel/` (ej. `http://172.17.74.7:8000/panel/`).

Requisitos: mismo Wi‑Fi o red cableada; tu PC encendido con el servidor corriendo. No expongas esto a Internet público con `DEBUG=True`.

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
| `admin` | `admin2026**` | Administrador (acceso total) |
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

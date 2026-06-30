# odoo_dev_env

Ambiente de desarrollo local para Odoo 19.

Este repositorio no contiene el codigo fuente de Odoo ni ejecuta Odoo dentro de Docker. Su funcion es preparar y documentar el entorno local de apoyo para desarrollar Odoo 19:

- PostgreSQL en Docker.
- Mailpit en Docker para capturar correos salientes.
- Configuracion local de Odoo en `config/odoo19.conf`.
- Entorno virtual Python local en `.venv`.
- Carpetas para addons propios y de terceros.
- Workspace de VS Code que abre este repositorio junto con el codigo fuente de Odoo 19.

## Estructura

```text
.
├── addons/
│   ├── custom/          # Modulos propios
│   └── third_party/     # Modulos externos o de terceros
├── config/
│   └── odoo19.conf      # Configuracion principal de Odoo 19
├── scripts/
│   └── setup-odoo19-python.sh
├── .env.example         # Variables base para Docker Compose
├── docker-compose.yml   # PostgreSQL + Mailpit
└── odoo_dev_env.code-workspace
```

## Rutas esperadas

El ambiente esta pensado para trabajar con estas rutas locales:

```text
/home/ruiznorlan/Documentos/odoo_dev_env
/home/ruiznorlan/Documentos/odoo/19.0
```

La configuracion `config/odoo19.conf` espera que el codigo fuente de Odoo este disponible en:

```text
/home/ruiznorlan/Documentos/odoo/19.0/odoo
```

El workspace `odoo_dev_env.code-workspace` abre dos carpetas:

- Este ambiente: `odoo_dev_env`.
- El codigo fuente: `../odoo/19.0`.

## Servicios Docker

`docker-compose.yml` levanta solo servicios auxiliares:

| Servicio | Imagen | Uso | Puerto local |
| --- | --- | --- | --- |
| `db` | `postgres:${POSTGRES_VERSION}` | Base de datos PostgreSQL para Odoo | `5432` |
| `mailpit` | `axllent/mailpit:latest` | Captura de correos SMTP en desarrollo | SMTP `1025`, Web `8025` |

La base de datos usa el volumen persistente:

```text
odoo19-postgres-data
```

La red Docker usada por los servicios es:

```text
odoo19-net
```

## Variables de entorno

El archivo `.env.example` contiene los valores base:

```env
PROJECT_NAME=odoo19-dev

POSTGRES_VERSION=16
POSTGRES_CONTAINER_NAME=odoo19-postgres
POSTGRES_DB=postgres
POSTGRES_USER=odoo
POSTGRES_PASSWORD=odoo
POSTGRES_PORT=5432

MAILPIT_CONTAINER_NAME=odoo19-mailpit
MAILPIT_SMTP_PORT=1025
MAILPIT_WEB_PORT=8025

TZ=America/Costa_Rica
```

Para preparar el entorno:

```bash
cp .env.example .env
```

El archivo `.env` queda fuera de Git para permitir ajustes locales.

## Configuracion de Odoo

La configuracion principal esta en:

```text
config/odoo19.conf
```

Comportamiento importante:

- Odoo se conecta a PostgreSQL en `localhost:5432`.
- El usuario de base de datos es `odoo`.
- La contrasena de base de datos es `odoo`.
- El puerto HTTP de Odoo es `8069`.
- `workers = 0`, orientado a desarrollo local.
- `dev = all`, habilitando modo desarrollo.
- `max_cron_threads = 1`, permitiendo cron local con baja concurrencia.
- Mailpit se usa como SMTP local en `localhost:1025`.
- El `data_dir` de Odoo queda dentro del repositorio en `.local/share/Odoo19`.

Los addons cargados por Odoo son:

```text
/home/ruiznorlan/Documentos/odoo/19.0/odoo/addons
/home/ruiznorlan/Documentos/odoo/19.0/addons
/home/ruiznorlan/Documentos/odoo_dev_env/addons/custom
/home/ruiznorlan/Documentos/odoo_dev_env/addons/third_party
```

## Preparacion inicial

1. Clonar o ubicar Odoo 19 en la ruta esperada:

```bash
mkdir -p /home/ruiznorlan/Documentos/odoo
```

El codigo fuente debe quedar disponible en:

```text
/home/ruiznorlan/Documentos/odoo/19.0/odoo/odoo-bin
```

2. Crear el archivo `.env`:

```bash
cp .env.example .env
```

3. Instalar dependencias del sistema y preparar el entorno Python:

```bash
./scripts/setup-odoo19-python.sh
```

El script:

- Usa Python 3.12 por defecto.
- Crea o reutiliza `.venv`.
- Instala dependencias del sistema necesarias para Odoo.
- Instala `requirements.txt` desde el codigo fuente de Odoo 19.
- Valida que `odoo-bin` pueda ejecutarse.

Tambien se pueden sobrescribir rutas con variables:

```bash
PYTHON_BIN=python3.12 \
ODOO_DIR=/home/ruiznorlan/Documentos/odoo/19.0/odoo \
DEV_ENV_DIR=/home/ruiznorlan/Documentos/odoo_dev_env \
./scripts/setup-odoo19-python.sh
```

## Levantar el ambiente

1. Iniciar PostgreSQL y Mailpit:

```bash
docker compose up -d
```

2. Activar el entorno virtual:

```bash
source .venv/bin/activate
```

3. Ejecutar Odoo desde el codigo fuente:

```bash
cd /home/ruiznorlan/Documentos/odoo/19.0/odoo
python odoo-bin -c /home/ruiznorlan/Documentos/odoo_dev_env/config/odoo19.conf
```

4. Abrir Odoo:

```text
http://localhost:8069
```

5. Abrir Mailpit:

```text
http://localhost:8025
```

## Flujo de desarrollo

Los modulos propios deben ir en:

```text
addons/custom
```

Los modulos externos o de terceros pueden ir en:

```text
addons/third_party
```

Despues de agregar o modificar modulos, reinicia Odoo y actualiza la lista de aplicaciones desde la interfaz. Para actualizar un modulo especifico desde terminal:

```bash
cd /home/ruiznorlan/Documentos/odoo/19.0/odoo
python odoo-bin \
  -c /home/ruiznorlan/Documentos/odoo_dev_env/config/odoo19.conf \
  -d nombre_base_datos \
  -u nombre_modulo
```

Para instalar un modulo:

```bash
cd /home/ruiznorlan/Documentos/odoo/19.0/odoo
python odoo-bin \
  -c /home/ruiznorlan/Documentos/odoo_dev_env/config/odoo19.conf \
  -d nombre_base_datos \
  -i nombre_modulo
```

## Comandos utiles

Ver estado de los servicios:

```bash
docker compose ps
```

Ver logs de PostgreSQL:

```bash
docker compose logs -f db
```

Ver logs de Mailpit:

```bash
docker compose logs -f mailpit
```

Detener servicios:

```bash
docker compose down
```

Detener servicios y eliminar el volumen de PostgreSQL:

```bash
docker compose down -v
```

> Este ultimo comando elimina los datos locales de PostgreSQL.

## Validacion con Dagger

El repositorio incluye un modulo Dagger y un workflow de GitHub Actions para validar que un clon fresco pueda levantar el ambiente base de Odoo 19.

La validacion:

- Levanta PostgreSQL 16 como servicio Dagger.
- Levanta Mailpit como servicio Dagger.
- Clona Odoo `19.0` dentro del contenedor de CI.
- Instala los requirements de Odoo.
- Genera un `odoo.conf` temporal con rutas propias del contenedor.
- Arranca Odoo y valida que responda en `http://127.0.0.1:8069/`.

Para ejecutarlo localmente con Dagger:

```bash
dagger call verify --source=.
```

En GitHub Actions se ejecuta desde:

```text
.github/workflows/ci.yml
```

## Datos locales ignorados por Git

El repositorio ignora archivos generados o sensibles, entre ellos:

- `.env`
- `.venv/`
- `.local/`
- caches de Python
- dumps o backups de bases de datos
- logs
- archivos locales de Docker Compose
- llaves y certificados

Esto mantiene versionados solo los archivos necesarios para reproducir el ambiente.

## Resumen del comportamiento

Este repositorio actua como capa de desarrollo alrededor de Odoo 19:

1. Docker entrega PostgreSQL y Mailpit.
2. Python se ejecuta localmente desde `.venv`.
3. Odoo se arranca manualmente desde `/home/ruiznorlan/Documentos/odoo/19.0/odoo`.
4. La configuracion vive en `config/odoo19.conf`.
5. Los addons del proyecto viven en `addons/custom` y `addons/third_party`.

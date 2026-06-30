#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# Odoo 19 Python Environment Setup
# elementary OS 8.1 / Ubuntu 24.04 compatible
# ==========================================================
#
# Este script:
# - NO modifica el Python del sistema.
# - Crea el entorno virtual en odoo_dev_env/.venv.
# - Instala pip, setuptools, wheel y requirements.txt de Odoo 19.
#
# Rutas esperadas:
# - Código fuente Odoo:
#   /home/ruiznorlan/Documentos/odoo/19.0
#
# - Entorno de desarrollo:
#   /home/ruiznorlan/Documentos/odoo_dev_env
#
# ==========================================================

PYTHON_BIN="${PYTHON_BIN:-python3.12}"

ODOO_DIR="${ODOO_DIR:-${HOME}/Documentos/odoo/19.0/odoo}"
DEV_ENV_DIR="${DEV_ENV_DIR:-${HOME}/Documentos/odoo_dev_env}"
VENV_DIR="${VENV_DIR:-${DEV_ENV_DIR}/.venv}"

echo "=========================================================="
echo " Odoo 19 Python environment setup"
echo "=========================================================="
echo "Python binary : ${PYTHON_BIN}"
echo "Odoo dir      : ${ODOO_DIR}"
echo "Dev env dir   : ${DEV_ENV_DIR}"
echo "Virtualenv    : ${VENV_DIR}"
echo "=========================================================="

echo ""
echo "0) Validando rutas base..."

if [ ! -d "${ODOO_DIR}" ]; then
    echo "ERROR: No existe la carpeta de Odoo:"
    echo "  ${ODOO_DIR}"
    exit 1
fi

if [ ! -d "${DEV_ENV_DIR}" ]; then
    echo "ERROR: No existe la carpeta del ambiente:"
    echo "  ${DEV_ENV_DIR}"
    echo ""
    echo "Puedes crearla con:"
    echo "  mkdir -p ${DEV_ENV_DIR}"
    exit 1
fi

cd "${ODOO_DIR}"

if [ ! -f "odoo-bin" ]; then
    echo "ERROR: No se encontró odoo-bin en:"
    echo "  $(pwd)"
    echo ""
    echo "Verifica que Odoo 19 esté clonado en:"
    echo "  ${ODOO_DIR}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "ERROR: No se encontró requirements.txt en:"
    echo "  $(pwd)"
    exit 1
fi

echo ""
echo "1) Instalando dependencias del sistema..."
sudo apt update

sudo apt install -y \
    git \
    build-essential \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-wheel \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    liblcms2-dev \
    libblas-dev \
    libatlas-base-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    libwebp-dev \
    npm \
    node-less \
    postgresql-client

echo ""
echo "2) Validando Python..."
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "ERROR: No se encontró ${PYTHON_BIN}."
    echo ""
    echo "Puedes verificar versiones instaladas con:"
    echo "  ls /usr/bin/python3*"
    exit 1
fi

"${PYTHON_BIN}" --version

echo ""
echo "3) Creando entorno virtual en odoo_dev_env si no existe..."

mkdir -p "${DEV_ENV_DIR}"

if [ ! -d "${VENV_DIR}" ]; then
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
    echo "Virtualenv creado en:"
    echo "  ${VENV_DIR}"
else
    echo "Virtualenv ya existe en:"
    echo "  ${VENV_DIR}"
fi

echo ""
echo "4) Activando entorno virtual..."

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "Python activo:"
which python
python --version

echo ""
echo "Pip activo:"
which pip
pip --version

echo ""
echo "5) Actualizando pip, setuptools y wheel..."
python -m pip install --upgrade pip setuptools wheel

echo ""
echo "6) Instalando requirements.txt de Odoo..."
cd "${ODOO_DIR}"
python -m pip install -r requirements.txt

echo ""
echo "6.1) Instalando debugpy para depuracion desde VS Code..."
python -m pip install debugpy

echo ""
echo "7) Validando Odoo..."
python odoo-bin --help >/dev/null

echo ""
echo "=========================================================="
echo " Ambiente Python para Odoo 19 listo correctamente."
echo "=========================================================="
echo ""
echo "Entorno virtual creado/usado en:"
echo "  ${VENV_DIR}"
echo ""
echo "Para activarlo:"
echo "  source ${VENV_DIR}/bin/activate"
echo ""
echo "Para iniciar Odoo:"
echo "  cd ${ODOO_DIR}"
echo "  python odoo-bin -c ${DEV_ENV_DIR}/config/odoo19.conf"
echo ""

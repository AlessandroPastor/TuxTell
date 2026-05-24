#!/bin/bash
# Ejecutar como root en el VPS Elastika (Ubuntu 22.04)
# Uso: bash deploy/setup.sh

set -e

APP_DIR="/opt/wisp-backend"
APP_USER="wisp"

echo "=== 1. Actualizando sistema ==="
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git postgresql postgresql-contrib nginx wireguard

echo "=== 2. Creando usuario del sistema ==="
id -u $APP_USER &>/dev/null || useradd -m -s /bin/bash $APP_USER

echo "=== 3. Configurando PostgreSQL ==="
sudo -u postgres psql -c "CREATE USER tuxtell WITH PASSWORD 'tuxtell123';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE tuxtelldb OWNER tuxtell;" 2>/dev/null || true

echo "=== 4. Clonando proyecto ==="
if [ ! -d "$APP_DIR" ]; then
    git clone https://AlessandroPastor:$GH_TOKEN@github.com/AlessandroPastor/TuxTell.git $APP_DIR
else
    cd $APP_DIR && git pull
fi

echo "=== 5. Instalando dependencias Python ==="
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== 6. Configurando .env ==="
if [ ! -f "$APP_DIR/.env" ]; then
    cp $APP_DIR/.env.example $APP_DIR/.env
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s|DATABASE_URL=sqlite.*|DATABASE_URL=postgresql://tuxtell:tuxtell123@localhost:5432/tuxtelldb|" $APP_DIR/.env
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET|" $APP_DIR/.env
    echo "[OK] .env creado con SECRET_KEY generada automáticamente"
else
    echo "[!] .env ya existe, no se sobreescribe"
fi

echo "=== 7. Creando tablas y usuario admin ==="
cd $APP_DIR
source venv/bin/activate
python seed.py

echo "=== 8. Instalando servicio systemd ==="
cp $APP_DIR/deploy/wisp-backend.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable wisp-backend
systemctl restart wisp-backend

echo ""
echo "=========================================="
echo " WISP Backend desplegado correctamente"
echo " URL: http://161.132.48.127:8000"
echo " Docs: http://161.132.48.127:8000/docs"
echo "=========================================="

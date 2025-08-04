#!/bin/bash

echo "🚀 Iniciando instalación de dependencias para el bot WireGuard..."

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip wireguard qrencode

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

mkdir -p data wg_confs
touch data/users.json
echo '{}' > data/users.json

echo "✅ Instalación completada correctamente."
echo "🛠 Puedes iniciar el bot con: source venv/bin/activate && python3 main.py"

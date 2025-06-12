#!/bin/sh
set -e

# Crear un subdirectorio para la base de datos si no existe
mkdir -p /var/data/database

echo "Ejecutando migraciones de la base de datos..."
python manage.py migrate --no-input

echo "Iniciando el servidor Gunicorn..."
exec gunicorn --workers 1 eventhub.wsgi:application
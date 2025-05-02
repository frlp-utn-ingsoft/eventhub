#!/bin/bash

python_interpreter="python"
#python_interpreter="python3"

db_file="db.sqlite3"
if [ -f "$db_file" ]; then
    read -p "Ya existe la base de datos ¿Desea eliminarla y crear una nueva? (y/n): " confirm_delete_db
    if [ "$confirm_delete_db" == "y" ]; then
        echo "==> Eliminando base de datos..."
        rm "$db_file"
        echo "✅  El archivo $db_file fue eliminado..."

        echo "==> Eliminando archivos de migración..."
        find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
        find . -path "*/migrations/*.pyc" -delete
    fi
fi

echo "==> Creando migraciones..."
$python_interpreter manage.py makemigrations
$python_interpreter manage.py migrate
$python_interpreter manage.py migrate cities_light
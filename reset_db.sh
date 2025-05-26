#!/bin/bash

#python_interpreter="python"
python_interpreter="python3"

# 1. eliminar la base de datos del proyecto
echo "==> Eliminando base de datos..."

db_file="db.sqlite3"
dir_data="fixtures"

if [ -f "$db_file" ]; then
    rm "$db_file"
    echo "✅  El archivo $db_file fue eliminado..."
else
    echo "❌ El archivo $db_file no existe"
fi

# 2. eliminar todos los archivos de migraciones del proyecto
echo "==> Eliminando archivos de migración..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 3. crear nuevamente las migraciones
echo "==> Creando migraciones..."
$python_interpreter manage.py makemigrations
$python_interpreter manage.py migrate


if [ -d "$dir_data" ]; then
    echo "==> Cargando datos de prueba desde $dir_data..."
    $python_interpreter manage.py loaddata "./fixtures/venues.json" && \
    $python_interpreter manage.py loaddata "./fixtures/categories.json" && \
    $python_interpreter manage.py loaddata "./fixtures/users.json" && \
    $python_interpreter manage.py loaddata "./fixtures/events.json" && \
    $python_interpreter manage.py loaddata "./fixtures/tickets.json" && \
    $python_interpreter manage.py loaddata "./fixtures/comments.json" && \
    $python_interpreter manage.py loaddata "./fixtures/notifications.json" && \
    $python_interpreter manage.py loaddata "./fixtures/refounds_request.json" && \
    $python_interpreter manage.py loaddata "./fixtures/rating.json" && \
    $python_interpreter manage.py loaddata "./fixtures/notifications.json"
    
    echo "✅ Datos de prueba cargados."
else
    echo "❌ El directorio $dir_data no existe..."
fi
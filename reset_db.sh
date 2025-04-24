#!/bin/bash

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
python3 manage.py makemigrations
python3 manage.py migrate

# 4. crear superusuario
read -p "¿Desea crear un superusuario? (y/n): " create_superuser
if [ "$create_superuser" == "y" ]; then
    python3 manage.py createsuperuser
fi

# 5. cargar datos de prueba
read -p "¿Desea cargar datos de prueba (fixtures)? (y/n): " load_fixtures
if [ "$load_fixtures" == "y" ]; then 
    if [ -d "$dir_data" ]; then
        echo "==> Cargando datos de prueba desde $dir_data..."
        
        for fixture in "$dir_data"/*.json; do
            echo "   -> Cargando $fixture..."
            python3 manage.py loaddata "$fixture"
            echo "✅ Archivo $fixture cargado"
        done

        echo "✅ Datos de prueba cargados."
    else
        echo "❌ El directorio $dir_data no existe..."
    fi
fi

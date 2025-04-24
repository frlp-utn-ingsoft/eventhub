#!/bin/bash

python_interpreter=""
if command -v python3 &>/dev/null; then
    python_interpreter="python3"
elif command -v python &>/dev/null; then
    python_interpreter="python"
else
    echo "Error: No se encontró un intérprete de Python válido."
    exit 1
fi

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

# 4. crear superusuario
read -p "¿Desea crear un superusuario? (y/n): " create_superuser
if [ "$create_superuser" == "y" ]; then
    $python_interpreter manage.py createsuperuser
fi

# 5. cargar datos de prueba
read -p "¿Desea cargar datos de prueba (fixtures)? (y/n): " load_fixtures
if [ "$load_fixtures" == "y" ]; then 
    if [ -d "$dir_data" ]; then
        echo "==> Cargando datos de prueba desde $dir_data..."
        
        for fixture in "$dir_data"/*.json; do
            echo "   -> Cargando $fixture..."
            $python_interpreter manage.py loaddata "$fixture"
            echo "✅ Archivo $fixture cargado"
        done

        echo "✅ Datos de prueba cargados."
    else
        echo "❌ El directorio $dir_data no existe..."
    fi
fi

# Eventhub

Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP

## Integrantes
1. Petosa Ayala Franco
2. Gonzalo Gerez
3. Isabella Bresciani
4. Silvia Romero
5. Sofia Belen Raggi
6. Sofia Lara Goszko

## Dependencias

- python 3
- Django
- sqlite
- playwright
- ruff

## Instalar dependencias

```
pip install -r requirements.txt
```

## Iniciar la Base de Datos

```
./start_db.sh
```

### Llenar la base de datos

```
./load_data.sh
```

## Iniciar app

```
python manage.py runserver
```

## Usuarios de prueba

### Usuario organizador
- Usuario: admin
- Contraseña: p

### Usuario no organizador
- Usuario: matias.rios
- Contraseña: p
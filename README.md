# Eventhub

Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP

## Integrantes
- Alvite Damián 32422
- Capre Rodrigo 31877
- Elizalde Benjamín 32030
- Canu Santiago 31626

## Dependencias

- python 3
- Django
- sqlite
- playwright
- ruff

## Instalar dependencias

`pip install -r requirements.txt`

## Iniciar la Base de Datos

`python manage.py migrate`

### Crear usuario admin

`python manage.py createsuperuser`

### Llenar la base de datos

`python manage.py loaddata fixtures/events.json`
`python manage.py loaddata fixtures/notification_priorities.json`

## Iniciar app

`python manage.py runserver`

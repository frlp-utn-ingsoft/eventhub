# Eventhub

Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP

## Integrantes del grupo:

- Ransan, Magali
- Capra, Valentina
- Kalpin, Sofia
- Lopez, Martina
- Gardiner, Ariadna

## Aclaraciones
 Antes de comenzar la app, desinstalar la dependencia django-fernet-fields con `pip uninstall uninstall django-fernet-fields`

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

## Iniciar app

`python manage.py runserver`

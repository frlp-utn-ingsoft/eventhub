# Eventhub

Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP

## Integrantes del grupo:

- Ransan, Magali
- Capra, Valentina
- Kalpin, Sofia
- Lopez, Martina
- Gardiner, Ariadna

## Aclaraciones
 1. volver a instalar dependencias con `pip install -r requirements.txt` ya que se instalaron:
    - qrcode para la utilización de qr en los tickets
    - fernet-fields para encriptación de datos

 2. En el caso de que la última dependencia no funcione, recomendamos instalar un entorno virtual:
    Procedimiento:
    2.1: En la raíz del proyecto, escribir este comando: 'python -m venv venv'
    2.2: Activar el entorno virtual: 'venv\Scripts\activate'
    2.3: Instalar las dependencias dentro del venv con `pip install -r requirements.txt`
    2.4: Ejecutar el siguiente script: 'python postinstall.py'. Este último fue de ayuda ya que tuvimos inconvenientes de compatibilidad entre dependencias

3. Iniciar la app

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

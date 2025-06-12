# Eventhub

Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP Grupo 5

## Participantes

Franco Beneforti

Lucas Diez

Emilio Bordignon 

Lucas Cambas Sanchez

Gabriela Otero

Tomas Coch

## Dependencias

-   Para ver las dependencias, entre al archivo requirements-dev.txt y el archivo requirements.txt

## Instalar dependencias

`pip install -r requirements-dev.txt`

## Iniciar la Base de Datos

`python manage.py migrate`

### Crear usuario admin

`python manage.py createsuperuser`

### Llenar la base de datos

`python manage.py loaddata fixtures/events.json`

## Iniciar app

`python manage.py runserver`


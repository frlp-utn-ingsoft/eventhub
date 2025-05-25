# Eventhub

Aplicación web para venta de entradas utilizada en la cursada 2025 de Ingeniería y Calidad de Software. UTN-FRLP

## Integrantes

- Valentín Augusto Garzaniti
- Romeo Lorenzo Monfroglio
- Gonzalo Martín Perez
- Manuel Rebol
- Facundo Serra
- Federico Nahuel Valle



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
rm app/migrations/0*.py
```
```
python manage.py makemigrations app
```
```
python manage.py migrate
```
```
python manage.py migrate
```

### Crear usuario admin

```
python manage.py createsuperuser
```

### Llenar la base de datos

```
python manage.py loaddata fixtures/events.json
```

## Iniciar app

```
python manage.py runserver
```

## Correr tests
#### Todos los tests
```
python manage.py test app.test
```
#### Tests unitarios
```
python manage.py test app.test.test_unit
```
#### Tests de integracion
```
python manage.py test app.test.test_integration
```
#### Tests e2e
```
python manage.py test app.test.test_e2e
```

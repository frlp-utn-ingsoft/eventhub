# Usamos una imagen base de Python oficial con versión específica (más ligera)
FROM python:3.12-slim as builder

# Creamos y establecemos el directorio de trabajo
WORKDIR /app

# Copiar solo requirements primero (para cachear dependencias)
COPY requirements.txt .

# Instalamos dependencias del sistema necesarias
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos solo el archivo de requerimientos primero para aprovechar la caché de Docker
COPY . .

# Puerto que expondrá el contenedor (el mismo que usa Django por defecto)
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
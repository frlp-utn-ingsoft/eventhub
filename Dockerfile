# Usamos una imagen base de Python oficial con versión específica (más ligera)
FROM python:3.10-slim-buster as builder

# Establecemos variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Creamos y establecemos el directorio de trabajo
WORKDIR /app

# Instalamos dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos solo el archivo de requerimientos primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalamos dependencias de Python
RUN pip install --user -r requirements.txt

# --- Fase final con imagen más ligera ---
FROM python:3.10-slim-buster

# Copiamos solo las dependencias instaladas desde la fase builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Asegurarnos que los scripts en .local son ejecutables
ENV PATH=/root/.local/bin:$PATH

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos el resto del proyecto
COPY . .

# Puerto que expondrá el contenedor (el mismo que usa Django por defecto)
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "eventhub.wsgi:application"]
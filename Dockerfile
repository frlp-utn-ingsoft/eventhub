# --------------------------------------
# ETAPA 1: Constructor (builder)
# --------------------------------------
FROM python:3.11-slim AS builder

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar herramientas necesarias para compilar dependencias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*




# Instalar dependencias de Python en formato wheel
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# --------------------------------------
# ETAPA 2: Producción
# --------------------------------------
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=eventhub.settings

WORKDIR /app

# Instalar dependencias desde la etapa anterior
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /root/.cache/pip

COPY ./entrypoint.sh /app/entrypoint.sh

# Copiar el proyecto completo
COPY . .


EXPOSE 8000

# Comando para iniciar Gunicorn
CMD sh -c "gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 eventhub.wsgi"
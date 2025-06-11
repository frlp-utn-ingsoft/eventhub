### Construcción y ejecución de tu aplicación
Cuando estés listo, inicia tu aplicación ejecutando:
`docker compose up --build.`

Tu aplicación estará disponible en http://localhost:8000.

Otra opción es construyendo una imagen a partir del Dockerfile mediante el comando:
`docker build -t eventhub:latest .`
_siendo `.` el directorio en donde se encuentra el Dockerfile_

Posterior a eso construimos el contenedor ejecutando:
`docker run --name eventhub -p 8000:8000 -d eventhub:latest`

### Referencias
* [Guía de Docker para Python](https://docs.docker.com/language/python/)
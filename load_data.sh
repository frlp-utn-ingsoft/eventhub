#!/bin/bash

python_interpreter="python"
#python_interpreter="python3"

echo "==> Cargando datos de prueba desde..."
$python_interpreter manage.py loaddata "./fixtures/venues.json" && \
$python_interpreter manage.py loaddata "./fixtures/categories.json" && \
$python_interpreter manage.py loaddata "./fixtures/users.json" && \
$python_interpreter manage.py loaddata "./fixtures/events.json" && \
$python_interpreter manage.py loaddata "./fixtures/tickets.json" && \
$python_interpreter manage.py loaddata "./fixtures/comments.json" && \
$python_interpreter manage.py loaddata "./fixtures/notifications.json" && \
$python_interpreter manage.py loaddata "./fixtures/refounds_request.json" && \
$python_interpreter manage.py loaddata "./fixtures/rating.json" && \
$python_interpreter manage.py loaddata "./fixtures/notifications.json"
#!/bin/sh

# espera que el servicio (por ejemplo db:5432) esté listo
host="$1"
shift
port="$1"
shift

until nc -z $host $port; do
  echo "Esperando a $host:$port..."
  sleep 1
done

exec "$@"

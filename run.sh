#!/bin/sh
# Abre el tunel nativo con el iPhone (sin root, por wifi) y levanta el joystick
# en http://127.0.0.1:8765
#
# El UDID sale de .env (POGO_UDID). Solo hace falta si tienes mas de un
# dispositivo Apple en la red.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DIR/.env" ] && . "$DIR/.env"

PY="$HOME/.local/share/uv/tools/pymobiledevice3/bin/python"
[ -x "$PY" ] || PY=python3

exec "$PY" "$DIR/spoof.py" ${POGO_UDID:+--udid "$POGO_UDID"} "$@"

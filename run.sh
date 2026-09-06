#!/bin/sh
# Levanta el joystick en http://127.0.0.1:8765 contra el emulador de Android.
#
#   ./run.sh                  el unico emulador que vea adb
#   ./run.sh emulator-5554    uno concreto, si tienes varios
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DIR/.env" ] && . "$DIR/.env"

# Si el python del sistema ya tiene las dos dependencias, tira con el. Si no,
# uv se las baja al vuelo y no hay que instalar nada a mano.
if python3 -c 'import starlette, uvicorn' 2>/dev/null; then
  exec python3 "$DIR/spoof.py" "$@"
fi
if command -v uv >/dev/null 2>&1; then
  exec uv run --with starlette --with uvicorn python "$DIR/spoof.py" "$@"
fi
echo "Falta starlette y uvicorn. Instala uv (https://docs.astral.sh/uv/) o:" >&2
echo "  python3 -m pip install starlette uvicorn" >&2
exit 1

#!/bin/sh
# Todo de una: emulador, joystick y navegador. Se puede lanzar las veces que
# quieras, lo que ya esta arrancado no se toca.
#
# Para tenerlo como comando (una vez):
#   ln -sf "$PWD/pogo" ~/.local/bin/pogo
set -e
DIR="$(dirname "$(realpath "$0")")"
URL=http://127.0.0.1:8765
LOG="${TMPDIR:-/tmp}"; LOG="${LOG%/}/pogo-spoof.log"

vivo() { curl -sf -o /dev/null -m 2 "$URL/pos"; }

# Primero el emulador, y esperando a que acabe: la web al abrirse le manda la
# posicion, y si aun no ha arrancado se pierde.
"$DIR/emulator.sh" start

if vivo; then
  echo "[pogo] joystick ya en marcha"
else
  serial="$("$DIR/emulator.sh" status | sed -n 's/^serial=//p')"
  # nohup: el joystick sigue vivo aunque cierres esta terminal. Sin buffer, para
  # que el log diga lo que pasa cuando pasa y no al cerrar.
  PYTHONUNBUFFERED=1 nohup "$DIR/run.sh" $serial > "$LOG" 2>&1 &
  pid=$!
  i=0
  until vivo; do
    # Si se ha caido (puerto ocupado, falta una dependencia) no tiene sentido
    # esperar el minuto entero: se dice por que y fuera.
    kill -0 "$pid" 2>/dev/null || { echo "[pogo] el joystick no arranco:" >&2; tail -5 "$LOG" >&2; exit 1; }
    i=$((i + 1))
    [ $i -lt 60 ] || { echo "[pogo] el joystick no contesta. Mira $LOG" >&2; exit 1; }
    sleep 1
  done
  echo "[pogo] joystick en $URL (log en $LOG)"
fi

open "$URL"

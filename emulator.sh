#!/bin/sh
# Arranca el emulador de Android con la unica configuracion en la que Pokemon GO
# es jugable: OpenGL ES 3.1 (si no, no se dibuja el avatar) y ANGLE apuntado a
# kosmickrisp (si no, va a 8 FPS en vez de 30).
#
# Todo lo que aqui se toca vive FUERA del repo: dentro del SDK y en ~/.android.
# Por eso existe este fichero, para no volver a averiguarlo. El porque de cada
# linea esta en el README, seccion "Registro de intentos".
#
#   ./emulator.sh start     arranca y deja el emulador listo (idempotente)
#   ./emulator.sh setup     solo aplica los parches, sin arrancar
#   ./emulator.sh status    imprime clave=valor
#   ./emulator.sh stop      apaga el emulador
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DIR/.env" ] && . "$DIR/.env"

SDK="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
AVD="${POGO_AVD:-Medium_Phone_2}"
AVD_HOME="${ANDROID_AVD_HOME:-$HOME/.android/avd}"
EMU="$SDK/emulator/emulator"
ADB="$SDK/platform-tools/adb"
ANGLE_ICD="$SDK/emulator/lib64/gles_angle/vk_swiftshader_icd.json"
KOSMICKRISP="$SDK/emulator/lib64/vulkan/libvulkan_kosmickrisp.dylib"
FEATURES="$HOME/.android/advancedFeatures.ini"

# La resolucion nativa (1080x2400) no da mas FPS y se come el render. 720x1600 a
# 280 dpi es el punto en el que dejo de ganar nada bajando mas.
WIDTH=720
HEIGHT=1600
DENSITY=280
SYSIMAGE="system-images;android-37.1;google_apis_playstore_ps16k;arm64-v8a"

say() { echo "[emulator] $*" >&2; }
die() { echo "[emulator] $*" >&2; exit 1; }

# --- parches fuera del repo -------------------------------------------------

# ANGLE carga su driver Vulkan de este json. De fabrica apunta a SwiftShader, que
# es un rasterizador por software: la GPU del Mac no pinta nada y el juego va a
# 8 FPS. kosmickrisp es Vulkan 1.3 sobre Metal y lo sube a 30, el tope del juego.
# MoltenVK aqui NO vale: le faltan extensiones y revienta el emulador al arrancar.
patch_icd() {
  [ -f "$KOSMICKRISP" ] || die "falta kosmickrisp en $KOSMICKRISP (actualiza el emulador del SDK)"
  if grep -q kosmickrisp "$ANGLE_ICD" 2>/dev/null; then
    say "ICD ya apunta a kosmickrisp"
    return
  fi
  [ -f "$ANGLE_ICD.orig" ] || cp "$ANGLE_ICD" "$ANGLE_ICD.orig"
  printf '{"file_format_version": "1.0.0", "ICD": {"library_path": "%s", "api_version": "1.3.0"}}\n' \
    "$KOSMICKRISP" > "$ANGLE_ICD"
  say "ICD de ANGLE apuntado a kosmickrisp (copia en $ANGLE_ICD.orig)"
}

unpatch_icd() {
  [ -f "$ANGLE_ICD.orig" ] || die "no hay copia original que restaurar"
  cp "$ANGLE_ICD.orig" "$ANGLE_ICD"
  say "ICD restaurado a SwiftShader"
}

# GuestAngle tiene que quedar APAGADO: da ES 3.1 pero Unity lo rechaza con
# "Unable to initialize the Unity Engine Graphics API", con cualquier driver.
write_features() {
  printf 'Vulkan = on\nGLDirectMem = on\n' > "$FEATURES"
  say "advancedFeatures.ini escrito (sin GuestAngle)"
}

# El AVD se puede borrar. Aqui esta su definicion, para recrearlo igual.
ensure_avd() {
  if [ -d "$AVD_HOME/$AVD.avd" ]; then
    say "AVD $AVD ya existe"
    return
  fi
  [ -d "$DIR/avd" ] || die "no encuentro $DIR/avd con la definicion del AVD"
  if ! "$SDK/cmdline-tools/latest/bin/sdkmanager" --list_installed 2>/dev/null | grep -q "google_apis_playstore_ps16k"; then
    die "falta la imagen de sistema. Instalala primero:
  $SDK/cmdline-tools/latest/bin/sdkmanager \"$SYSIMAGE\""
  fi
  say "recreando AVD $AVD desde $DIR/avd"
  mkdir -p "$AVD_HOME/$AVD.avd"
  sed "s|@AVD_HOME@|$AVD_HOME|g; s|@AVD@|$AVD|g" "$DIR/avd/avd.ini" > "$AVD_HOME/$AVD.ini"
  cp "$DIR/avd/config.ini" "$AVD_HOME/$AVD.avd/config.ini"
  say "AVD creado. El primer arranque tarda, tiene que formatear /data"
}

setup() {
  patch_icd
  write_features
  ensure_avd
}

# --- arranque ---------------------------------------------------------------

pids() { pgrep -f "qemu-system-aarch64.*$AVD" 2>/dev/null || true; }

serial() {
  "$ADB" devices | awk '/^emulator-/ {print $1; exit}'
}

booted() {
  s="$(serial)"
  [ -n "$s" ] || return 1
  [ "$("$ADB" -s "$s" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]
}

# El override de resolucion no sobrevive al reinicio, hay que ponerlo cada vez.
resize() {
  s="$(serial)"
  "$ADB" -s "$s" shell wm size "${WIDTH}x${HEIGHT}"
  "$ADB" -s "$s" shell wm density "$DENSITY"
  say "pantalla a ${WIDTH}x${HEIGHT} @ ${DENSITY}dpi"
}

start() {
  if booted; then
    say "el emulador ya esta arrancado"
    resize
    return
  fi
  [ -z "$(pids)" ] || die "hay un emulador a medio arrancar. Espera, o ./emulator.sh stop"
  setup
  say "arrancando $AVD con -gpu swangle"
  # nohup + setsid para que sobreviva a quien lance el script (la web, p.ej.)
  nohup "$EMU" -avd "$AVD" -gpu swangle -no-snapshot-load \
    > "${TMPDIR:-/tmp}/pogo-emulator.log" 2>&1 &

  i=0
  while [ $i -lt 90 ]; do
    if booted; then
      resize
      g="$("$ADB" -s "$(serial)" shell getprop ro.opengles.version | tr -d '\r')"
      [ "$g" = "196609" ] || say "AVISO: ro.opengles.version=$g, esperaba 196609 (ES 3.1). Sin ES 3.1 no se dibuja el avatar"
      say "listo"
      return
    fi
    sleep 2
    i=$((i + 1))
  done
  die "no arranco en 180s. Mira ${TMPDIR:-/tmp}/pogo-emulator.log"
}

stop() {
  s="$(serial)"
  [ -n "$s" ] && "$ADB" -s "$s" emu kill >/dev/null 2>&1 || true
  say "apagado"
}

status() {
  s="$(serial)"
  echo "avd=$AVD"
  echo "running=$([ -n "$(pids)" ] && echo yes || echo no)"
  echo "booted=$(booted && echo yes || echo no)"
  echo "serial=$s"
  if [ -n "$s" ]; then
    echo "gles=$("$ADB" -s "$s" shell getprop ro.opengles.version 2>/dev/null | tr -d '\r')"
    echo "size=$("$ADB" -s "$s" shell wm size 2>/dev/null | tr -d '\r' | awk -F': ' '/Override/{print $2} END{}')"
  fi
  echo "icd=$(grep -q kosmickrisp "$ANGLE_ICD" 2>/dev/null && echo kosmickrisp || echo swiftshader)"
}

case "${1:-start}" in
  start)   start ;;
  setup)   setup ;;
  status)  status ;;
  stop)    stop ;;
  unpatch) unpatch_icd ;;
  *) die "uso: $0 [start|setup|status|stop|unpatch]" ;;
esac

# pogo

Joystick GPS y rutas para iPhone. Levanta una web local en el Mac y controla la
ubicacion que reporta el movil: mando analogico, rutas que se recorren solas y
velocidad configurable.

Sin jailbreak, sin cable, sin app modificada. Va sobre el servicio de
desarrollador de iOS (DVT), el mismo que usa Xcode para simular ubicacion.

Probado en: macOS + iPhone XR con iOS 18.6.2, conectado por wifi.

## Aviso

Falsear la ubicacion viola los terminos de servicio de Niantic. El sistema de
sanciones es de tres avisos:

1. Aviso: 7 dias sin Pokemon raros ni EX raids (shadowban)
2. Suspension: 30 dias
3. Ban permanente

La deteccion es retroactiva. Usa una cuenta desechable de Pokemon Trainer Club,
nunca tu cuenta principal ni tu Google.

## Requisitos

- macOS. El tunel nativo sin root es exclusivo de macOS.
- Mac y iPhone en la misma red wifi.
- iPhone con iOS 17 o superior.
- Modo Desarrollador activo en el iPhone.
- El iPhone emparejado con este Mac alguna vez (vale un emparejamiento antiguo).
- [uv](https://docs.astral.sh/uv/) instalado.

## Instalacion (una sola vez)

### 1. Instalar pymobiledevice3

```sh
uv tool install pymobiledevice3
```

### 2. Activar Modo Desarrollador en el iPhone

Ajustes > Privacidad y seguridad > Modo Desarrollador > activar.
El movil se reinicia. Tras el reinicio confirma el dialogo.

Si no aparece la opcion, conecta el movil por cable a un Mac con Xcode una vez.
El menu aparece despues del primer emparejamiento.

### 3. Averiguar el UDID del movil

```sh
pymobiledevice3 remote browse | grep -E '"(udid|model|name)"'
```

Busca la linea con tu modelo. El iPhone XR es `iPhone11,8`.

### 4. Crear el fichero .env

```sh
echo 'POGO_UDID=00008020-XXXXXXXXXXXXXXXX' > .env
```

Esta en `.gitignore`, no se sube al repo. Solo hace falta si tienes mas de un
dispositivo Apple en la red; con uno solo, `run.sh` lo encuentra igual.

## Uso diario

```sh
./run.sh
```

Luego abre <http://127.0.0.1:8765>

Eso es todo. `run.sh` abre el tunel, monta la DeveloperDiskImage si hace falta y
levanta la web. Deja la terminal abierta: si cierras el proceso se cae el tunel.

### Antes de jugar, comprueba

1. iPhone desbloqueado y en la misma wifi que el Mac.
2. Abre Apple Maps en el movil: debe mostrarte donde diga la web, no donde estas.
3. Solo entonces abre Pokemon GO.

## Controles

| Accion | Como |
|---|---|
| Fijar posicion | Click en el mapa (con "Modo ruta" desactivado) |
| Mover | Arrastrar el circulo azul, o `WASD` / flechas |
| Velocidad | Slider, o los presets Andar / Rapido / Bici |
| Crear ruta | Marcar "Modo ruta" y hacer click en cada punto |
| Recorrer ruta | Boton "Recorrer" |
| Fin de ruta | Bucle, Ida y vuelta, o Parar |
| Volver al GPS real | Boton "Devolver GPS real" |

La ruta y la velocidad se guardan en el navegador. Siguen ahi al reabrir.

Manda una coordenada por segundo, como un GPS real, con +-3 metros de ruido para
que la traza no salga en linea geometrica perfecta.

## Reglas de Pokemon GO

### Velocidad

Por encima de **10.5 km/h** el juego deja de contar la distancia. Para incubar
huevos y el caramelo de compañero usa Andar (4.5) o Rapido (9). El preset Bici
(15) sirve para desplazarte, no para acumular kilometros.

### Cooldown

Tras un salto grande de ubicacion, NO hagas ninguna accion (capturar, girar
parada, dar bayas, soltar, abrir regalo) hasta que pase este tiempo:

| Distancia | Espera |
|---|---|
| 1 km | 30 s |
| 5 km | 2 min |
| 10 km | 6 min |
| 25 km | 11 min |
| 30 km | 14 min |
| 65 km | 22 min |
| 100 km | 35 min |
| 250 km | 45 min |
| 500 km | 60 min |
| 1000 km | 90 min |
| 1500 km o mas | 120 min |

Moverse y mirar el mapa no cuenta. Solo cuentan las acciones.

El joystick a velocidad de andar no dispara cooldown. Saltar de ciudad si.

### Higiene

- Cuenta PTC desechable, nunca la principal.
- No alternes ubicacion real y falsa el mismo dia. Al volver a tu sitio real,
  cooldown completo antes de tocar nada.
- Sin VPN a otro pais con GPS local, ni al reves: la incoherencia IP contra GPS
  es señal directa.
- Soft ban (los Pokemon huyen al primer intento, las paradas no dan items):
  gira la misma parada unas 40 veces seguidas, o espera el cooldown.

## Como funciona

- `spoof.py`: abre el tunel RemoteXPC con el movil usando el `remotepairingd` de
  macOS (sin root), monta la DeveloperDiskImage si no lo esta, y sirve una API
  local. `POST /loc` inyecta una coordenada via `LocationSimulation` de DVT.
- `index.html`: el mapa, el joystick y el recorrido de rutas. Toda la
  interpolacion de movimiento se calcula en el navegador; el servidor solo
  reenvia coordenadas al movil.

## Problemas

**`address already in use`**

Quedo un proceso vivo de una ejecucion anterior:

```sh
lsof -ti tcp:8765 | xargs kill
```

**`Device not found` o el tunel no levanta**

- iPhone desbloqueado y en la misma wifi.
- Comprueba que aparece: `pymobiledevice3 remote browse`
- Si no aparece, conectalo por cable una vez y acepta "Confiar en este
  ordenador".

**Errores de DVT o de servicio no encontrado**

Falta la DeveloperDiskImage. `run.sh` la monta sola, pero se puede forzar:

```sh
pymobiledevice3 remote start-tunnel --udid TU_UDID --script-mode
```

Con la direccion y puerto que imprime:

```sh
pymobiledevice3 mounter auto-mount --rsd DIRECCION PUERTO
```

La DDI se desmonta cada vez que reinicias el movil. `run.sh` la vuelve a montar.

**La ubicacion no vuelve a la real**

Boton "Devolver GPS real". Si no, reinicia el movil.

## Cambiar el puerto

```sh
./run.sh --port 9000
```

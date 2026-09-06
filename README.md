# pogo

Joystick GPS y rutas. Levanta una web local en el Mac y controla la ubicacion
que reporta el dispositivo: mando analogico, rutas que se recorren solas y
velocidad configurable. Sirve para un iPhone por wifi o para un emulador de
Android.

Sin jailbreak, sin cable, sin app modificada. Va sobre el servicio de
desarrollador de iOS (DVT), el mismo que usa Xcode para simular ubicacion.

Probado en: macOS + iPhone XR con iOS 18.6.2, conectado por wifi.

## Estado: Pokemon GO no funciona

Probado el 2026-09-06 en iPhone XR con iOS 18.6.2. Nada mas abrir el juego sale
"Failed to detect location (12)". La distancia da igual: falla tambien con la
coordenada puesta a 100 metros de la posicion real.

En iOS 17 en adelante el unico canal para inyectar posicion es
`com.apple.instruments.server.services.LocationSimulation`, el mismo que usa
Xcode en Debug > Simulate Location. CoreLocation marca esas posiciones con
`CLLocation.sourceInformation.isSimulatedBySoftware = true`. La marca la pone
`locationd`: no viaja en lo que mandamos nosotros y no se puede quitar desde el
Mac. Apple Maps no la consulta, por eso te sigue. Niantic si.

Saltarselo pide jailbreak o binario del juego modificado, las dos cosas fuera de
lo que hace este repo. El iPhone XR es A12, asi que checkm8 tampoco aplica.

El resto sigue funcionando: Apple Maps y cualquier app que no mire esa marca.
El detalle de lo probado esta en [Registro de intentos](#registro-de-intentos).

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

Contra un emulador de Android, con el emulador ya arrancado:

```sh
./run.sh --android
```

Con varios dispositivos en `adb devices`, pasa el serial: `./run.sh --android
emulator-5554`. No hace falta ni root ni app de mock location: `adb emu geo fix`
alimenta el GPS emulado, que para el sistema es el de verdad. La misma web y los
mismos controles.

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
| Fijar casa | Boton "Fijar casa aqui", con la posicion puesta en tu portal |
| Volver a casa | Boton "Ir a casa" |
| Volver al GPS real | Boton "Devolver GPS real" |

La ruta y la velocidad se guardan en el navegador. Siguen ahi al reabrir.

Manda una coordenada por segundo, como un GPS real, con +-3 metros de ruido para
que la traza no salga en linea geometrica perfecta.

## Punto de partida (casa)

Fija tu ubicacion real como punto de partida. Al abrir la web el movil arranca
siempre ahi, no en donde lo dejaste la ultima vez. Asi no hay saltos entre
sesiones.

Una sola vez:

1. Busca tu portal en el mapa y haz zoom.
2. Haz click encima, con "Modo ruta" desactivado.
3. Pulsa "Fijar casa aqui".

Se guarda en el `localStorage` del navegador. **No se guarda en el repo ni se
manda a ningun servidor**: tu direccion no sale de tu Mac. Si borras los datos
del navegador hay que volver a fijarla.

El boton "Ir a casa" te devuelve ahi de golpe. Si venias de una ubicacion
lejana, ese salto tambien tiene cooldown antes de poder hacer acciones.

## Reglas de Pokemon GO

> Hoy el juego no arranca con la ubicacion simulada, ver
> [Estado](#estado-pokemon-go-no-funciona). Lo de abajo queda como referencia
> por si algun dia vuelve a valer.

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

## Registro de intentos

Lo probado y como acabo, para no repetir callejones sin salida entre sesiones.

### 2026-09-06

**Entorno verificado.** pymobiledevice3 11.5.0, uvicorn 0.52.4, starlette 1.6.0.
Todas las APIs que usa `spoof.py` existen con la firma esperada. El tunel nativo
y `POST /loc` funcionan contra el iPhone XR (`iPhone11,8`) y contra el iPhone 16
Pro (`iPhone17,1`). El backend no falla en nada.

**Descartado: el Modo Desarrollador y la DeveloperDiskImage.** Con el tunel
abierto y la DDI montada, pero sin inyectar ninguna coordenada, Pokemon GO entra
sin error. Lo que detecta es la coordenada, no el entorno de desarrollo.

**Descartado: incoherencia entre GPS e IP u operadora.** Coordenada puesta a unos
100 metros de la posicion real, misma wifi y misma cobertura: error 12 igual, al
instante. No es un control de distancia ni de coherencia con la red.

**Descartado: el servicio antiguo `com.apple.dt.simulatelocation`.** Es un canal
lockdown distinto al de Instruments, y ademas la posicion aguanta con la sesion
cerrada, asi que valia la pena mirarlo. Apple lo quito en iOS 17:

```
pymobiledevice3.exceptions.InvalidServiceError: No such service: com.apple.dt.simulatelocation
```

Se probo con un flag `--service dt` en `spoof.py`, revertido despues para no
dejar codigo muerto.

**Descartado sin escribir codigo: una app de iOS propia que haga de joystick.**
No sirve. El sandbox de iOS no deja que una app inyecte ubicacion en otra, no
existe el equivalente al mock location provider de Android. La marca la pone
`locationd` para todo el sistema mientras la simulacion esta activa, asi que una
app propia leeria la posicion igual de marcada. Lo unico que aportaria es
diagnostico: leer `CLLocation.sourceInformation.isSimulatedBySoftware` y medir lo
que aqui esta deducido por descarte. No abre ninguna via nueva.

**Descartado: `com.apple.coredevice.locationservice`.** Enumerando los 60
servicios que publica el movil por RSD, es el unico canal de ubicacion aparte del
de Instruments. Responde bien, pero devuelve los escenarios de siempre:

```
{"scenarios": [{"name": "City Run"}, {"name": "City Bicycle Ride"},
               {"name": "Apple"}, {"name": "Freeway Drive"}]}
```

Son los presets de Debug > Simulate Location de Xcode. Es el mismo feature con
otro transporte, CoreDevice en vez de DTX, asi que la posicion sale marcada
igual. `devicectl` de Xcode ni siquiera expone el subcomando. No hay un tercer
canal de ubicacion en iOS.

**Android, emulador: funciona.** Backend nuevo en `spoof.py`, opcion `--android`,
que sustituye la inyeccion de pymobiledevice3 por `adb emu geo fix`. La web, las
rutas, el joystick y la persistencia se reutilizan tal cual. Comprobado sirviendo
37.8859, -4.7658 desde la web y leyendo el sistema:

```
last location=Location[gps 37.885898,-4.765798 hAcc=5.0 ...]
last location=Location[fused 37.885898,-4.765798 ...]
```

Proveedor `gps` y `fused`, sin marca de mock, porque no es un mock provider: es el
GPS emulado. El movimiento tambien cuadra: 10 pasos de 10 metros al norte dejan
la latitud en 37.885897 partiendo de 37.884998, o sea 100.07 metros, con la
longitud intacta. Ojo, `adb emu geo fix` pide **longitud primero**, hay un test en
`test_spoof.py` para eso.

Esto no sirve para jugar: Pokemon GO no arranca en un emulador, lo tumba Play
Integrity. El emulador es el banco de pruebas. Para jugar haria falta movil
Android real, y ahi la inyeccion por `adb` marca la posicion con `isMock`, que es
justo lo que Niantic mira. Sin root, mismo muro que en iOS.

**Conclusion.** iOS cerrado. Los dos unicos canales de ubicacion del sistema son
el mismo feature de Xcode, y ese feature va marcado. Lo que queda esta todo fuera
de lo que hace este repo:

- Jailbreak: no hay para el iPhone XR con iOS 18.6.2. El XR es A12 y checkm8
  llega hasta A11. TrollStore pide iOS 17.0 o anterior.
- Binario del juego modificado o metido en un contenedor con hooks: rompe la
  premisa de "sin app modificada" y es terreno de copyright.
- Emitir señal GPS falsa con un SDR: transmitir en las bandas GNSS es ilegal y
  afecta a cualquiera que este cerca. Descartado de plano.

La unica via viva es portarlo a Android con root y ocultacion de mock location,
que es otro proyecto y donde la deteccion tambien pelea.

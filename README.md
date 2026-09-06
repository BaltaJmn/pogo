# pogo

Joystick GPS y rutas. Levanta una web local en el Mac y controla la ubicacion
que reporta el dispositivo: mando analogico, rutas que se recorren solas y
velocidad configurable. Sirve para un iPhone por wifi o para un emulador de
Android.

Sin jailbreak, sin cable, sin app modificada. Va sobre el servicio de
desarrollador de iOS (DVT), el mismo que usa Xcode para simular ubicacion.

Probado en: macOS + iPhone XR con iOS 18.6.2, conectado por wifi.

## Estado: en iPhone no, en emulador de Android si

Pokemon GO **funciona con el emulador de Android**: arranca, carga el mapa, y
anda con el joystick. Ver [Uso diario](#uso-diario), opcion `--android`.

En iPhone no hay nada que hacer, y el resto de esta seccion explica por que.

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

> Esto aplica jugando desde el emulador de Android, que es donde funciona. Desde
> iPhone da igual, el juego ni arranca, ver
> [Estado](#estado-en-iphone-no-en-emulador-de-android-si).

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
  local. Tambien lleva el movimiento: un bucle propio avanza la posicion e
  inyecta un fix por segundo, la cadencia de un GPS real. En iPhone via
  `LocationSimulation` de DVT, en emulador via `adb emu geo fix`.
- `index.html`: el mapa, el joystick y el editor de rutas. Solo manda la
  intencion con `POST /loc` (`vx`, `vy`, `kmh`, `route`, `walking`...) y sondea
  `GET /pos` para pintar. No calcula movimiento.

El bucle esta en el servidor a proposito. Chrome estrangula los temporizadores de
una pestaña oculta, y para mirar el juego tienes que tapar el navegador. Asi
sigues andando aunque cierres la pestaña.

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

**Android, emulador: Pokemon GO tambien funciona.** Predije que Play Integrity lo
tumbaria y me equivoque. En un emulador arm64 de Android Studio sobre Apple
Silicon (`sdk_gphone16k_arm64`) el juego arranca, entra en la cuenta, carga el
mapa con paradas y gimnasios, y responde al joystick: andando 50 metros a paso
humano salto un encuentro salvaje. Ningun error 12.

El motivo es el de siempre, visto del derecho: `adb emu geo fix` no es un mock
provider, alimenta el GPS emulado. El sistema sirve esa posicion como una
normal, sin `isMock` y sin nada equivalente a `isSimulatedBySoftware`. No hay
marca que detectar.

En movil Android real sin root la cosa cambia: ahi la inyeccion por `adb` va por
test provider y si marca `isMock`, que es justo lo que Niantic lee. El emulador
se libra por no tener GPS de verdad.

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

### 2026-09-06, tarde: el juego no sigue la posicion en vivo

Sintoma: al mover el joystick en la web el avatar no se mueve. Al cerrar y
reabrir Pokemon GO aparece en la posicion nueva. O sea, la posicion llega, pero
el juego solo la lee al arrancar.

**El canal funciona.** Un solo `adb emu geo fix -4.7630000 37.8858350` aterriza
exacto y al instante:

```
last location=Location[gps 37.885835,-4.762998 hAcc=5.0 et=+28m30s490ms ...]
```

**El GPS emulado emite a 1 Hz, no mas.** Empujando 8 posiciones seguidas en
metodo bucle rapido, el proveedor `gps` solo tomo una: `et` avanzo un segundo
justo. No es un fallo, es la cadencia del HAL. Empujar mas rapido no sirve de
nada.

**El proveedor `fused` va con retraso.** Con `gps` en -4.762957, `fused` marcaba
-4.762991, unos 3 metros por detras, y con `vel` casi cero. Google Play Services
suaviza los saltos. Pokemon GO esta registrado en los dos:

```
gps provider:
  10229/com.nianticlabs.pokemongo/092601A3 Request[@+1s0ms HIGH_ACCURACY, ...]
fused provider:
  10229/com.nianticlabs.pokemongo/38855783 Request[@+1s0ms BALANCED, ...]
```

Pide 1 Hz en ambos, asi que las actualizaciones le estan llegando.

**El bucle de movimiento vive en el navegador y se estrangula.** Midiendo `/pos`
mientras la pestaña estaba oculta: 12 lecturas seguidas, una sola coordenada. Con
la pestaña despierta avanza a 1.25 m/s clavados. Chrome baja el temporizador de
las pestañas de fondo, y para mirar el juego hay que tapar el navegador. Esto
contamina cualquier medida y ademas rompe el uso normal.

**El juego si sigue la posicion en vivo.** Paseo de 150 s al este a 4.5 km/h
inyectando por `adb` directamente, sin navegador de por medio, con capturas del
emulador antes, a mitad y al final. El mapa avanza, cargan paradas nuevas y
salen encuentros salvajes (Clefairy, Nidoran, Pikachu). Al abrir el perfil salto
una eclosion de huevo, que solo pasa acumulando kilometros andando. Niantic
cuenta el recorrido.

**El avatar no se dibuja, y eso es otra cosa.** El circulo morado de alcance esta
en su sitio y los Pokemon se renderizan bien, pero el muñeco del jugador no
aparece. El emulador se queda en OpenGL ES 3.0:

```
GLES: Google (Apple), Android Emulator OpenGL ES Translator (Apple M2 Pro),
      OpenGL ES 3.0 (4.1 Metal - 90.5)
ANDROID_EMU_gles_max_version_3_0
```

Es cosmetico y no toca a la ubicacion. La prueba es que sin avatar visible el
juego sigue contando kilometros y eclosionando huevos.

**Arreglado: el bucle de movimiento se muda a `spoof.py`.** La causa real de
"muevo el joystick y no pasa nada". Ahora `index.html` solo manda la intencion
(`vx`, `vy`, `kmh`, `route`, `walking`, `endmode`, `jitter`) por `POST /loc` y
sondea `GET /pos` para pintar. El servidor avanza la posicion e inyecta un fix
por segundo. Andas aunque tapes o cierres el navegador. Comprobado sin navegador
ninguno:

```
t=0   {"lat":37.885835,"lon":-4.765513,"dist":0.0}
t=10  {"lat":37.885835,"lon":-4.765370,"dist":12.5}
      movil: Location[gps 37.885843,-4.765387 hAcc=5.0]
t=20  {"lat":37.885835,"lon":-4.765242,"dist":23.75}
      movil: Location[gps 37.885835,-4.765248 hAcc=5.0]
```

12.5 metros en 10 segundos son los 4.5 km/h pedidos, y el desfase de metros con
el movil es el ruido GPS de +-3 m. `test_spoof.py` cubre el motor: velocidad,
medio gas, zona muerta, bucle, ida y vuelta, modo parar y ruta con puntos
repetidos.

### 2026-09-06, tarde 2: la camara no sigue y el avatar no se dibuja

Dos sintomas que resultan ser el mismo problema. Registro de lo probado.

**Descartado: no es la entrega del sistema.** Google Maps si sigue en vivo.
Punto azul quieto en el centro de pantalla y el mapa desplazandose debajo: 72
metros al este en 60 segundos, medido comparando etiquetas entre las dos
capturas (Carrefour de x=560 a x=525, PARQUE FIDIANA de 458 a 420). Andando a
4.5 km/h, exactamente lo pedido. El GPS emulado entrega bien a 1 Hz.

**Descartado: no es falta de datos en el fix.** `adb emu geo fix` acepta mas
parametros de los que mandabamos:

```
geo fix <longitude> <latitude> [<altitude> [<satellites> [<velocity>]]]
```

Probado a mano, 90 fixes de un segundo con altitud, 12 satelites y 2.43 nudos:

```
Location[gps 37.878998,-4.778118 hAcc=5.0 alt=100.0 vel=1.250099 bear=0.0
         {Bundle[{satellites=0, maxCn0=0, meanCn0=0}]}]
```

La altitud y la velocidad llegan (2.43 nudos son 1.25 m/s, la velocidad de
andar). El contador de satelites lo ignora el emulador y `bear` sigue a 0 en el
proveedor `gps`, aunque el `fused` se calcula el rumbo solo. Con todo eso, tras
112 metros el juego seguia con los mismos pokestops en los mismos pixeles. La
hipotesis del fix incompleto era falsa.

**Confirmado: el cliente si acepta saltos grandes.** Teletransporte de 2 km con
la app en primer plano: a los 20 segundos el mapa esta en el sitio nuevo, con su
buddy y su circulo de interaccion. O sea, el juego escucha las actualizaciones
mientras corre. Lo que ignora es el movimiento a escala de paseo: 75 metros en
60 segundos dan una captura identica pixel a pixel salvo el temporizador de la
incursion.

**La pista buena: el avatar no existe.** El buddy (un Kirlia) se dibuja solo en
mitad del cesped, sin muñeco ni sombra al lado. Y el circulo de interaccion se
queda clavado en el mismo punto de pantalla. En Pokemon GO la camara sigue al
avatar; si el avatar no llega a instanciarse, la camara no tiene a quien seguir,
y solo se recoloca cuando algo fuerza un recentrado completo, que es justo lo que
hacen el arranque de la app y el salto de 2 km. Un unico fallo explica los dos
sintomas.

Queda por atribuir por que no se instancia. El emulador esta capado a
`OpenGL ES 3.0 (4.1 Metal - 90.5)` con `ANDROID_EMU_gles_max_version_3_0`, y el
avatar nuevo de Niantic es bastante mas pesado que el resto del mapa.

### 2026-09-06, tarde 3: la causa raiz es OpenGL, no el GPS

El log del propio juego, filtrando por su PID:

```
E GFXSTREAM: [egl.cpp(1800)] EGL_BAD_CONFIG: no ES 3.2 support
E GFXSTREAM: [egl.cpp(1794)] EGL_BAD_CONFIG: no ES 3.1 support
E GFXSTREAM: [egl.cpp(1220)] error 0x3004 (EGL_BAD_ATTRIBUTE)
```

Pokemon GO pide un contexto OpenGL ES 3.2, luego 3.1, y el emulador le niega los
dos. Cae a 3.0. Por eso no se dibuja el avatar y por eso la barra de objetos sale
con siluetas negras en vez de iconos de pokemon. Nada que ver con la ubicacion.

Por que esta capado:

```
GLES: Google (Apple), Android Emulator OpenGL ES Translator (Apple M2 Pro),
      OpenGL ES 3.0 (4.1 Metal - 90.5)
```

El traductor GL del emulador se apoya en el OpenGL del host. macOS lo deja en
4.1, y ES 3.1 necesita 4.3. Camino muerto. Lo dice hasta el fichero de features
del propio emulador, en `emulator/lib/advancedFeatures.ini`:

> For example, OS X is not known to support GLES 3.1.

**Intento: ANGLE sobre Vulkan.** La imagen si trae ANGLE
(`/system/lib64/libEGL_angle.so`) y el HAL de Vulkan (`vulkan.ranchu.so`), pero
la feature `Vulkan` viene apagada de fabrica. Activada en
`~/.android/advancedFeatures.ini`:

```
Vulkan = on
GLDirectMem = on
```

y el emulador relanzado fuera de Android Studio:

```
~/Library/Android/sdk/emulator/emulator -avd Medium_Phone_2 \
  -feature Vulkan,GLDirectMem -gpu host
```

Con ANGLE forzado solo para el juego (`settings put global
angle_gl_driver_selection_pkgs com.nianticlabs.pokemongo`), ANGLE arranca de
verdad y desaparecen los `EGL_BAD_CONFIG`:

```
I ANGLE: Version (2.1 ...), Renderer (Vulkan 1.3.0 (Goldfish GFXStream (Apple M2 Pro)))
```

Pero el juego no llega al mapa. Primero un aviso de Unity, `Your device does not
match the hardware requirements of this application`, y tras darle a Continue:

```
Error
Unable to initialize the Unity Engine Graphics API.
```

Asi que ANGLE queda descartado: el Unity de Pokemon GO no arranca contra el.
Ajuste revuelto con `settings delete`. La feature `Vulkan` se queda puesta,
porque ahora que el HAL responde, Unity puede elegir Vulkan el solo, que es la
via que queda por probar.

Para deshacerlo todo: borrar `~/.android/advancedFeatures.ini` y reiniciar el
emulador.

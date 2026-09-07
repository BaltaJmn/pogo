# pogo

Joystick GPS para Pokemon GO en un emulador de Android. Levanta una web local
en el Mac y controla la ubicacion que reporta el emulador: mando analogico,
rutas que se recorren solas, lugares guardados y velocidad configurable.

Sin root, sin app de mock location y sin tocar el juego. La posicion entra por
`adb emu geo fix`, que alimenta el GPS emulado: para ese Android es el unico GPS
que existe, asi que no hay ninguna marca que delate nada.

Probado en macOS sobre Apple M2 Pro contra un AVD arm64 con Google Play.

> Hubo una via para iPhone por wifi y se quito: el juego la detecta siempre.
> Esta archivada en [docs/ios.md](docs/ios.md) por si se retoma.

## Estado

Pokemon GO **funciona con el emulador de Android**: arranca, carga el mapa, anda
con el joystick, y el avatar y la camara siguen al personaje en vivo. Ver
[Uso diario](#uso-diario).

Con dos condiciones. La primera: el emulador tiene que arrancarse con
**`-gpu swangle`**. Con el modo de GPU por defecto de Android Studio el juego
funciona y cuenta kilometros, pero el avatar no se dibuja y la camara no sigue.

La segunda: hay que apuntar el ICD de Vulkan de ANGLE a **kosmickrisp**, si no
el juego va a 8 FPS. Con el parche va a 30, que es el tope del propio juego.

Las dos las aplica `./emulator.sh start`, o el boton "Arrancar emulador" de la
web. Ver [El emulador](#el-emulador), y el porque en
[Registro de intentos](#registro-de-intentos).

A 720x1600 el juego va a 30 FPS, que es su propio tope.

## Aviso

Falsear la ubicacion viola los terminos de servicio de Niantic. El sistema de
sanciones es de tres avisos:

1. Aviso: 7 dias sin Pokemon raros ni EX raids (shadowban)
2. Suspension: 30 dias
3. Ban permanente

La deteccion es retroactiva. Usa una cuenta desechable de Pokemon Trainer Club,
nunca tu cuenta principal ni tu Google.

## Empezar de cero

Guia completa en un Mac limpio. Si ya tienes Android Studio con un emulador,
salta al paso 4.

### Lo que hace falta

- **Un Mac con Apple Silicon** (M1 o posterior). La imagen del emulador es arm64
  y en un Mac Intel no arranca.
- **Unos 20 GB libres.** El SDK y la imagen del sistema ocupan lo suyo.
- **Una cuenta desechable de Pokemon Trainer Club.** Nunca la principal, ver
  [Aviso](#aviso).

### 1. Android Studio

Bajalo de <https://developer.android.com/studio>, arrastralo a Aplicaciones y
abrelo. El asistente de la primera vez descarga el SDK, dale a todo que si.

Al terminar, comprueba que el SDK esta donde toca:

```sh
ls ~/Library/Android/sdk/platform-tools/adb ~/Library/Android/sdk/emulator/emulator
```

Si eso imprime las dos rutas, vas bien. Si dice "No such file or directory",
abre Android Studio y ve a **Settings > Languages & Frameworks > Android SDK**,
pestaña **SDK Tools**, y marca "Android SDK Platform-Tools" y "Android Emulator".

### 2. La imagen del emulador

En **Settings > Languages & Frameworks > Android SDK**, pestaña **SDK
Platforms**, marca abajo **"Show package details"** y elige la imagen
**arm64-v8a con Google Play** de Android 37.1 (`google_apis_playstore_ps16k`).
Aplicar y esperar, son varios GB.

Tiene que ser la de **Play Store**: sin ella no puedes instalar Pokemon GO
dentro del emulador.

Comprobar:

```sh
ls ~/Library/Android/sdk/system-images/android-37.1/google_apis_playstore_ps16k/arm64-v8a
```

### 3. El emulador

Crea el AVD desde Android Studio (**Device Manager > Create Virtual Device >
Medium Phone**, y elige la imagen del paso anterior), o deja que lo cree el
script del paso 5, que trae la definicion guardada en `avd/`.

### 4. El repo

```sh
git clone https://github.com/BaltaJmn/pogo.git ~/pogo
cd ~/pogo
```

### 5. Arrancar

```sh
./run.sh
```

Si te dice que faltan `starlette` y `uvicorn`, instala [uv](https://docs.astral.sh/uv/)
y `run.sh` se encarga solo a partir de ahi:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

O con pip, si lo prefieres:

```sh
python3 -m pip install starlette uvicorn
```

Abre <http://127.0.0.1:8765> y pulsa **"Arrancar emulador"**. Tarda un par de
minutos la primera vez. El boton aplica los parches de GPU, arranca el emulador
con la configuracion correcta y le pone la resolucion.

### 6. Pokemon GO

Dentro del emulador, abre la Play Store, inicia sesion con una cuenta de Google
cualquiera e instala Pokemon GO. Luego entra al juego **con la cuenta PTC
desechable**, no con la de Google.

Esto hay que hacerlo a mano, no se puede guionizar.

### 7. Comprobar que quedo bien

```sh
./emulator.sh status
```

Tiene que decir esto:

```
avd=Medium_Phone_2
running=yes
booted=yes
serial=emulator-5554
gles=196609
size=720x1600
icd=kosmickrisp
```

`gles` distinto de `196609` significa que no vas a ver tu avatar. `icd` distinto
de `kosmickrisp` significa que el juego ira a 8 FPS en vez de 30. En los dos
casos, `./emulator.sh stop && ./emulator.sh start`.

`spoof.py` busca `adb` en el `PATH` y, si no esta, en
`~/Library/Android/sdk/platform-tools/adb`.

## Uso diario

```sh
./run.sh
```

Abre <http://127.0.0.1:8765>. Deja la terminal abierta: si matas el proceso se
corta la inyeccion y el emulador se queda en la ultima coordenada.

Si el emulador no esta arrancado, pulsa **"Arrancar emulador"** en la web. O
desde la terminal:

```sh
./emulator.sh start
```

Las dos cosas hacen lo mismo y son idempotentes: con el emulador ya arrancado,
solo reponen la resolucion.

**No lo arranques desde el boton de play de Android Studio.** No pasa
`-gpu swangle`, y sin eso el juego funciona y cuenta kilometros pero no dibuja
tu avatar ni mueve la camara.

Con varios emuladores abiertos, pasa el serial que salga en `adb devices`:

```sh
./run.sh emulator-5554
```

## El emulador

Toda la configuracion que hace jugable a Pokemon GO vive **fuera del repo**:
dentro del SDK de Android y en `~/.android`. Es decir, se pierde si actualizas
el emulador o borras el AVD. `emulator.sh` la guarda y la vuelve a aplicar.

```sh
./emulator.sh start     # parchea si hace falta, arranca, espera y pone la resolucion
./emulator.sh setup     # solo los parches, sin arrancar
./emulator.sh status    # clave=valor, es lo que lee la web
./emulator.sh stop      # apaga
./emulator.sh unpatch   # devuelve el ICD de ANGLE a SwiftShader
```

`status` en un emulador sano:

```
avd=Medium_Phone_2
running=yes
booted=yes
serial=emulator-5554
gles=196609
size=720x1600
icd=kosmickrisp
```

Si `gles` no es `196609` no se dibuja el avatar. Si `icd` no es `kosmickrisp` el
juego va a 8 FPS en vez de 30.

### Que toca, y por que

| Que | Donde | Por que |
|---|---|---|
| `-gpu swangle` | flag de arranque | Da OpenGL ES 3.1. Sin ES 3.1 no se dibuja el avatar ni sigue la camara |
| ICD de ANGLE a kosmickrisp | `$SDK/emulator/lib64/gles_angle/vk_swiftshader_icd.json` | De fabrica apunta a SwiftShader, que pinta por CPU: 8 FPS. kosmickrisp es Vulkan 1.3 sobre Metal: 30 FPS |
| `Vulkan = on`, `GLDirectMem = on` | `~/.android/advancedFeatures.ini` | Lo que ya habia. `GuestAngle` tiene que quedar **apagado**: da ES 3.1 pero Unity lo rechaza |
| `wm size 720x1600`, `wm density 280` | via adb, en cada arranque | El override no sobrevive al reinicio. A resolucion nativa el render se ahoga |

Trampas conocidas:

- **MoltenVK como ICD de ANGLE no vale.** Revienta el emulador al arrancar, le
  faltan extensiones. Tiene que ser kosmickrisp.
- **`-cores` no da FPS.** El render ocurre en el host, no en el guest. Mide
  igual con 4, 6 y 8. Y con 10 ni arranca: el tope de QEMU son 8
  (`Number of SMP CPUs requested (10) exceeds max CPUs supported by machine 'mach-virt' (8)`),
  aunque el desplegable de Android Studio te deje poner 6 como maximo.
- **Bajar mas la resolucion tampoco.** De 720x1600 a 540x1200 no gana nada.

### Si borras el AVD

La definicion esta en `avd/` (`config.ini` y `avd.ini`). `./emulator.sh start`
recrea el AVD solo si no existe. Necesita la imagen de sistema descargada; si
falta, el script te da el comando exacto:

```sh
~/Library/Android/sdk/cmdline-tools/latest/bin/sdkmanager \
  "system-images;android-37.1;google_apis_playstore_ps16k;arm64-v8a"
```

Despues hay que entrar en el emulador e instalar Pokemon GO desde la Play Store
a mano, eso no se puede guionizar.

Para usar otro AVD: `POGO_AVD=MiOtroAvd ./emulator.sh start`, o ponlo en `.env`.

## Controles

| Accion | Como |
|---|---|
| Elegir que hacer con un punto | Click en el mapa (con "Modo ruta" desactivado) |
| Mover | Arrastrar la aguja de la rosa, o `WASD` / flechas |
| Velocidad | Slider, o los presets Andar / Rapido / Bici |
| Crear ruta | Marcar "Modo ruta" y hacer click en cada punto |
| Recorrer ruta | Boton "Recorrer" |
| Fijar un objetivo de km | Los botones de la seccion "Objetivo" |
| Reiniciar el contador | "Poner el contador a cero" |
| Guardar la ruta dibujada | Boton "Guardar ruta actual", y le pones nombre |
| Recuperar una ruta guardada | Boton "Cargar" en la lista de rutas |
| Pausar a mitad de ruta | Boton "Pausar", o la tecla `espacio` |
| Seguir donde lo dejaste | Boton "Reanudar", o `espacio` otra vez |
| Fin de ruta | Bucle, Ida y vuelta, o Parar |
| Guardar un lugar | Click en el mapa, "Guardar", y le pones nombre |
| Guardar donde estas | Boton "Guardar esta posicion" |
| Ir andando a un sitio | "Andar", en el globo del mapa o en la lista de lugares |
| Saltar a un sitio | "Saltar", en el globo del mapa o en la lista. Pide confirmacion |
| Fijar casa | "Fijar casa en esta posicion", con la posicion puesta en tu portal |
| Volver a casa andando | Boton "Andar a casa" |
| Volver a casa de golpe | Boton "Saltar a casa", tiene cooldown |
| Centrar el mapa | Boton "Centrar aqui" |
| Que el mapa te siga | Boton "Seguir" (se queda activado) |
| Arrancar el emulador | Boton "Arrancar emulador" |
| Volver al GPS real | Boton "Devolver GPS real" |

El mapa no persigue al marcador por defecto: si lo arrastras para mirar otra
zona, no te lo devuelve al sitio en el siguiente sondeo. "Seguir" activa el
perseguimiento cuando lo quieras.

**Un click en el mapa ya no te teletransporta de golpe.** Sale un globo con las
tres cosas que puedes querer hacer con ese punto: ir andando, saltar, o
guardarlo con nombre. Saltar tiene cooldown y casi nunca es lo que quieres, asi
que ya no es lo que pasa por defecto.

**La ruta se puede pausar.** Si ves un gimnasio o una parada que quieres, dale a
"Pausar" (o a `espacio`) y te quedas quieto donde estes, sin perder por donde
ibas. "Reanudar" sigue desde ese mismo punto, no desde el principio. La etiqueta
de la seccion Ruta te dice por donde vas: "punto 3 de 7".

La rosa de los vientos marca el rumbo, no es solo un mando. Andando a mano lo
saca del joystick; recorriendo una ruta, de la diferencia entre posiciones, que
es cuando de verdad te interesa mirarla.

La ruta actual, la velocidad, los lugares, las rutas guardadas y el objetivo de
distancia viven en el navegador. Siguen ahi al reabrir.

Manda una coordenada por segundo, como un GPS real, con +-3 metros de ruido para
que la traza no salga en linea geometrica perfecta.

## Objetivo de distancia

Aqui se anda por una razon: incubar huevos (2, 5, 7, 10 o 12 km) y el caramelo
de compañero. La seccion **Objetivo** convierte el contador suelto en lo unico
que quieres saber, cuanto falta.

Eliges la distancia de tu huevo y la barra de escala te dice por donde vas:

```
OBJETIVO                                    10 km
[ 2 ][ 5 ][ 7 ][ 10 ][ 12 ][ Ninguno ]
[####################              ]
Faltan 3.6 km, unos 48 min andando.
```

Detalles que importan:

- **El progreso no se pierde al saltar.** El `dist` del servidor se reinicia
  cada vez que colocas la posicion, asi que la web acumula los incrementos en
  vez de leerlo tal cual. Un salto no te borra el huevo, igual que no te lo
  borra el juego.
- **Sobrevive a cerrar el navegador.** Incubar un huevo de 10 km lleva dias, no
  una sesion. Vive en el `localStorage`.
- **Por encima de 10.5 km/h se para**, y te dice que esta parado. Ver
  [Velocidad](#velocidad).
- **"Poner el contador a cero"** cuando eclosione, para el siguiente.

## Rutas guardadas

Las rutas que dibujas se pueden guardar con nombre y recuperar despues, para no
tener que volver a marcar los puntos cada vez.

Dibuja la ruta como siempre (marca "Marcar puntos en el mapa" y ve haciendo
click), y pulsa **"Guardar ruta actual"**. Pide un nombre y ya esta.

Cada ruta de la lista muestra lo que mide y trae dos cosas:

- **Click en el nombre**: encuadra el mapa en esa ruta para que la veas, sin
  tocar la que tengas puesta.
- **Cargar**: la pone como ruta activa. Ojo, **reemplaza la que tuvieras
  dibujada**, asi que guardala antes si te interesa. No empieza a andar sola:
  la carga y ya le das a "Recorrer" cuando quieras.

Cargar una ruta la deja siempre en el punto 1, aunque vinieras de una pausa a
mitad de otra.

### Por calles

Marcar cuatro puntos a ojo te hace atravesar manzanas en linea recta. El boton
"Por calles" pasa los puntos que tengas marcados por Valhalla, el enrutador de
OpenStreetMap (<https://valhalla1.openstreetmap.de/route>), con perfil
"pedestrian", y sustituye la ruta por la linea entera que devuelve, calle a calle.

En una prueba real en Cordoba con 3 puntos: 1.831 m en linea recta contra 2.389
m por calles. Se eligio Valhalla y no OSRM porque el servidor publico de OSRM
solo tiene grafo de coche, y para el mismo tramo daba 1.979 m evitando lo
peatonal. El precio de Valhalla es decodificar una polilinea de precision 6:
catorce lineas de codigo, verificadas contra el total que reporta el propio
Valhalla. 2.389 m decodificados contra 2.389 m reportados, sin discrepancia.

Aviso importante: valhalla1.openstreetmap.de lo mantiene la comunidad y no tiene
garantia de servicio. Si falla, la ruta se queda como estaba y el estado lo dice.

**No se puede ajustar mientras la ruta esta andando.** Hay que pararla antes:
el boton "Pausar" te deja quieto sin perder por donde ibas, luego ajusta y sigue
de ahi.

La peticion a Valhalla vive ahora en una sola funcion que usan tanto el boton
"Por calles" como el botón "Andar" a un sitio. Los numeros de los puntos de ruta
(salida, 1, 2, ..., final) solo salen si la ruta tiene doce puntos o menos. Una
ruta por calles trae cientos de vertices de geometria y numerarlos tapaba el mapa:
en esas se dibujan solo "salida" y "final". En las rutas que marcas tu a mano los
numeros siguen igual.

### Etiqueta de la ruta

La etiqueta debajo del boton "Recorrer" ahora dice lo que mide. Por ejemplo:
"3 puntos . 1.8 km". Con el modo "Bucle" ese numero es el que indica cuantas
vueltas hacen falta para el huevo.

## Buscar sitio

Caja de busqueda encima del mapa, justo bajo los botones "Centrar" y "Seguir".
Escribes el nombre de un sitio (calle, plaza, parque, monumento, lo que sea) y la
web te lo encuentra en el mapa. El buscador vive ahi porque mirar el mapa es lo que
importa cuando buscas; la barra lateral queda para lo que es configuracion.

Usa Nominatim, el geocodificador de OpenStreetMap
(<https://nominatim.openstreetmap.org/search>). No necesita clave de API, no suma
ninguna dependencia al proyecto, y permite CORS, asi que la peticion sale directo
desde el navegador.

**Solo busca al enviar.** El boton "Ir" o Enter dispara la busqueda, nunca segun
tecleas. Es a proposito: la politica de Nominatim pide como mucho una peticion por
segundo, y buscar al enviar sale gratis en codigo comparado con montar un debounce
o un apaño similar.

### Coordenadas pegadas

Google Maps te da una pokeparada como "37.881994, -4.768207". Pegarlo en la caja
de busqueda y que se lo tire a un geocodificador no tiene sentido: ya es la
respuesta.

El buscador lo detecta automaticamente. Si lo que escribes son dos numeros validos
(latitud y longitud), no consulta a Nominatim: ya es el resultado. Sale directamente
como candidato, con su "Andar" y su "Saltar", sin hacer peticion a la red.

Acepta coma, punto y coma o solo un espacio entre los dos numeros. Latitud primero,
como lo escribe Google Maps.

Los resultados se sesgan hacia el trozo de mapa que estas viendo, pasando el
"viewbox" de Leaflet al geocodificador. Como no se pone `bounded=1`, si el sitio
esta fuera tambien lo encuentra: solo prioriza lo cercano.

Cada resultado sale como una fila igual a las de Lugares, con la distancia a la
que estas y los mismos dos botones: "Andar" y "Saltar". Son literalmente las mismas
funciones, asi que "Saltar" dispara cooldown y pide la confirmacion de costumbre.

Click en el nombre centra el mapa ahi sin mover el personaje ni crear ruta ninguna.
El nombre que devuelve Nominatim es kilometrico, asi que en la fila se recortan los
tres primeros trozos y el resto queda en el tooltip.

Los resultados no se guardan en ningun sitio. Si quieres conservar uno, salta o anda
hasta alli y guarda la posicion con "Guardar esta posicion" de la seccion Lugares.

### Candidatos a parada

El boton "Candidatos a parada" busca en el trozo de mapa que estas viendo por
posibles ubicaciones de pokeparadas.

**Advertencia importante:** no existe ninguna API publica de pokeparadas ni de
gimnasios. Lo que circula por internet son scrapers de la red privada del juego:
violan los terminos de servicio de Niantic y ponen tu cuenta en riesgo. Esto no es
eso.

Lo que hace es consultar Overpass, la API de consultas de OpenStreetMap
(<https://overpass-api.de/api/interpreter>). Gratis y sin clave de API: es la
puerta publica a los datos de OSM.

Por que sirve de algo: las paradas reales salen de portales de Ingress, y esos
portales salen de arte urbano, monumentos, fuentes, iglesias, parques infantiles y
pistas deportivas. Eso es justo lo que se le pide a OpenStreetMap. La idea es que
si hay algo interesante en el mundo real, alguien lo mapea en OSM y Ingress lo
recoge de alli.

Las etiquetas que consulta son: `tourism=artwork`, cualquier cosa bajo `historic`,
`amenity` en `place_of_worship`, `fountain`, `library`, `post_office`, `townhall`,
`theatre`, `community_centre`, y `leisure` en `playground`, `pitch`, `park`,
`fitness_station`. Consulta tanto nodos como recintos (poligonos), pidiendo el
centro de cada recinto con `out center` para que Overpass te de un punto unico.

**Los candidatos son candidatos, no paradas reales.** Habra POI que aparezcan aqui
y no sean parada. Y habra paradas reales que no esten en OpenStreetMap. Como brujula
para decidir a que barrio ir y donde buscar, sirve. Como mapa fiel de paradas, no.

**Pide zoom 14 como minimo.** Por debajo Overpass rechaza la consulta o tarda
mucho: mide el area en tiempo de CPU, y debajo del zoom 14 el trozo de mapa es
demasiado grande. Ademas, salen tantos puntos que no dicen nada.

El boton funciona de interruptor: pulsa una vez y aparecen los candidatos. Pulsa otra
vez y se van. El texto del boton cambia entre "Candidatos a parada" y "Ocultar
candidatos", para que veas el estado sin necesidad de otro control. Si cambias de
zoom o arrastras el mapa, los puntos siguen ahi; si sacas zoom por debajo de 14 el
boton se desactiva (no se pueden pedir candidatos a ese zoom). Cuando vuelves a zoom
14 el boton se reactiva.

Los candidatos se pintan en dorado, para no confundirlos con los resultados de
Nominatim (magenta) ni con los lugares guardados. Click en cualquier candidato abre
el mismo popup que un click en el mapa, con los botones "Andar", "Saltar" y "Guardar".
Si el sitio tiene nombre en OpenStreetMap, el campo de guardar viene ya relleno con el.

## Radio de accion

Un circulo de 40 metros alrededor de tu posicion, dibujado en metros de verdad y no
en pixeles. Encoge y crece con el zoom, asi que ve siempre a escala real.

40 metros es justo la distancia a la que el juego te deja girar una parada o entrar
a un gimnasio. Junto a los candidatos de Overpass, el mapa deja de ser un selector
de puntos y pasa a servir para planificar: ves de un vistazo si llegas a tocar
cada candidato desde donde estas, sin necesidad de ampliar cada uno.

## Lugares

Sitios guardados con nombre, para no tener que buscarlos en el mapa cada vez.

Para guardar uno: click en el mapa, "Guardar", y le pones nombre. O el boton
"Guardar esta posicion", que guarda donde estes ahora.

Cada lugar de la lista tiene dos botones, y la diferencia importa:

- **Andar**: te pone a caminar hacia alli a la velocidad que tengas puesta, y
  para al llegar. Reemplaza la ruta que tuvieras dibujada. Mientras vas, debajo
  de las coordenadas te dice cuanto falta y cuanto tarda.
  
  No traza una recta entre donde estas y el destino. Pasa los dos puntos por
  Valhalla, el enrutador de OpenStreetMap, con perfil "pedestrian", y anda la
  linea completa calle a calle. Una recta perfecta que cruza manzanas, rios y
  edificios no la anda ningun peaton: de todo lo que puede delatar a un cliente
  falseado, la forma del recorrido es lo unico que se arregla desde la web.
  
  En una prueba real en Cordoba: un trayecto de 1.359 metros en linea recta sale
  1.645 metros por calles, o sea 1,21 veces mas, con 88 puntos, y el enrutador
  tardo 288 milisegundos. Si el enrutador no contesta, se anda la recta de
  siempre y el estado lo dice: "en linea recta, el enrutador no contesta".
  Quedarse quieto seria peor.
  
  El "faltan X, unos Y andando" ahora se calcula sumando lo que queda de ruta
  desde el punto al que va el servidor, no en linea recta. Antes se quedaba
  corto justo cuando mas se miraba.
  
  Si pulsas Andar a un sitio y luego a otro antes de que termine de trazar,
  gana el segundo. Un contador de peticion descarta la respuesta que ya no vale.
- **Saltar**: teletransporte. Instantaneo, pero **dispara cooldown**, asi que
  pide confirmacion antes (ver [Confirmacion de saltos](#confirmacion-de-saltos)).

Click en el nombre centra el mapa ahi sin mover nada.

Los lugares viven en el `localStorage` del navegador, igual que casa y que las
rutas guardadas. **No se guardan en el repo ni se mandan a ningun sitio.**

## Punto de partida (casa)

Fija tu ubicacion real como punto de partida. Al abrir la web el movil arranca
siempre ahi, no en donde lo dejaste la ultima vez. Asi no hay saltos entre
sesiones.

Una sola vez:

1. Busca tu portal en el mapa y haz zoom.
2. Haz click encima, con "Modo ruta" desactivado, y pulsa "Saltar".
3. Pulsa "Fijar casa en esta posicion", en la seccion Casa.

Se guarda en el `localStorage` del navegador. **No se guarda en el repo ni se
manda a ningun servidor**: tu direccion no sale de tu Mac. Si borras los datos
del navegador hay que volver a fijarla.

Hay dos formas de volver:

- **"Andar a casa"**: te lleva caminando, como cualquier otro lugar. Sin
  cooldown, porque andar no dispara nada. Es lo que quieres casi siempre.
- **"Saltar a casa"**: teletransporte. Util si estabas lejos de verdad, pero
  **dispara cooldown** como cualquier salto, y por eso pide confirmacion.

## Reglas de Pokemon GO

### Velocidad

Por encima de **10.5 km/h** el juego deja de contar la distancia. Para incubar
huevos y el caramelo de compañero usa Andar (4.5) o Rapido (9). El preset Bici
(15) sirve para desplazarte, no para acumular kilometros.

La web lo refleja: el slider lleva una marca en 10.5, y al pasarla la velocidad
se pone en rojo y el contador de distancia se para. **Se para de verdad, no solo
avisa**, porque un contador que sume lo que el juego no suma es peor que no
tener contador.

**La velocidad que manda es la del servidor**, no la del slider. Con dos pestañas
abiertas se desincronizaban: una cambiaba el slider, pero la otra seguia con la
velocidad anterior, y el "faltan X, unos Y andando" mentia. Ahora el sondeo
sincroniza el slider con el servidor una vez por segundo, salvo mientras lo estas
arrastrando: mientras lo tocas vale tu version, para que no te pelee el ratón
con las actualizaciones de la red.

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

**Ningun salto ocurre sin que lo confirmes**, ver
[Confirmacion de saltos](#confirmacion-de-saltos).

**La web lleva la cuenta sola.** Cada vez que saltas (click en el mapa y "Saltar
aqui", "Saltar" en un lugar, o "Ir a casa") mide el salto, busca en esa tabla y
saca un contador rojo con el tiempo que queda. Sobrevive a recargar la pestaña,
porque el cooldown no lo lleva el juego, lo llevas tu. Andando no aparece: andar
no dispara nada.

### Confirmacion de saltos

Cualquier cosa que te teletransporte ("Saltar" en el globo del mapa, "Saltar" en
un lugar guardado, "Saltar a casa") abre antes un dialogo que te dice a que
distancia esta y **cuanto cooldown te va a costar exactamente**. Nada se manda
hasta que le das a "Saltar" ahi. Escape o "Cancelar" y no ha pasado nada.

Si el salto es de menos de 1 km, el dialogo lo dice: "Salto corto, no genera
cooldown". Sale igual, para que la distincion la veas tu y no tengas que
acordarte de la tabla.

**El dialogo avisa tambien si ya hay un cooldown corriendo** del salto anterior,
con lo que queda. Saltar encima de un cooldown abierto es justo lo que hay que
evitar: te comes un soft ban. Antes solo decia el cooldown que ibas a provocar,
no el que todavia estaba pasando.

Andar no pregunta nada: no cuesta cooldown, asi que no hay nada que confirmar.

La comprobacion vive en la funcion que hace el salto, no en cada boton, de modo
que cualquier via que se anada mas adelante queda cubierta sola.

### Higiene

- Cuenta PTC desechable, nunca la principal.
- No alternes ubicacion real y falsa el mismo dia. Al volver a tu sitio real,
  cooldown completo antes de tocar nada.
- Sin VPN a otro pais con GPS local, ni al reves: la incoherencia IP contra GPS
  es señal directa.
- Soft ban (los Pokemon huyen al primer intento, las paradas no dan items):
  gira la misma parada unas 40 veces seguidas, o espera el cooldown.

## Como funciona

### La idea, en una frase

El juego no sabe donde estas. Sabe lo que le cuenta el sistema operativo. Este
proyecto le miente al sistema operativo, y el juego se lo cree porque no tiene
forma de distinguirlo.

Y ahi esta el porque de que esto sea Android y no iPhone, que es toda la
historia del proyecto: en el emulador la mentira entra por el mismo sitio por el
que entraria un GPS de verdad, asi que es indistinguible. En iOS entra por una
puerta lateral que deja marca, y Niantic mira la marca. El detalle esta en
[docs/ios.md](docs/ios.md).

### Que pasa cuando arrastras la aguja

1. **El navegador no mueve nada.** Manda una intencion: `POST /loc` con `vx` y
   `vy`, que es "hacia el noreste", no "ponme en estas coordenadas". Y para de
   hablar.
2. **`spoof.py` tiene un bucle que despierta una vez por segundo.** Mira la
   ultima intencion que le llego, calcula cuantos metros das en un segundo a la
   velocidad que tengas puesta, y mueve la posicion esos metros.
3. **Le suma ruido de +-3 metros.** Un GPS real nunca da dos lecturas identicas.
   Una traza perfectamente recta y perfectamente regular no la produce ningun
   telefono.
4. **Inyecta la coordenada** con `adb emu geo fix <lon> <lat>`.
5. **Android se la entrega a las apps como si viniera de un satelite.** No hay
   "mock location" de por medio, no hace falta root, y no hay bandera que
   delate nada: `geo fix` alimenta el GPS emulado, que para ese Android es el
   unico GPS que existe.
6. **Aparte, el navegador pregunta `GET /pos` una vez por segundo**, solo para
   pintar el mapa y la rosa. Si dejas de preguntar, no pasa nada: tu seguirias
   andando igual.

### Por que el bucle vive en el servidor y no en el navegador

Porque para mirar el juego tienes que tapar el navegador, y Chrome estrangula
los temporizadores de las pestañas ocultas. Con el bucle en la pagina, andabas a
tirones o directamente parabas al cambiar de ventana.

Con el bucle en `spoof.py` la pagina es un mando y un espejo: si la cierras,
sigues andando. Puedes recargarla a mitad de ruta y no se entera nadie.

### Las piezas

| Fichero | Que hace |
|---|---|
| `spoof.py` | El servidor. Lleva el movimiento, inyecta la posicion y sirve la web. Todo el estado vive aqui |
| `test_spoof.py` | Los 9 tests del calculo de movimiento |
| `run.sh` | Lo que arrancas. Levanta `spoof.py` con las dependencias que encuentre |
| `index.html` | El mando: mapa con radio de 40 m, rosa de los vientos, rutas (con boton "Por calles" y "Andar" a sitio), lugares, buscador de Nominatim, coordenadas pegadas y candidatos de Overpass. No calcula movimiento, solo manda intenciones y pinta |
| `emulator.sh` | Arranca el emulador con la configuracion que hace jugable al juego, y la repara si se perdio |
| `avd/` | La definicion del emulador, por si lo borras |

### Lo que no sale de tu Mac

Casa, los lugares, las rutas guardadas, la ruta actual y el objetivo de
distancia viven en el `localStorage` del navegador.
No se commitean, no se mandan a ningun servidor y no se buscan en ningun
geocodificador.

Este repo es publico. Esa es justo la razon.

## Problemas

**`address already in use`**

Quedo un proceso vivo de una ejecucion anterior:

```sh
lsof -ti tcp:8765 | xargs kill
```

**El emulador arranca pero no se ve mi avatar**

Le falta OpenGL ES 3.1. Comprueba con `./emulator.sh status` que `gles=196609`.
Si pone `196608`, lo arrancaste sin `-gpu swangle`, casi seguro desde el boton
de Android Studio. Cierralo y usa `./emulator.sh start`.

**El juego va a tirones**

`./emulator.sh status` y mira `icd`. Si pone `swiftshader` en vez de
`kosmickrisp`, el parche se perdio, normalmente porque Android Studio actualizo
el emulador. `./emulator.sh setup` lo repone.

**`adb: no devices/emulators found`**

El emulador no esta arrancado, o aun no termino de arrancar. `./emulator.sh status`.

## Tests

Cubren lo unico que puede romperse en silencio: el orden `lon`/`lat` que pide
`adb emu geo fix` y el motor de movimiento del servidor.

```sh
uvx --with starlette --with uvicorn pytest test_spoof.py -q
```

Sin uv, con pytest y las dependencias ya instaladas: `pytest test_spoof.py -q`.

## Cambiar el puerto

```sh
./run.sh --port 9000
```

## Registro de intentos

Lo probado y como acabo, para no repetir callejones sin salida entre sesiones.

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

### 2026-09-06, tarde 4: forzar Vulkan en Unity tampoco sirve

**Intento:** lanzar el juego pidiendole a Unity que use Vulkan en vez de OpenGL, con el argumento de arranque de Unity pasado como extra del intent:

```sh
adb shell am start -n com.nianticlabs.pokemongo/com.nianticproject.holoholo.libholoholo.unity.UnityMainActivity --es unity "-force-vulkan"
```

**Resultado:** el juego arranca, pero Unity responde en logcat:

```
E Unity   : Forced GfxDevice 'Vulkan' was not built from editor, shaders will not be available
```

**Interpretacion:** el APK de Pokemon GO no lleva variantes de shader compiladas para Vulkan, solo para OpenGL ES. Aunque el emulador tenga Vulkan activo y funcionando (MoltenVK sobre Apple M2 Pro), el juego no puede usarlo. La via de Vulkan queda cerrada para esta build del juego.

**Y siguen apareciendo los mismos errores al volver a OpenGL:**

```
E GFXSTREAM: [egl.cpp(1800)] EGL_BAD_CONFIG: no ES 3.2 support
E GFXSTREAM: [egl.cpp(1794)] EGL_BAD_CONFIG: no ES 3.1 support
```

**Confirmacion del usuario:** el juego arranca pero el personaje sigue sin aparecer.

**Estado:** descartadas hasta ahora tres vias para subir de OpenGL ES 3.0: ANGLE por paquete (carga pero Unity no inicializa), Unity eligiendo Vulkan solo (no lo hace) y forzar Vulkan por argumento (no hay shaders).

### 2026-09-06, tarde 5: correccion, OpenGL NO es la causa raiz

**Correccion de las secciones "tarde 3" y "tarde 4":** alli se concluyo que la falta de avatar venia del cap de OpenGL ES 3.0. Es falso.

**Prueba:** capturas del emulador con el juego en marcha. La pantalla de captura de un Pokemon renderiza perfecta: modelo de Pancham con texturas, sombras, efectos de particulas de la Ultra Ball, escenario 3D completo. El mapa tambien renderiza entero: carreteras, PokeParadas, gimnasios, contadores de incursion, icono del tiempo, iconos de objetos, HUD con nivel 41 y el compañero Gardevoir.

**Reinterpretacion de los logs EGL:** los errores `EGL_BAD_CONFIG: no ES 3.2 support` y `EGL_BAD_CONFIG: no ES 3.1 support` son solo el sondeo normal de Unity buscando la version mas alta antes de caer a ES 3.0. El juego funciona en ES 3.0 sin problema.

**Otra lectura equivocada:** las siluetas negras en la barra inferior no eran un fallo de texturas. Son las siluetas de Pokemon no vistos que el juego dibuja asi a proposito.

**Observacion nueva sin explicar todavia:** en el mapa aparece una cadena de Pokemon identicos dibujados enormes en la zona baja de la pantalla, justo donde deberia estar el avatar. Sospecha: son spawns acumulados en la posicion del jugador (incienso) tapando el avatar, no un fallo de render.

**Estado:** la investigacion vuelve al lado de la localizacion y del estado del juego, no del GPU.

### 2026-09-06, tarde 6: RESUELTO, el avatar necesita OpenGL ES 3.1

- Se retira la correccion de la seccion "tarde 5". Estaba equivocada. La causa raiz SI era el cap de OpenGL ES 3.0.
- Por que despisto: el juego renderiza perfectamente en ES 3.0 (Pokemon, mapa, gimnasios, efectos, HUD). Lo unico que no se dibuja es el avatar del entrenador. Se comprobo que tampoco aparece en la pantalla de perfil, ni esperando 30 segundos, asi que no era carga lenta ni un problema de camara.
- La pista que faltaba: el avatar es la unica cosa del juego que necesita algo que ES 3.0 no da.
- La solucion: el modo de GPU "swangle" del emulador, que es ANGLE con backend SwiftShader. Expone OpenGL ES 3.1 al guest.
- Comando que funciona:

```sh
~/Library/Android/sdk/emulator/emulator -avd Medium_Phone_2 -gpu swangle -no-snapshot-load
```

- Antes, con -gpu host:

```
GLES: Google (Apple), Android Emulator OpenGL ES Translator (Apple M2 Pro), OpenGL ES 3.0 (4.1 Metal - 90.5)
ro.opengles.version = 196608
```

- Despues, con -gpu swangle:

```
GLES: Google (Google Inc. (Google)), Android Emulator OpenGL ES Translator (ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (LLVM 10.0.0) (0x0000C0DE)), SwiftShader driver-5.0.0)), OpenGL ES 3.1 (OpenGL ES 3.1.0 (ANGLE 2.1.1 git hash: fbf66f49c7cc))
ro.opengles.version = 196609
```

- En logcat ya solo queda el aviso de ES 3.2, el de ES 3.1 desaparece:

```
E GFXSTREAM: [egl.cpp(1800)] EGL_BAD_CONFIG: no ES 3.2 support
```

- Resultado: el avatar del entrenador aparece en el mapa y tambien en el icono del HUD abajo a la izquierda.
- Contrapartida: SwiftShader renderiza por CPU, asi que va mas lento y las texturas se ven con ruido.
- Nota de metodo: el emulador se arranco con -no-snapshot-load a la vez que se cambio el modo de GPU, asi que en rigor cambiaron dos cosas. La evidencia apunta al modo de GPU, porque con ES 3.0 el avatar falto en decenas de arranques de la app, incluidos arranques en frio.
- Lista completa de modos de GPU del emulador, de "emulator -help-gpu": auto, host, software, lavapipe, swiftshader, swangle.

### 2026-09-06, tarde 7: la camara tambien queda cerrada

La seccion "tarde 2" dejo abierto que la camara no seguia al personaje. Queda
cerrado: era el mismo fallo que el avatar, y `-gpu swangle` lo arregla. La
hipotesis de "tarde 2" era correcta, la camara sigue al avatar y sin avatar
instanciado no tenia a quien seguir.

Verificado con el emulador y el servidor en marcha:

```
servidor  GET /pos   {"lat":37.881853395616176,"lon":-4.795,"dist":95.0}
emulador  gps        Location[gps 37.881832,-4.795000 hAcc=5.0 ...]
emulador  fused      Location[fused 37.881834,-4.795001 hAcc=3.392 vel=0.176 bear=89.99 ...]
```

Los 2 metros de diferencia en latitud son el ruido de +-3 m que mete el servidor
a proposito. El `bear=89.99` del proveedor `fused` es rumbo este, coherente con
el ultimo movimiento.

Modo de GPU en el emulador de la prueba:

```
ro.opengles.version = 196609
GLES: Google (Google Inc. (Google)), Android Emulator OpenGL ES Translator
      (ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device ...))), OpenGL ES 3.1
```

Arrancado con `-avd Medium_Phone_2 -gpu swangle -no-snapshot-load`.

**Estado del proyecto:** cerrado y funcionando en emulador de Android. iOS
descartado con evidencia, archivada en [docs/ios.md](docs/ios.md). Los 8 tests
de `test_spoof.py` pasan.

**Nota de metodo, error cometido.** En una sesion anterior se lanzo un script de
diagnostico llamando a `establish_native_rsd()` sin pasar UDID. Cogio el primer
dispositivo emparejado, que no era el iPhone XR sino el iPhone 16 Pro personal, y
le inyecto ubicacion simulada unos segundos antes de limpiarla con
`stopLocationSimulation`. Sin consecuencias, la simulacion DVT no sobrevive a la
desconexion, pero conviene recordarlo: `run.sh` pasa el UDID desde `.env`, los
scripts sueltos no. **Cualquier script de diagnostico contra un dispositivo Apple
tiene que pasar `serial=` explicito.**

### 2026-09-06, tarde 8: de 8 a 30 FPS sin perder el avatar

`-gpu swangle` dejaba el juego jugable pero a **7.8 FPS**. La causa: swangle es
ANGLE de host traduciendo GLES a Vulkan, y el Vulkan que usaba era SwiftShader,
que es un rasterizador **por software**. La GPU del Mac no pintaba nada.

El nudo era este:

| Config | GLES | Backend | Avatar | FPS |
|---|---|---|---|---|
| `-gpu swangle` | 3.1 | SwiftShader (CPU) | si | 7.8 |
| `-gpu host` | 3.0 | Apple M2 Pro | **no** | 30.0 |
| `-gpu host` + `GuestAngle` | 3.1 | Apple M2 Pro | Unity no arranca | - |

El avatar necesita ES 3.1. `-gpu host` en macOS se queda en ES 3.0 porque el
OpenGL de macOS tope en 4.1 y ES 3.1 pide GL 4.3. O sea: velocidad sin avatar, o
avatar sin velocidad.

**Lo que no funciono:**

- **Bajar resolucion.** De 1080x2400 a 720x1600 sube de 7.9 a ~9-11 FPS. De ahi
  a 540x1200 no gana nada mas. No es fill rate.
- **Subir `-cores`.** 4 cores da 7.9, 6 da 9.0, 8 da 7.8. Todo ruido de la misma
  medida. SwiftShader corre en el proceso del emulador, en el host, asi que los
  cores del guest no le tocan. Y con `-cores 10` el emulador ni arranca:
  `Number of SMP CPUs requested (10) exceeds max CPUs supported by machine
  'mach-virt' (8)`. El tope de QEMU son 8, no los 6 del desplegable de Android
  Studio.
- **`-gpu angle`.** No es un modo valido. El emulador lo rechaza y cae a
  lavapipe, que tambien es software: ES 3.0 y `Selecting Vulkan device: llvmpipe`.
  Los modos validos, sacados del binario, son
  `'auto', 'host', 'lavapipe', 'swiftshader' o 'swangle'`.
- **`GuestAngle` sobre hardware.** La hipotesis era que Unity rechazaba ANGLE en
  guest porque debajo estaba MoltenVK, que es Vulkan incompleto (el propio
  binario del emulador lleva la cadena "MoltenVK enabled but necessary device
  extensions are not supported"). Se repitio con kosmickrisp, que si es Vulkan
  1.3 completo. Arranca bien:

  ```
  ro.opengles.version = 196609
  Selecting Vulkan device: Apple M2 Pro, Version: 1.3.348
  ANGLE : Version (2.1 ...), Renderer (Vulkan 1.3.0 (Goldfish GFXStream (Apple M2 Pro)))
  ```

  Y aun asi Unity muere igual con "Unable to initialize the Unity Engine
  Graphics API". **Hipotesis descartada:** no es el driver de debajo, es que
  Unity rechaza ANGLE en guest y punto.

**Lo que si funciono.** Si Unity acepta ANGLE de host (swangle) y lo unico malo
de swangle era su backend de software, la jugada es cambiarle el backend. El SDK
del emulador ya trae kosmickrisp, el driver Vulkan sobre Metal de Mesa, en
`lib64/vulkan/libvulkan_kosmickrisp.dylib`. ANGLE carga su ICD desde
`lib64/gles_angle/vk_swiftshader_icd.json`, asi que basta reescribir ese fichero
para que apunte a kosmickrisp. El comando esta en
[Instalacion](#instalacion-una-sola-vez).

Resultado, mismo `-gpu swangle -no-snapshot-load` de siempre, a 720x1600:

```
30.0 FPS   (63 frames, 33.4 ms/frame)
30.0 FPS   (63 frames, 33.3 ms/frame)
30.0 FPS   (63 frames, 33.3 ms/frame)
ro.opengles.version = 196609
```

Los 30.0 clavados son el tope del propio juego, no del emulador: no hay mas que
sacar. **3.8x**, con ES 3.1, avatar visible, camara siguiendo, y el joystick
sincronizado (`/pos` 37.882787,-4.795906 contra `gps 37.882787,-4.795875`, los 3
metros son el jitter que mete el servidor).

Un intento anterior habia probado esto mismo apuntando el ICD a MoltenVK y
reventaba el emulador al arrancar. La diferencia es que kosmickrisp expone el
Vulkan 1.3 completo que ANGLE necesita y MoltenVK no.

**Como se mide.** `dumpsys SurfaceFlinger --latency` sobre la capa BLAST de
Unity:

```sh
ADB=~/Library/Android/sdk/platform-tools/adb
RAW=$($ADB shell dumpsys SurfaceFlinger --list | tr -d '\r' \
      | grep "SurfaceView\[com.nianticlabs" | grep BLAST | head -1)
NAME=$(echo "$RAW" | sed 's/^RequestedLayerState{//; s/ parentId=[0-9]*}$//')
$ADB shell "dumpsys SurfaceFlinger --latency '$NAME'"
```

Ojo: si hay un modal encima el juego deja de repintar y no salen muestras. Hay
que cerrarlo antes de medir.

# iPhone: por que no funciona

Archivado. El proyecto es solo Android por ahora; esto queda aqui para no volver
a investigar lo mismo cuando se retome.

El codigo de iOS se quito de `spoof.py` en el commit que anadio esta pagina.
Esta entero en el historial de git si hace falta recuperarlo.

## Resumen

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
El detalle de lo probado esta en el registro de abajo.


## Registro de lo probado

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

**Descartado con el log del propio movil: no es un problema de permisos.** Antes
de dar por buena la teoria de la deteccion habia que descartar lo aburrido, que
es que Pokemon GO no tuviera permiso de ubicacion o lo tuviera en precision
reducida. Capturando `pymobiledevice3 syslog live` mientras se abre el juego,
`locationd` registra al cliente asi:

```
Authorization = 4;                          (= Always)
"registration":"AllowedAlways"
InUseLevel = 5;
LocationTechnologiesInUse = (1, 10, 4, 6);
```

Permiso concedido y en precision completa. El unico `Denied` de toda la captura
es de otro servicio y despista:

```
Handling access request to kTCCServiceUserTracking, from Sub:{com.nianticlabs.pokemongo}
  ... ReqResult(Auth Right: Denied (User Consent), promptType: 1, DB Action:None)
```

`kTCCServiceUserTracking` es App Tracking Transparency, o sea publicidad e IDFA.
No tiene nada que ver con la ubicacion.

**Confirmado en el log: iOS marca la posicion y el juego la suelta.** En la misma
captura, `locationd` etiqueta cada fix como simulado y lo anuncia al sistema:

```
@ClxSimulated, Fix, 1, ll, <private>, <private>, acc, 5.00
LocationProvider,Sending through simulated location for <private>
CL: CLLocationController::onSimulatedNotification
```

Y el cliente de Niantic la recibe y deja de recibirla:

```
{"msg":"stopped receiving location information", "client":"icom.nianticlabs.pokemongo:"}
"oldArrowState":"ReceivingLocationInformation", "newArrowState":"RequestingLocationInformation"
```

Recibe y suelta. Eso es el error 12 visto desde dentro. Con el permiso descartado
por el propio log, la marca de simulacion es la unica explicacion que queda en
pie. Sigue siendo inferencia sobre el comportamiento de Niantic, no codigo suyo.

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


## Problemas conocidos del tunel

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


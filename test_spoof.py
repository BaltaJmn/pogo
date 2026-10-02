"""Comprobaciones de lo unico que puede romperse en silencio: el orden lon/lat
que pide `adb emu geo fix` y el motor de movimiento que ahora vive en el servidor."""
import asyncio

import spoof
from spoof import SIM, AdbEmulator, advance, meters, step


def test_geo_fix_manda_longitud_primero():
    argv = AdbEmulator("emulator-5554").argv(37.8859, -4.7658)
    assert argv[-4:] == ["geo", "fix", "-4.7658", "37.8859"], argv


def test_sin_serial_no_pone_el_flag():
    assert "-s" not in AdbEmulator("").argv(0.0, 0.0)


def reset(**kw):
    SIM.update(lat=37.885835, lon=-4.765513, dist=0.0, vx=0.0, vy=0.0, kmh=4.5,
               route=[], idx=0, dir=1, endmode="loop", walking=False)
    SIM.update(kw)


def test_joystick_anda_la_velocidad_pedida():
    reset(vx=1.0, vy=0.0, kmh=4.5)          # 1.25 m/s
    inicio = (SIM["lat"], SIM["lon"])
    for _ in range(8):
        assert step()
    d = meters(*inicio, SIM["lat"], SIM["lon"])
    assert abs(d - 10.0) < 0.05, d
    assert abs(SIM["lat"] - inicio[0]) < 1e-12, "al este no se cambia la latitud"


def test_joystick_a_medio_gas_anda_la_mitad():
    reset(vx=0.5, vy=0.0)
    inicio = (SIM["lat"], SIM["lon"])
    step()
    assert abs(meters(*inicio, SIM["lat"], SIM["lon"]) - 0.625) < 0.01


def test_joystick_en_reposo_no_reinyecta():
    reset(vx=0.01, vy=0.0)
    assert step() is False


def test_ruta_en_bucle_vuelve_al_primer_punto():
    a = {"lat": 37.885835, "lon": -4.765513}
    b = {"lat": 37.885835 + 10 / spoof.M, "lon": -4.765513}   # 10 m al norte
    reset(route=[a, b], walking=True, idx=1, endmode="loop")
    advance(25.0)                            # 10 hasta b, 10 de vuelta a a, 5 mas
    assert SIM["walking"], "en bucle no se para"
    assert SIM["dist"] == 25.0
    assert 4.9 < meters(a["lat"], a["lon"], SIM["lat"], SIM["lon"]) < 5.1


def test_ruta_en_modo_parar_se_para():
    a = {"lat": 37.885835, "lon": -4.765513}
    b = {"lat": 37.885835 + 10 / spoof.M, "lon": -4.765513}
    reset(route=[a, b], walking=True, idx=1, endmode="once")
    advance(50.0)
    assert not SIM["walking"]
    assert (SIM["lat"], SIM["lon"]) == (b["lat"], b["lon"])


def test_ruta_degenerada_no_cuelga():
    p = {"lat": 37.885835, "lon": -4.765513}
    reset(route=[p, dict(p)], walking=True, endmode="loop")
    advance(5.0)                             # dos puntos iguales, presupuesto sin gastar
    assert SIM["walking"]


def test_pausa_y_reanuda_desde_donde_iba():
    """Pausar es dejar de andar sin tocar `idx`. Si al reanudar se reenviara la
    ruta, el servidor lo pondria a 0 y te devolveria al primer punto."""
    a = {"lat": 37.885835, "lon": -4.765513}
    b = {"lat": 37.885835 + 20 / spoof.M, "lon": -4.765513}   # 20 m al norte
    c = {"lat": 37.885835 + 40 / spoof.M, "lon": -4.765513}
    reset(route=[a, b, c], walking=True, idx=1, endmode="once")
    advance(5.0)
    lat_pausa, idx_pausa = SIM["lat"], SIM["idx"]

    SIM["walking"] = False                   # pausa
    assert step() is False, "en pausa no se reinyecta"
    assert SIM["lat"] == lat_pausa, "en pausa no se mueve"

    SIM["walking"] = True                    # reanudar, sin tocar la ruta
    advance(5.0)
    assert SIM["idx"] == idx_pausa, "reanudar no puede cambiar de tramo"
    assert SIM["lat"] > lat_pausa, "sigue hacia el norte, no vuelve al punto 0"


class Grabadora:
    """Emulador de mentira: apunta los fix en vez de llamar a adb."""
    def __init__(self):
        self.fixes = []

    async def set(self, lat, lon):
        self.fixes.append((lat, lon))


def test_parado_repite_el_ultimo_fix_sin_jitter_nuevo():
    """Un emulador que arranca con el servidor ya en marcha tiene que recibir
    posicion aunque no te muevas, y quieto no puede temblar."""
    reset(jitter=True, loc=Grabadora(), fix=None)
    asyncio.run(spoof.tick())
    assert SIM["loc"].fixes == [], "sin fix previo no hay nada que repetir"
    asyncio.run(spoof.inject())
    asyncio.run(spoof.tick())
    asyncio.run(spoof.tick())
    a, b, c = SIM["loc"].fixes
    assert a == b == c, "parado se repite el mismo punto"


class Pantalla:
    """adb shell de mentira: apunta los comandos y se apaga a las n llamadas,
    que es como para el bucle infinito del autoclicker."""
    def __init__(self, n):
        self.cmds, self.n = [], n

    async def shell(self, *cmd):
        self.cmds.append(cmd)
        if len(self.cmds) > self.n:
            raise RuntimeError("emulador apagado")
        return "Physical size: 1080x2400\nOverride size: 720x1600\n"


def test_autoclicker_toca_el_centro_y_cada_tanto_mantiene():
    SIM["loc"] = Pantalla(1 + spoof.TOQUES + 1)
    asyncio.run(spoof.clicker())
    wm, *toques, larga, _ = SIM["loc"].cmds
    assert wm == ("wm", "size")
    assert toques == [("input", "tap", "360", "800")] * spoof.TOQUES, "centro del override"
    assert larga == ("input", "swipe", "360", "800", "360", "800", str(spoof.PULSACION_MS))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)

"""Comprobaciones de lo unico que puede romperse en silencio: el orden lon/lat
que pide `adb emu geo fix` y el motor de movimiento que ahora vive en el servidor."""
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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)

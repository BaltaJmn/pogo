"""Comprobacion del unico sitio donde es facil meter la pata: el orden lon/lat."""
from spoof import AdbEmulator


def test_geo_fix_manda_longitud_primero():
    argv = AdbEmulator("emulator-5554").argv(37.8859, -4.7658)
    assert argv[-4:] == ["geo", "fix", "-4.7658", "37.8859"], argv


def test_sin_serial_no_pone_el_flag():
    assert "-s" not in AdbEmulator("").argv(0.0, 0.0)


if __name__ == "__main__":
    test_geo_fix_manda_longitud_primero()
    test_sin_serial_no_pone_el_flag()
    print("ok")

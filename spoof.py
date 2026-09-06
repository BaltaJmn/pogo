#!/usr/bin/env python3
"""Joystick GPS y rutas para un emulador de Android.

Levanta una web local. El movimiento se calcula aqui, un fix por segundo, y la
web solo manda la intencion: hacia donde y a que velocidad. Antes el bucle vivia
en el navegador y Chrome lo estrangulaba al ocultar la pestaña, que es justo lo
que pasa mientras miras el juego.
"""
from __future__ import annotations

import argparse
import asyncio
import math
import random
import shutil
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

HERE = Path(__file__).resolve().parent
ADB = shutil.which("adb") or str(Path.home() / "Library/Android/sdk/platform-tools/adb")
M = 111320.0  # metros por grado de latitud
SIM = {
    "loc": None, "lat": None, "lon": None, "dist": 0.0,
    "vx": 0.0, "vy": 0.0,          # joystick normalizado, x=este y=norte
    "kmh": 4.5, "jitter": True,
    "route": [], "idx": 0, "dir": 1, "endmode": "loop", "walking": False,
}
# Claves que la web puede tocar. Lista blanca: el resto del estado es nuestro.
INTENT = ("vx", "vy", "kmh", "jitter", "route", "endmode", "walking")
LOCK = asyncio.Lock()


class AdbEmulator:
    """Inyecta la posicion en un emulador de Android con `adb emu geo fix`.

    No hace falta root ni app de mock location: alimenta el GPS emulado, que para
    el sistema es el de verdad.
    """

    def __init__(self, serial: str) -> None:
        self.serial = serial

    def argv(self, lat: float, lon: float) -> list[str]:
        # geo fix quiere LONGITUD primero. Invertirlo te manda al otro lado del mundo.
        prefix = [ADB] + (["-s", self.serial] if self.serial else [])
        return prefix + ["emu", "geo", "fix", str(lon), str(lat)]

    async def set(self, lat: float, lon: float) -> None:
        proc = await asyncio.create_subprocess_exec(
            *self.argv(lat, lon),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        out, _ = await proc.communicate()
        if proc.returncode:
            raise RuntimeError(out.decode().strip() or f"adb salio con {proc.returncode}")

    async def clear(self) -> None:
        pass  # el emulador no tiene GPS real al que volver


# --- movimiento --------------------------------------------------------


def shift(lat: float, lon: float, east: float, north: float) -> tuple[float, float]:
    return lat + north / M, lon + east / (M * math.cos(math.radians(lat)))


def meters(alat: float, alon: float, blat: float, blon: float) -> float:
    return math.hypot((blon - alon) * M * math.cos(math.radians(alat)), (blat - alat) * M)


def next_target() -> bool:
    n = SIM["idx"] + SIM["dir"]
    if 0 <= n < len(SIM["route"]):
        SIM["idx"] = n
        return True
    if SIM["endmode"] == "loop":
        SIM["idx"] = 0 if SIM["dir"] > 0 else len(SIM["route"]) - 1
        return True
    if SIM["endmode"] == "pingpong":
        SIM["dir"] *= -1
        SIM["idx"] = n + 2 * SIM["dir"]
        return 0 <= SIM["idx"] < len(SIM["route"])
    return False


def advance(budget: float) -> None:
    """Consume `budget` metros siguiendo la ruta. El guard corta rutas degeneradas
    con puntos repetidos, que si no dan vueltas sin gastar presupuesto."""
    for _ in range(500):
        if budget <= 1e-6:
            return
        t = SIM["route"][SIM["idx"]]
        d = meters(SIM["lat"], SIM["lon"], t["lat"], t["lon"])
        if d > budget:
            f = budget / d
            SIM["lat"] += (t["lat"] - SIM["lat"]) * f
            SIM["lon"] += (t["lon"] - SIM["lon"]) * f
            SIM["dist"] += budget
            return
        SIM["lat"], SIM["lon"] = t["lat"], t["lon"]
        SIM["dist"] += d
        budget -= d
        if not next_target():
            SIM["walking"] = False
            return


def step() -> bool:
    """Un segundo de movimiento. True si hay que reinyectar."""
    if SIM["lat"] is None:
        return False
    metros = SIM["kmh"] * 1000 / 3600
    if SIM["walking"] and len(SIM["route"]) > 1:
        advance(metros)
        return True
    m = math.hypot(SIM["vx"], SIM["vy"])
    if m <= 0.05:
        return False
    k = min(1.0, m) / m * metros
    SIM["lat"], SIM["lon"] = shift(SIM["lat"], SIM["lon"], SIM["vx"] * k, SIM["vy"] * k)
    SIM["dist"] += min(1.0, m) * metros
    return True


async def inject() -> None:
    lat, lon = SIM["lat"], SIM["lon"]
    if SIM["jitter"]:
        lat, lon = shift(lat, lon, random.uniform(-3, 3), random.uniform(-3, 3))
    async with LOCK:
        await SIM["loc"].set(lat, lon)


async def ticker() -> None:
    """Un fix por segundo, la cadencia de un GPS real. Sigue corriendo aunque
    cierres el navegador."""
    while True:
        await asyncio.sleep(1)
        try:
            if step():
                await inject()
        except Exception as e:  # una inyeccion fallida no puede matar el bucle
            print(f"tick: {e}")


# --- web ---------------------------------------------------------------


async def index(request):
    return FileResponse(HERE / "index.html")


async def pos(request):
    # `idx` es por donde va la ruta. La web lo necesita para saber si "Recorrer"
    # empieza de cero o reanuda una pausa.
    return JSONResponse({"lat": SIM["lat"], "lon": SIM["lon"], "dist": SIM["dist"],
                         "walking": SIM["walking"], "idx": SIM["idx"]})


def valid(lat, lon) -> bool:
    return -90 <= lat <= 90 and -180 <= lon <= 180


async def set_loc(request):
    """Teletransporte y/o cambio de intencion. La web manda solo lo que cambia."""
    body = await request.json()
    if "lat" in body:
        lat, lon = float(body["lat"]), float(body["lon"])
        if not valid(lat, lon):
            return JSONResponse({"ok": False, "error": "coordenadas fuera de rango"},
                                status_code=400)
        SIM["lat"], SIM["lon"] = lat, lon
        SIM["dist"] = 0.0
    if "route" in body:
        r = body["route"]
        if not all(valid(float(p["lat"]), float(p["lon"])) for p in r):
            return JSONResponse({"ok": False, "error": "ruta fuera de rango"}, status_code=400)
        body["route"] = [{"lat": float(p["lat"]), "lon": float(p["lon"])} for p in r]
        SIM["idx"], SIM["dir"] = 0, 1
    for k in INTENT:
        if k in body:
            SIM[k] = body[k]
    if SIM["lat"] is not None:
        await inject()
    return JSONResponse({"ok": True})


async def clear_loc(request):
    SIM.update(lat=None, lon=None, vx=0.0, vy=0.0, walking=False, dist=0.0)
    async with LOCK:
        await SIM["loc"].clear()
    return JSONResponse({"ok": True})


# --- emulador ----------------------------------------------------------

EMU_SH = HERE / "emulator.sh"
EMU = {"task": None, "log": []}


def emu_busy() -> bool:
    t = EMU["task"]
    return t is not None and not t.done()


async def emu_run(*args: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        str(EMU_SH), *args,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        # sesion propia: el emulador tiene que sobrevivir a que matemos el servidor
        start_new_session=True)
    out, _ = await proc.communicate()
    return proc.returncode, out.decode(errors="replace").strip()


async def emu_status(request):
    """Estado del emulador, parseado de `emulator.sh status` (clave=valor)."""
    code, out = await emu_run("status")
    st = dict(l.split("=", 1) for l in out.splitlines() if "=" in l and not l.startswith("["))
    st["starting"] = emu_busy()
    st["log"] = EMU["log"][-12:]
    if code:
        st["error"] = out
    return JSONResponse(st)


async def emu_start(request):
    """Arranca el emulador en segundo plano. El arranque tarda minutos, asi que
    devolvemos ya y la web sondea /emulator."""
    if emu_busy():
        return JSONResponse({"ok": False, "error": "ya se esta arrancando"}, status_code=409)

    async def job():
        EMU["log"] = ["arrancando..."]
        code, out = await emu_run("start")
        EMU["log"] = [l for l in out.splitlines() if l.strip()] or ["sin salida"]
        if code:
            EMU["log"].append(f"fallo (codigo {code})")

    EMU["task"] = asyncio.create_task(job())
    return JSONResponse({"ok": True})


app = Starlette(routes=[
    Route("/", index),
    Route("/pos", pos),
    Route("/loc", set_loc, methods=["POST"]),
    Route("/clear", clear_loc, methods=["POST"]),
    Route("/emulator", emu_status),
    Route("/emulator", emu_start, methods=["POST"]),
])


async def main() -> None:
    ap = argparse.ArgumentParser(description="Joystick GPS para un emulador de Android")
    ap.add_argument("serial", nargs="?", default="", metavar="SERIAL",
                    help="serial del emulador (p.ej. emulator-5554). Sin valor, "
                         "el unico dispositivo que vea adb")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    print(f"emulador android {args.serial or '(unico)'}")
    await serve(AdbEmulator(args.serial), args.port)


async def serve(loc, port: int) -> None:
    SIM["loc"] = loc
    print(f"\n  joystick -> http://127.0.0.1:{port}\n")
    task = asyncio.create_task(ticker())
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    try:
        await uvicorn.Server(config).serve()
    finally:
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())

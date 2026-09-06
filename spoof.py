#!/usr/bin/env python3
"""Joystick GPS y rutas para iPhone (iOS 17+) via pymobiledevice3.

Levanta una web local. El navegador calcula el movimiento y manda una
coordenada por segundo; aqui solo se inyecta en el movil.
"""
from __future__ import annotations

import argparse
import asyncio
import shutil
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

from pymobiledevice3.exceptions import AlreadyMountedError
from pymobiledevice3.remote.native_tunnel import establish_native_rsd
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
from pymobiledevice3.services.mobile_image_mounter import auto_mount

HERE = Path(__file__).resolve().parent
ADB = shutil.which("adb") or str(Path.home() / "Library/Android/sdk/platform-tools/adb")
SIM = {"loc": None, "lat": None, "lon": None}
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


async def index(request):
    return FileResponse(HERE / "index.html")


async def pos(request):
    return JSONResponse({"lat": SIM["lat"], "lon": SIM["lon"]})


async def set_loc(request):
    body = await request.json()
    lat, lon = float(body["lat"]), float(body["lon"])
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return JSONResponse({"ok": False, "error": "coordenadas fuera de rango"}, status_code=400)
    async with LOCK:
        await SIM["loc"].set(lat, lon)
    SIM["lat"], SIM["lon"] = lat, lon
    return JSONResponse({"ok": True})


async def clear_loc(request):
    async with LOCK:
        await SIM["loc"].clear()
    SIM["lat"] = SIM["lon"] = None
    return JSONResponse({"ok": True})


app = Starlette(routes=[
    Route("/", index),
    Route("/pos", pos),
    Route("/loc", set_loc, methods=["POST"]),
    Route("/clear", clear_loc, methods=["POST"]),
])


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--udid", help="UDID del movil, si tienes varios conectados")
    ap.add_argument("--rsd", nargs=2, metavar=("HOST", "PORT"),
                    help="usar un tunel ya abierto en vez de abrir el nativo")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--android", nargs="?", const="", metavar="SERIAL",
                    help="usar un emulador de Android en vez del iPhone. Sin valor, "
                         "el unico dispositivo que vea adb")
    args = ap.parse_args()

    if args.android is not None:
        print(f"emulador android {args.android or '(unico)'}")
        await serve(AdbEmulator(args.android), args.port)
        return

    if args.rsd:
        rsd = RemoteServiceDiscoveryService((args.rsd[0], int(args.rsd[1])))
        await rsd.connect()
    else:
        rsd = await establish_native_rsd(serial=args.udid)

    print(f"conectado a {rsd.udid} ({rsd.product_type})")

    # La DeveloperDiskImage se desmonta al reiniciar el movil. Sin ella no hay DVT.
    try:
        await auto_mount(rsd)
        print("DeveloperDiskImage montada")
    except AlreadyMountedError:
        pass
    async with DvtProvider(rsd) as dvt, LocationSimulation(dvt) as loc:
        await serve(loc, args.port)


async def serve(loc, port: int) -> None:
    SIM["loc"] = loc
    print(f"\n  joystick -> http://127.0.0.1:{port}\n")
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    await uvicorn.Server(config).serve()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Joystick GPS y rutas para iPhone (iOS 17+) via pymobiledevice3.

Levanta una web local. El navegador calcula el movimiento y manda una
coordenada por segundo; aqui solo se inyecta en el movil.
"""
from __future__ import annotations

import argparse
import asyncio
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
SIM = {"loc": None, "lat": None, "lon": None}
LOCK = asyncio.Lock()


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
    args = ap.parse_args()

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
        SIM["loc"] = loc
        print(f"\n  joystick -> http://127.0.0.1:{args.port}\n")
        config = uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning")
        await uvicorn.Server(config).serve()


if __name__ == "__main__":
    asyncio.run(main())

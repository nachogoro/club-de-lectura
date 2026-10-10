#!/usr/bin/env python3
"""Descarga los países de Natural Earth (escala 1:50m) y genera data/paises.geojson
con solo las propiedades necesarias y coordenadas redondeadas."""
import json
import urllib.request
from pathlib import Path

URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
       "master/geojson/ne_50m_admin_0_countries.geojson")
DESTINO = Path(__file__).resolve().parent.parent / "data" / "paises.geojson"
DECIMALES = 2


def redondear(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], DECIMALES), round(coords[1], DECIMALES)]
    out = [redondear(c) for c in coords]
    # quitar puntos consecutivos repetidos tras redondear
    if out and isinstance(out[0][0], (int, float)):
        limpio = [out[0]]
        for p in out[1:]:
            if p != limpio[-1]:
                limpio.append(p)
        if len(limpio) < 4:  # anillo degenerado: conservar original
            return out
        return limpio
    return out


def main():
    with urllib.request.urlopen(URL) as r:
        datos = json.load(r)
    features = []
    for f in datos["features"]:
        p = f["properties"]
        codigo = p["ADM0_A3"]
        if codigo == "ATA":  # Antártida: ocupa mucho y no es un país
            continue
        geom = f["geometry"]
        geom = {"type": geom["type"], "coordinates": redondear(geom["coordinates"])}
        features.append({
            "type": "Feature",
            "id": codigo,
            "properties": {"nombre": p.get("NAME_ES") or p["NAME"]},
            "geometry": geom,
        })
    features.sort(key=lambda f: f["properties"]["nombre"])
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps({"type": "FeatureCollection", "features": features},
                                  ensure_ascii=False, separators=(",", ":")),
                       encoding="utf-8")
    print(f"{len(features)} países → {DESTINO} ({DESTINO.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

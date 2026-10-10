#!/usr/bin/env python3
"""Gestión del mapa del club de lectura.

Ejemplos:
  python club.py member add Ana
  python club.py add japon "Kafka en la orilla" --author "Haruki Murakami" --attendees Ana,Luis --grade 7.5
  python club.py mark japon Marta
  python club.py unmark japon Luis
  python club.py grade japon 8
  python club.py status
  python club.py search guinea
"""
import argparse
import datetime as dt
import json
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CLUB = RAIZ / "data" / "club.json"
PAISES = RAIZ / "data" / "paises.geojson"


# ---------- utilidades ----------

def normalizar(texto):
    t = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(c for c in t if not unicodedata.combining(c)).strip()


def error(msg):
    sys.exit(f"Error: {msg}")


def cargar_paises():
    datos = json.loads(PAISES.read_text(encoding="utf-8"))
    return {f["id"]: f["properties"]["nombre"] for f in datos["features"]}


def cargar_club():
    if not CLUB.exists():
        return {"personas": [], "lecturas": []}
    return json.loads(CLUB.read_text(encoding="utf-8"))


def guardar_club(club):
    club["lecturas"].sort(key=lambda l: (l.get("fecha") or "", l["pais"]))
    CLUB.write_text(json.dumps(club, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolver_pais(texto, paises):
    """Acepta código ISO alpha-3 o nombre en español (sin importar tildes/mayúsculas)."""
    if texto.upper() in paises:
        return texto.upper()
    buscado = normalizar(texto)
    exactos = [c for c, n in paises.items() if normalizar(n) == buscado]
    if len(exactos) == 1:
        return exactos[0]
    parciales = [c for c, n in paises.items() if buscado in normalizar(n)]
    if len(parciales) == 1:
        return parciales[0]
    if not parciales:
        error(f"no encuentro el país «{texto}». Prueba: python club.py search <texto>")
    opciones = "\n".join(f"  {c}  {paises[c]}" for c in parciales)
    error(f"«{texto}» es ambiguo. Usa el código:\n{opciones}")


def resolver_personas(nombres, club):
    resultado = []
    por_norm = {normalizar(p): p for p in club["personas"]}
    for nombre in nombres:
        p = por_norm.get(normalizar(nombre))
        if p is None:
            error(f"«{nombre}» no está en el club. Añádela con: python club.py member add {nombre}")
        if p not in resultado:
            resultado.append(p)
    return resultado


def separar(lista):
    """Admite 'Ana,Luis' y 'Ana Luis'."""
    return [x.strip() for item in lista or [] for x in item.split(",") if x.strip()]


def elegir_lectura(club, codigo, libro, paises):
    lecturas = [l for l in club["lecturas"] if l["pais"] == codigo]
    if libro:
        lecturas = [l for l in lecturas if normalizar(libro) in normalizar(l["libro"])]
    if not lecturas:
        error(f"no hay ninguna lectura de {paises[codigo]}"
              + (f" con el libro «{libro}»" if libro else "")
              + ". Créala con: python club.py add ...")
    if len(lecturas) > 1 and not libro:
        print(f"Hay {len(lecturas)} lecturas de {paises[codigo]}; uso la más reciente "
              f"(«{lecturas[-1]['libro']}»). Usa --book para elegir otra.")
    return lecturas[-1]


def describir(l, paises):
    autor = f" — {l['autor']}" if l.get("autor") else ""
    asist = ", ".join(l["asistentes"]) or "(nadie)"
    nota = f"  {formatear_nota(l['nota'])}/10" if l.get("nota") is not None else ""
    return f"{l.get('fecha') or '????-??-??'}  {paises.get(l['pais'], l['pais'])}: «{l['libro']}»{autor}{nota}  [{asist}]"


def formatear_nota(n):
    return f"{n:g}".replace(".", ",")


def leer_nota(texto):
    try:
        n = float(str(texto).replace(",", "."))
    except ValueError:
        error(f"la nota debe ser un número entre 0 y 10 (recibido «{texto}»)")
    if not 0 <= n <= 10:
        error("la nota debe estar entre 0 y 10")
    return int(n) if n == int(n) else round(n, 2)


# ---------- comandos ----------

def cmd_persona(a, club, paises):
    nombres = separar(a.nombres)
    if a.accion == "add":
        for n in nombres:
            if normalizar(n) in {normalizar(p) for p in club["personas"]}:
                print(f"{n} ya estaba en el club")
            else:
                club["personas"].append(n)
                print(f"Añadida: {n}")
    else:
        for n in resolver_personas(nombres, club):
            club["personas"].remove(n)
            for l in club["lecturas"]:
                if n in l["asistentes"]:
                    l["asistentes"].remove(n)
            print(f"Quitada: {n} (y de todas sus lecturas)")
    return True


def cmd_leer(a, club, paises):
    codigo = resolver_pais(a.pais, paises)
    fecha = a.fecha or dt.date.today().isoformat()
    try:
        dt.date.fromisoformat(fecha)
    except ValueError:
        error("la fecha debe tener formato AAAA-MM-DD")
    asistentes = club["personas"][:] if a.todos else resolver_personas(separar(a.asistentes), club)
    asistentes.sort(key=club["personas"].index)
    if not asistentes:
        print("Aviso: lectura sin asistentes. Añádelos con: python club.py mark <país> <personas>")
    lectura = {"pais": codigo, "libro": a.libro, "autor": a.autor or "",
               "fecha": fecha, "asistentes": asistentes}
    if a.nota is not None:
        lectura["nota"] = leer_nota(a.nota)
    club["lecturas"].append(lectura)
    print("Añadida: " + describir(lectura, paises))
    return True


def cmd_marcar(a, club, paises, marcar=True):
    codigo = resolver_pais(a.pais, paises)
    lectura = elegir_lectura(club, codigo, a.libro, paises)
    for p in resolver_personas(separar(a.personas), club):
        if marcar and p not in lectura["asistentes"]:
            lectura["asistentes"].append(p)
        elif not marcar and p in lectura["asistentes"]:
            lectura["asistentes"].remove(p)
    lectura["asistentes"].sort(key=club["personas"].index)
    print(describir(lectura, paises))
    return True


def cmd_nota(a, club, paises):
    codigo = resolver_pais(a.pais, paises)
    lectura = elegir_lectura(club, codigo, a.libro, paises)
    if a.valor.lower() in ("remove", "none", "-"):
        lectura.pop("nota", None)
    else:
        lectura["nota"] = leer_nota(a.valor)
    print(describir(lectura, paises))
    return True


def cmd_borrar(a, club, paises):
    codigo = resolver_pais(a.pais, paises)
    lectura = elegir_lectura(club, codigo, a.libro, paises)
    club["lecturas"].remove(lectura)
    print("Borrada: " + describir(lectura, paises))
    return True


def cmd_estado(a, club, paises):
    personas = resolver_personas(separar(a.personas), club) if a.personas else None
    if not personas:
        print(f"Lecturas ({len(club['lecturas'])}):")
        for l in club["lecturas"]:
            print("  " + describir(l, paises))
        total = {l["pais"] for l in club["lecturas"]}
        notas = [l["nota"] for l in club["lecturas"] if l.get("nota") is not None]
        media = f" · nota media {formatear_nota(round(sum(notas) / len(notas), 2))}/10" if notas else ""
        print(f"\nClub: {len(total)} países{media}")
        personas = club["personas"]
    for p in personas:
        suyos = sorted({paises[l["pais"]] for l in club["lecturas"] if p in l["asistentes"]})
        print(f"{p}: {len(suyos)} {'país' if len(suyos) == 1 else 'países'}" + (f" — {', '.join(suyos)}" if suyos else ""))
    return False


def cmd_buscar(a, club, paises):
    buscado = normalizar(a.texto)
    for c, n in sorted(paises.items(), key=lambda x: x[1]):
        if buscado in normalizar(n) or buscado == c.casefold():
            print(f"{c}  {n}")
    return False


def main():
    ap = argparse.ArgumentParser(description="Mapa del club de lectura",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n", 2)[2])
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("member", help="añadir o quitar miembros del club")
    s.add_argument("accion", metavar="{add,remove}", choices=["add", "remove"])
    s.add_argument("nombres", metavar="names", nargs="+")
    s.set_defaults(f=cmd_persona)

    s = sub.add_parser("add", help="registrar la lectura de un país")
    s.add_argument("pais", metavar="country", help="código ISO (JPN) o nombre (japon)")
    s.add_argument("libro", metavar="book")
    s.add_argument("--author", dest="autor")
    s.add_argument("--date", dest="fecha", help="AAAA-MM-DD (por defecto, hoy)")
    s.add_argument("--grade", dest="nota", help="nota media del club, de 0 a 10")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--attendees", dest="asistentes", nargs="+", help="Ana,Luis o Ana Luis")
    g.add_argument("--all", dest="todos", action="store_true", help="asistió todo el club")
    s.set_defaults(f=cmd_leer)

    for nombre, ayuda, marcar in [("mark", "añadir asistentes a una lectura", True),
                                  ("unmark", "quitar asistentes de una lectura", False)]:
        s = sub.add_parser(nombre, help=ayuda)
        s.add_argument("pais", metavar="country")
        s.add_argument("personas", metavar="names", nargs="+")
        s.add_argument("--book", dest="libro", help="para elegir si hay varias lecturas del país")
        s.set_defaults(f=lambda a, c, p, m=marcar: cmd_marcar(a, c, p, m))

    s = sub.add_parser("grade", help="poner o cambiar la nota media de una lectura")
    s.add_argument("pais", metavar="country")
    s.add_argument("valor", metavar="value", help="de 0 a 10 (admite decimales: 7.5 o 7,5), o «remove»")
    s.add_argument("--book", dest="libro", help="para elegir si hay varias lecturas del país")
    s.set_defaults(f=cmd_nota)

    s = sub.add_parser("delete", help="eliminar una lectura")
    s.add_argument("pais", metavar="country")
    s.add_argument("--book", dest="libro")
    s.set_defaults(f=cmd_borrar)

    s = sub.add_parser("status", help="resumen de lecturas y países por persona")
    s.add_argument("personas", metavar="names", nargs="*")
    s.set_defaults(f=cmd_estado)

    s = sub.add_parser("search", help="buscar el código de un país")
    s.add_argument("texto", metavar="text")
    s.set_defaults(f=cmd_buscar)

    a = ap.parse_args()
    club = cargar_club()
    if a.f(a, club, cargar_paises()):
        guardar_club(club)


if __name__ == "__main__":
    main()

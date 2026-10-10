# La vuelta al mundo en libros

Mapa interactivo del club de lectura: un libro por país, con vista del club entero y de cada persona. En la vista del club se muestran también las notas medias de cada libro.

## Estructura

- `index.html`: el mapa (lo que sirve GitHub Pages).
- `data/club.json`: personas y lecturas. Se edita con `club.py`, aunque también se puede tocar a mano.
- `data/paises.geojson`: fronteras (Natural Earth 1:50m). Se regenera con `python herramientas/generar_paises.py`.
- `club.py`: script para gestionar los datos (solo necesita Python 3, sin dependencias).

## Uso del script

Los países se indican por nombre en español (sin importar tildes ni mayúsculas) o por su código ISO de tres letras.

```bash
# Miembros del club
python club.py persona añadir Ana Luis Marta
python club.py persona quitar Luis

# Registrar una reunión (fecha por defecto: hoy)
python club.py leer japon "Kafka en la orilla" --autor "Haruki Murakami" --fecha 2026-01-20 --asistentes Ana,Marta
python club.py leer nigeria "Todo se desmorona" --autor "Chinua Achebe" --todos

# Nota media del club (0 a 10, admite decimales)
python club.py leer peru "La ciudad y los perros" --autor "Mario Vargas Llosa" --nota 8 --todos
python club.py nota croacia 5
python club.py nota croacia quitar

# Corregir la asistencia
python club.py marcar japon Luis
python club.py desmarcar japon Marta

# Borrar una lectura
python club.py borrar japon

# Consultar
python club.py estado          # todo
python club.py estado Ana      # una persona
python club.py buscar guinea   # códigos de países que coinciden
```

Si un país tiene varias lecturas, `marcar`, `desmarcar`, `nota` y `borrar` actúan sobre la más reciente; usa `--libro "título"` para elegir otra.

## Publicar en GitHub Pages

```bash
git init && git add . && git commit -m "Mapa del club"
git branch -M main
git remote add origin git@github.com:USUARIO/mapa-libros.git
git push -u origin main
```

En GitHub: **Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)`**.
El mapa quedará en `https://USUARIO.github.io/mapa-libros/`.

Después de cada reunión:

```bash
python club.py leer ...
git commit -am "Lectura: Japón" && git push
```

Para enlazar directamente la vista de una persona: `https://USUARIO.github.io/mapa-libros/#Ana`.

## Ver en local

`index.html` carga los datos con `fetch`, así que no funciona abriéndolo como fichero. Usa:

```bash
python -m http.server
# y abre http://localhost:8000
```

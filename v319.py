# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.19)

NUEVO: la zona «M-30 (aprox.)» viene ya dibujada en el mapa de zonas, como ZONA MEDIA (todo lo de dentro de la M-30).
  - Se anade UNA sola vez (al arrancar la app, o al abrir los ajustes de Bolt). Despues se puede mover, editar o borrar como cualquier otra y no vuelve a salir.
  - Tus zonas dibujadas siguen mandando como siempre: si un punto cae en varias, gana la alta, luego la media y luego la baja. Fuera de la M-30 y de tus zonas sigue la zona por defecto.
  - El contorno esta hecho a mano (no he podido bajar el trazado real): puede fallar varios cientos de metros en los bordes.
Solo cambia www/index.html (nada de Java). Se puede pasar mas de una vez (la segunda no hace nada). Todo o nada: si falta cualquier ancla NO se cambia nada.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "eNqFVNtu2zgU/JWzebDFQGEkyzfFYIAE24cCdRAgXWCxjhHQEu1oI5FaknJru/6ifkAf+pYvW0qUFDsNUkCw6NGZOcPhZTY72QpOYXoWeBcQiT"
    "hZiRMXTqja8AiWBY90IjikgsbOqqAyRrvy8/npOvDDsyzwTs/v+fkprAPsh/D8A1IKleDz91ISHJpL8RWj55/gaBELowQxMw/XshqltjcQS8tY"
    "nFAE64RxBhsKcbIo/qUxdeGvmytQwpSv2RbDHYO8YIZv6jWVIGAhpDSDSGQCooKm/xUJM7iWFDbABawLlq4ZUFA0TSSG0ngkuNIwDbyHm6vpB9"
    "I9stydHBbcfr4js1nfw/3xyHPPAjwMPW/uWmRgkdG4QczIIm3NsEaG/QYZDC0yaFn9WmfQa5Cgb5F+W9P7BfEbVqvs1crDRicIw1d+grDWGYUN"
    "Mq4djl+QWid8QezcR9641Qks4g/b7j2L9PxB47BBeg3Sa5CgQYIGGbRpNEjYJlYjgd+m6tc1bRrDsPbTskbDGmlZ41rHOJ3PzSq329zs5z8FZw"
    "7apUxDTJY0VWyi5WYXk1RENL3TQtIVwyumP2qWOd08jh4Mq4sIIV2/u4+ojh4dhnb7kpUsnXjR6cQLrJjWCV+poz/YMO+Y2cUxiomWBTugS6YL"
    "ySHeH9ubUvlk7JXiR4bUa0OucYNe2XmzddV4cosVXbMb8cU5JB02V6baHATT/J4DlHLlG8DMsY0N1a5tbva7PUJbco2j5arTqV7YnHV2OK5+1M"
    "Ro/XFljvEGJ6p6O9s3NU3dFiuRMYeSS9rpUMxN/s05Rt++bXHK+Eo/XpLp1d//oF2b3ORQbW/Vtrjg6jFZamfHLxoR9+mim3XdXKuL+vjjjOZO"
    "Ti5n+cxspHzmz+doj2pHtWyVZYm8hPiqoXneu1vnLhzdyIpli/JaoylEVK6oLG9fgGtcsprFu8YLqhhR3BhsZ1hbMf1u8UKk+pMhkJI1sRJ2XU"
    "wwpF3Zyvl70uV3u97IbKTPScZEoR0HkctqR+ZMqkRpB2H9yLhTh46wzaIq2x9tL9ezmr+1fM/f6lclV5LeaxEMPNPlZD7/H055G18="
)
SHA = "4e294a08407827290a09e6804663f0095435706705fa734f3171a88a544f0915"
MARK = '/*v319-m30*/'

def fin(msg):
    raise SystemExit(msg)

if not os.path.exists('www/index.html'):
    try:
        os.chdir('/workspaces/PORTAL_CONDUCTOR/portal')
    except OSError:
        pass
p = 'www/index.html'
if not os.path.exists(p):
    fin('ERROR: no encuentro www/index.html (ejecuta el parche desde la carpeta portal). No se ha cambiado nada.')
try:
    raw = zlib.decompress(base64.b64decode(PAYLOAD)).decode('utf-8')
    ok_sum = hashlib.sha256(raw.encode('utf-8')).hexdigest() == SHA
    edits = json.loads(raw) if ok_sum else None
except Exception:
    ok_sum = False
if not ok_sum:
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v319.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.19 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    faltan = [n for n, old, new in edits if orig.count(new) != 1]
    if faltan:
        fin('ERROR: la v3.19 esta a medias (falta: ' + ', '.join(faltan) + '). No se ha cambiado nada.')
    print('v3.19 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)

s = orig
for n, old, new in edits:
    c = s.count(old)
    if c != 1:
        fin('ERROR: ' + n + (' no esta' if c == 0 else ' esta repetido (' + str(c) + ' veces)') + ' en la pagina. No se ha cambiado nada (la app no es la version esperada).')
    s = s.replace(old, new, 1)
if s.count(MARK) != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir='www', suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('pagina: actualizada')
print('v3.19 aplicado: la zona «M-30 (aprox.)» (zona media) viene dibujada en el mapa de zonas')

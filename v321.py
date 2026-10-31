# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.21)

NUEVO: APLICACION PRIORITARIA a elegir (Bolt, Uber o Cabify).
  - En Control Horario, debajo de «Ahora trabajo con», aparece «Aplicacion prioritaria»: Bolt (por defecto), Uber o Cabify.
  - El bloque principal («Solo Bolt») pasa a llamarse con la app elegida («Solo Uber», «Solo Cabify») en el diario, el semanal y el mensual,
    igual que los botones del selector, el desglose de «Todas las apps», la tabla semanal y el nombre de cada tramo.
  - Por dentro no cambia nada: las horas, los km, las horas prioritarias y la meta semanal se calculan igual que en la v3.18, solo cambia el nombre.
    Si cambias la app prioritaria, lo que ya tenias como prioritario pasa a llamarse con el nombre nuevo.
Necesita la v3.18 (pasala antes). Solo cambia www/index.html (nada de Java). Se puede pasar mas de una vez. Todo o nada: si falta cualquier ancla NO se cambia nada.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "eNqlVc1y2zYQfpWt7JpkLFM/Tt2YlORJMp3pIU0yTTs9WJ4xSIISKhJgAEiRSustes9M7zl1Or3XL9RH6IKgJEq1Z/pzkbDA7ofdbz8sr69b6Z"
    "zHTHCqWm2oDI0WkKJ4RSKauUuvlFTPJYflycnSx/3hcOgIPaXSuXLeaEmUcVZO4LwQmXbWBqbzZHHe750VkoknnTHvdGBx7vd78Mfv6JuxmJgb"
    "wRxLpolkJAATDG4hJCQ0pbEWXhu+j6gEAS9JxNKVD+9EJiAmecQI0Axev/nmxbdfQYxIaL2fU1AUFtQYUSaMjRdgbQXJQrDAXEsBik2ML6M8Ec"
    "Y5ZyoX4GZCAVaT419CgXBNFcRzDCEc70CPRrqeP+Zbqsz+a5JT1yszqoEPLRGhlquSD90kOjlJIl9RrRmfqD3DN7HPi8K7u6vZi4mOpy71ynXN"
    "Ojd0GyKcu7tqbdlwrviG8EYqiPvWIrrcK8ccMNx9DMHbQoTGk6XuZ43UvMZ6WK43LrtiEYk/WIw58Gz2VdRDLjxUZIEgocQuUPlSmM5kaI/5+o"
    "Datyyefa1zPKwKqmm5HSRsAUqvMjoct3IiJ4yfaVEEvW6xHLdGA5WTLNs6JEwVGVkFKIx4FsYoJBkcXabR0/hZmOLlZx8om0x18GW3G9ZgkdBa"
    "5MEXFdzzWrX3v+7JFlVDUC1/F5wXDDpVBpgIzVDOwBJMoy5/3ALB4ynhE5Nbo2l6ypS/INmceuizSf4DS/QUC+t+HhYkSZDIoNcrlmEkJHJ3Jk"
    "nC5iro9c0WiWcTKeY8CY66z/pPz6NNsZSkF2laxwQYDkpkLIGj/uVlkqYXF5YHxX6iQQ+LPqQFSTgur61e2lZO7Y2SbvycoOKGo9uBKKrGVTVg"
    "6scl9tP8oih20rlywLJCExwbznpk3AYdGzu69fwfBeOu43i4aR3/TT8bYrDNe8cA22QHh2rjWsFUmLllWrYioCm//4Tm4StXUBCFr59AlhFExf"
    "FC1P0nf9vaDmpwdHug2f8wOXfMmOnZu2nDdQvltz8izVxF1aAOZ1Y0Pwg5M6JxItMTFMzINGfQieYoXD76B/7HZePmZqBNwVIv5ONIthgDtStn"
    "i2Pp2ZD0v0BsortJsG6g1nTZB6hFQqoP2Z8ff/4NvjNW1W+DCW71jTkFYa7xHvXaY6Xp3q9uyqmWOAtMuBVlTbtdN7YP2N2e95sJ4yMUNpOPv9"
    "gPnEHb39kDwqPzCoALTWCWG9dX+M2a5eazVVW4Miux5XLfwzndgZ06D/haPjWJ8M0omhNuS9XTuk5cbDYOKrQnvZubvwAjQNxV"
)
SHA = "23adcc80d5798577c6704e34c825138b61f13c15a032efff901118d8cb081974"
MARK = '/*v321-prio*/'

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v321.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.21 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    quedan = [n for n, old, new, c in edits if n != 'funciones' and orig.count(old) != 0]
    if quedan or orig.count('function prioName()') != 1:
        fin('ERROR: la v3.21 esta a medias (falta: ' + ', '.join(quedan or ['funciones']) + '). No se ha cambiado nada.')
    print('v3.21 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)
if orig.count('/*v318-apps*/') != 1:
    fin('ERROR: falta la v3.18 (pasa antes v318.py). No se ha cambiado nada.')

s = orig
for n, old, new, c in edits:
    k = s.count(old)
    if k != c:
        fin('ERROR: ' + n + ' no sale ' + str(c) + ' vez/veces en la pagina sino ' + str(k) + ' (la app no es la version esperada). No se ha cambiado nada.')
    s = s.replace(old, new)
if s.count(MARK) != 1 or s.count('function prioName()') != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir='www', suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('pagina: actualizada')
print('v3.21 aplicado: aplicacion prioritaria a elegir (Bolt, Uber o Cabify) en Control Horario')

# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.26)

NUEVO: Free Now y Pide Taxi como plataformas, igual que Privados (el importe va entero, sin comision de la app).
  - Calculadora: segunda fila de cuatro cuadros iguales: Aeropuerto, Free Now (rosa), Pide Taxi (amarillo), Cancelaciones.
  - Totales del dia, Facturacion (cargar importes y editar), Informe (pantalla e imagen) y Nomina: ahora cuentan las dos apps.
    Los resumenes por aplicacion pasan a tres columnas y dos filas (Bolt, Uber, Cabify / Privados, Free Now, Pide Taxi).
  - Control: Free Now (rosa) y Pide Taxi (amarillo) se pueden elegir como aplicacion prioritaria.
  - Los totales de las cuatro apps de siempre no cambian.
NO lee ofertas ni el importe al terminar el viaje de estas dos apps (eso necesitaria capturas de sus pantallas y tocar el Java).
Solo cambia www/index.html (nada de Java). Necesita la v3.24 (restyling). Se puede pasar mas de una vez. Todo o nada.
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "atJsfb2h2XZ9iGnr+rCjsb7KLYHe1dX/AWvopzk="
)
SHA = "9fc462b3bdf317b5aef6bd7da1a184817822f9565e05e9cd95e390b8675e6f3c"
MARK = '/*v326-plat*/'

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v326.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.26 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    quedan = [n for n, old, new, c in edits if ((orig.count(new) not in (c if isinstance(c, list) else [c])) if old in new else (orig.count(old) != 0))]
    if quedan:
        fin('ERROR: la v3.26 esta a medias (falta: ' + ', '.join(quedan) + '). No se ha cambiado nada.')
    print('v3.26 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)
if orig.count('/*v324-lt*/') != 1:
    fin('ERROR: falta la v3.24 (restyling claro). Pasa primero v324.py. No se ha cambiado nada.')
if orig.count('function decorateCalc(){') != 1:
    fin('ERROR: no encuentro la pantalla principal con Cancelaciones (v3.14). No se ha cambiado nada.')

s = orig
for n, old, new, c in edits:
    k = s.count(old)
    cs = c if isinstance(c, list) else [c]
    if k not in cs:
        fin('ERROR: ' + n + ' no sale ' + ' o '.join(str(x) for x in cs) + ' vez/veces en la pagina sino ' + str(k) + ' (la app no es la version esperada). No se ha cambiado nada.')
    s = s.replace(old, new)
if s.count(MARK) != 1 or s.count('id="v326-style"') != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir='www', suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('pagina: actualizada')
print('v3.26 aplicado: Free Now y Pide Taxi como plataformas (calculadora, facturacion, informe, nomina y control)')

# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.27)

ARREGLO: Cancelaciones con Free Now y Pide Taxi.
  - La ventana de Cancelaciones ofrece Uber, Bolt, Cabify, Free Now y Pide Taxi (antes solo las tres primeras).
  - Las cancelaciones de Free Now / Pide Taxi suman a su cuadro del dia, a Facturacion (dia, semana, mes), Informe y Nomina, como las de Uber.
  - Ayuda, Jenny e Informacion al dia: Free Now y Pide Taxi, cancelaciones, aplicacion prioritaria, Madrid hoy, Tema, aeropuerto verde,
    y la version que se ve en Informacion (decia v3.7) ahora dice v3.27.
NUEVO: Tema claro / oscuro en Ajustes (Automatico, Claro, Oscuro).
  - Automatico: claro de dia y oscuro de noche segun la salida y puesta del sol en Madrid (se calcula en el movil, sin internet). Cambia solo.
  - Claro u Oscuro: fijo. Se guarda en este aparato. Afecta a Calculadora, Control, Facturacion e Informe (Ajustes, el menu y Madrid hoy ya eran oscuros).
Solo cambia www/index.html (nada de Java). Necesita la v3.26. Se puede pasar mas de una vez. Todo o nada.
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "ef/jdmsGGc"
)
SHA = "1ccf55f64365667fd1e5f48afce5cb0052c80c3c9fff46a1b564c6ab0050488f"
MARK = '/*v327-theme*/'

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v327.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.27 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    quedan = [n for n, old, new, c in edits if ((orig.count(new) not in (c if isinstance(c, list) else [c])) if old in new else (orig.count(old) != 0))]
    if quedan:
        fin('ERROR: la v3.27 esta a medias (falta: ' + ', '.join(quedan) + '). No se ha cambiado nada.')
    print('v3.27 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)
if orig.count('/*v326-plat*/') != 1:
    fin('ERROR: falta la v3.26 (Free Now y Pide Taxi). Pasa primero v326.py. No se ha cambiado nada.')
if orig.count('function decorateCalc(){') != 1 or orig.count('function ltSet(on){') != 1:
    fin('ERROR: no encuentro la pantalla principal con Cancelaciones o el restyling (v3.24). No se ha cambiado nada.')

s = orig
for n, old, new, c in edits:
    k = s.count(old)
    cs = c if isinstance(c, list) else [c]
    if k not in cs:
        fin('ERROR: ' + n + ' no sale ' + ' o '.join(str(x) for x in cs) + ' vez/veces en la pagina sino ' + str(k) + ' (la app no es la version esperada). No se ha cambiado nada.')
    s = s.replace(old, new)
if s.count(MARK) != 1 or s.count('id="v327-style"') != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir='www', suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('pagina: actualizada')
print('v3.27 aplicado: cancelaciones con Free Now y Pide Taxi, y tema claro/oscuro/automatico en Ajustes')

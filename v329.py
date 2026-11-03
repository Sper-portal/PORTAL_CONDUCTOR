# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.29)

CAMBIO: el boton flotante (la burbuja sobre Bolt, Uber y Cabify).
  - Ya no parpadea: antes se quitaba y se ponia cada vez que Android cambiaba la ventana activa (pasa muchas veces por segundo).
    Ahora, si la ventana vuelve a Bolt/Uber/Cabify en menos de 0,8 segundos, la burbuja ni se entera. Aparece suave (fundido de un cuarto de segundo).
  - Imagen de la app dentro de un circulo, con un aro luminoso por fuera que se agranda y se encoge despacio (1,4 segundos cada vez), como la de Bolt.
  - Si el movil tiene las animaciones desactivadas (ahorro de bateria), el aro se queda quieto.
  - La burbuja es un poco mas grande en pantalla (el aro necesita sitio) pero el circulo con el icono mide lo mismo y queda donde la dejaste.
Solo cambia ScreenReaderService.java (nada de www/index.html). Hay que volver a compilar el APK. Se puede pasar mas de una vez. Todo o nada.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "ba93198328b5df7ab581fd86dd7cd2c60dedce2bfc2d200272658f017788a28c"
MARK = '/*v329-bub*/'

def fin(msg):
    raise SystemExit(msg)

if not os.path.exists('www/index.html'):
    try:
        os.chdir('/workspaces/PORTAL_CONDUCTOR/portal')
    except OSError:
        pass
try:
    raw = zlib.decompress(base64.b64decode(PAYLOAD)).decode('utf-8')
    ok_sum = hashlib.sha256(raw.encode('utf-8')).hexdigest() == SHA
    edits = json.loads(raw) if ok_sum else None
except Exception:
    ok_sum = False
if not ok_sum:
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v329.py. No se ha cambiado nada.')

f = list(edits)[0]
if not os.path.exists(f):
    fin('ERROR: no encuentro ' + f + ' (ejecuta el parche desde la carpeta portal). No se ha cambiado nada.')
with open(f, encoding='utf-8', newline='') as fh:
    orig = fh.read()
if '\r\n' in orig:
    fin('ERROR: ' + f + ' tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.29 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    for n, old, new in edits[f]:
        if orig.count(new) != 1:
            fin('ERROR: la v3.29 esta a medias (falta: ' + n + '). No se ha cambiado nada.')
    print('v3.29 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)

s = orig
for n, old, new in edits[f]:
    c = s.count(old)
    if c != 1:
        fin('ERROR: ' + n + (' no esta' if c == 0 else ' esta repetido (' + str(c) + ' veces)') + ' en ' + f + '. No se ha cambiado nada (la app no es la version esperada).')
    s = s.replace(old, new, 1)
if s.count(MARK) != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir=os.path.dirname(f) or '.', suffix='.tmp')
os.close(fd)
try:
    with open(tmp, 'w', encoding='utf-8', newline='') as fh:
        fh.write(s)
    os.replace(tmp, f)
except Exception as e:
    try: os.remove(tmp)
    except OSError: pass
    fin('ERROR escribiendo: ' + str(e) + '. No se ha cambiado nada.')
print('burbuja: actualizada')
print('v3.29 aplicado: la burbuja ya no parpadea y tiene un aro luminoso que se agranda y se encoge (hay que volver a compilar la APK)')

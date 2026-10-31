# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.18)

NUEVO: la jornada separa Bolt y otras apps.
  - Selector «Ahora trabajo con: Bolt / Otras apps» en Control Horario. Se puede cambiar con la jornada en marcha (cada cambio parte el tiempo y los km del GPS).
  - Control Horario: en el diario, semanal y mensual hay dos bloques: «Solo Bolt» (horas prioritarias, no prioritarias y total, solo de Bolt)
    y «Todas las apps (Bolt + otras)» con el total, y el desglose de Bolt y de otras apps (horas y km del GPS).
  - Pantalla principal, facturacion por hora y por km, informes: siguen usando TODAS las horas y TODOS los km (no cambian).
  - Los tramos que ya tenias cuentan como Bolt. Cada tramo guardado tiene un boton para pasarlo de Bolt a otras apps y al reves.
Solo cambia www/index.html (nada de Java). Se puede pasar mas de una vez (la segunda no hace nada). Todo o nada: si falta cualquier ancla NO se cambia nada.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "c7d0f2a7f9a91840921a44c7beda8fbd0977eee58f94e82ac80626d4c4f8df24"
MARK = '/*v318-apps*/'

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v318.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.18 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    # si la v3.21 (aplicacion prioritaria) ya esta puesta, esta ha cambiado a proposito algunos textos de la v3.18: no se comprueban uno a uno
    if '/*v321-prio*/' in orig:
        print('v3.18 ya aplicado: no hay nada que cambiar.')
        raise SystemExit(0)
    # los estilos se comprueban por su id: otro parche (v3.16) puede insertar su bloque justo antes y cambiar lo que hay al lado
    faltan = [n for n, old, new in edits if (orig.count('<style id="v318-style">') != 1 if n == 'estilos' else orig.count(new) != 1)]
    if faltan:
        fin('ERROR: la v3.18 esta a medias (falta: ' + ', '.join(faltan) + '). No se ha cambiado nada.')
    print('v3.18 ya aplicado: no hay nada que cambiar.')
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
print('v3.18 aplicado: Control Horario con dos bloques (solo Bolt / todas las apps) y selector «Ahora trabajo con»')

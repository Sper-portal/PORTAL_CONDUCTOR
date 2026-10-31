# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.22)

NUEVO: Control Horario mas visual.
  - Los bloques «Todas las apps (... + otras)» (diario, semanal y mensual) pasan a CIRCULOS en gris neon, como los de horas prioritarias:
    total de horas, km del dia, la app prioritaria y otras apps (en el diario son 4 circulos; en el semanal y el mensual, 3).
  - Los tramos del dia (la nota, «Anadir tramo manual» y la lista de tramos) van dentro de una ventana que se esconde («Tramos del dia»).
  - La tabla de la semana (prior., no prior., app prioritaria y todas) es mas llamativa (colores neon) y va en otra ventana que se esconde.
    Las ventanas empiezan cerradas y recuerdan si las dejaste abiertas.
Necesita la v3.18 y la v3.21 (pasalas antes). Solo cambia www/index.html (nada de Java). Se puede pasar mas de una vez. Todo o nada: si falta cualquier ancla NO se cambia nada.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "b0dc3ca1b02550da4e95746c4021ea001c46f017e85062c61e01fe294ff92b91"
MARK = '/*v322-ui*/'

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v322.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.22 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    quedan = [n for n, old, new, c in edits if n != 'estilos' and ((orig.count(new) != 1) if old in new else (orig.count(old) != 0))]
    if orig.count('<style id="v322-style">') != 1:
        quedan.append('estilos')
    if quedan:
        fin('ERROR: la v3.22 esta a medias (falta: ' + ', '.join(quedan) + '). No se ha cambiado nada.')
    print('v3.22 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)
if orig.count('/*v318-apps*/') != 1 or orig.count('/*v321-prio*/') != 1:
    fin('ERROR: falta la v3.18 o la v3.21 (pasa antes v318.py y v321.py). No se ha cambiado nada.')

s = orig
for n, old, new, c in edits:
    k = s.count(old)
    if k != c:
        fin('ERROR: ' + n + ' no sale ' + str(c) + ' vez/veces en la pagina sino ' + str(k) + ' (la app no es la version esperada). No se ha cambiado nada.')
    s = s.replace(old, new)
if s.count(MARK) != 1 or s.count('<style id="v322-style">') != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir='www', suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('pagina: actualizada')
print('v3.22 aplicado: Control Horario con circulos grises y ventanas que se esconden (tramos y detalle semanal)')

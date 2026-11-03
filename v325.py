cd /workspaces/PORTAL_CONDUCTOR && gh run download $(gh run list -L 1 --status success --json databaseId -q '.[0].databaseId') -D apk_v325 && ls -R apk_v325# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.25)

NUEVO en «Madrid hoy»: IFEMA.
  - Se lee el calendario de ifema.es (ferias y espectaculos) y salen en la lista del dia con interes de recinto grande (Barajas).
  - Ferias de pocos dias: la web de IFEMA no da horario, asi que se supone el tipico (10:00) y la salida sale a las ~19:00; en el detalle puedes cambiar la duracion (8 h, 9 h o 10 h).
    Es una suposicion mia, no un dato de IFEMA.
  - Espectaculos de larga temporada (como Circlassica): salen todos los dias sin hora.
  - Si ifema.es falla o cambia su pagina, no se rompe nada: siguen los eventos de Ticketmaster y abajo pone lo que ha pasado con IFEMA.
NO incluye futbol ni baloncesto (Ticketmaster no los vende y aun no hay otra fuente comprobada).
Solo cambia www/index.html (nada de Java). Necesita la pantalla «Madrid hoy» (v3.16). Se puede pasar mas de una vez. Todo o nada.
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "RJjodmxDrIpgQ6CdIVe7Y0qOmt9W8Zv+L0knz2M="
)
SHA = "ac4cce3abc2ad65c05a044f10f8739051cf29216f7a1587a5c1a6a00c4187239"
MARK = '/*v325-ifema*/'

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v325.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.25 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    quedan = [n for n, old, new, c in edits if n != 'estilos' and ((orig.count(new) != 1) if old in new else (orig.count(old) != 0))]
    if quedan:
        fin('ERROR: la v3.25 esta a medias (falta: ' + ', '.join(quedan) + '). No se ha cambiado nada.')
    print('v3.25 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)
if orig.count('function parseEv(j){') != 1:
    fin('ERROR: no encuentro la pantalla «Madrid hoy» (falta la v3.16). No se ha cambiado nada.')

s = orig
for n, old, new, c in edits:
    k = s.count(old)
    if k != c:
        fin('ERROR: ' + n + ' no sale ' + str(c) + ' vez/veces en la pagina sino ' + str(k) + ' (la app no es la version esperada). No se ha cambiado nada.')
    s = s.replace(old, new)
if s.count(MARK) != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir='www', suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('pagina: actualizada')
print('v3.25 aplicado: IFEMA en Madrid hoy (ferias y espectaculos), con aviso si ifema.es falla')

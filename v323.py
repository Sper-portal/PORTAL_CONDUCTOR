# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.23)

NUEVO: restyling visual (solo apariencia) + arreglos de lo que se veia mal en Control Horario.
  - «Faltan para X h» (semana), «Dias trabajados» (mes) y «Estado» (dia) ya no son un cuadrado suelto entre los circulos:
    pasan a una etiqueta redondeada a la derecha de «Solo Bolt» (mismo dato, mismo calculo).
  - Los tramos guardados tienen SIEMPRE la misma fila: botones del mismo tamano y alineados (antes el tercero salia distinto).
  - Las letras de los circulos de Control se ajustan solas para quedar dentro del circulo (tambien con letra grande en el movil).
  - Circulos grises de «Todas las apps»: Bolt con tono verde y «Otras apps» con tono morado (como en el boceto).
  - Tarjetas de la Calculadora: «Total facturacion» en azul y «Mi comision» en morado; ventanas de detalle en cristal claro.
  - Las tres lineas del menu (arriba a la izquierda) un poco mas grandes. El encabezado no cambia.
Necesita la v3.22 (pasala antes). Solo cambia www/index.html (nada de Java). Se puede pasar mas de una vez. Todo o nada: si falta cualquier ancla NO se cambia nada.
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "Lw=="
)
SHA = "3057dc0262061b624005eddadeb4ace9ccb7d24640d371b1fb2a93352071f819"
MARK = '/*v323-ui*/'

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v323.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.23 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    quedan = [n for n, old, new, c in edits if n != 'estilos' and ((orig.count(new) != 1) if old in new else (orig.count(old) != 0))]
    if orig.count('<style id="v323-style">') != 1:
        quedan.append('estilos')
    if quedan:
        fin('ERROR: la v3.23 esta a medias (falta: ' + ', '.join(quedan) + '). No se ha cambiado nada.')
    print('v3.23 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)
if orig.count('/*v322-ui*/') != 1:
    fin('ERROR: falta la v3.22 (pasa antes v322.py). No se ha cambiado nada.')

s = orig
for n, old, new, c in edits:
    k = s.count(old)
    if k != c:
        fin('ERROR: ' + n + ' no sale ' + str(c) + ' vez/veces en la pagina sino ' + str(k) + ' (la app no es la version esperada). No se ha cambiado nada.')
    s = s.replace(old, new)
if s.count(MARK) != 1 or s.count('<style id="v323-style">') != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir='www', suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('pagina: actualizada')
print('v3.23 aplicado: restyling visual y arreglos de Control Horario (etiquetas, tramos alineados, letras dentro de los circulos)')

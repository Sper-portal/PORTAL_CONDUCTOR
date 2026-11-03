# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.24)

RESTYLING VISUAL (solo apariencia): estilo claro azul y verde, tarjetas de cristal blanco, botones de plataforma con sus colores de siempre.
  - Calculadora, Control, Facturacion e Informe pasan a un fondo claro con degradados suaves. Ajustes, el menu y las demas pantallas se quedan como estaban.
  - Bolt verde, Uber negro, Cabify morado y Privados azul (como siempre).
  - Control: todo lo «prioritario» toma el color de la app prioritaria que elijas (Bolt verde, Uber negro, Cabify morado):
    el selector, el circulo de horas prioritarias, el de la app en «Todas las apps» y el punto de «Solo ...».
  - Circulos: horas prioritarias (verde), no prioritarias (rojo), total (azul) y los grises, cada uno con su degradado casi blanco.
  - No se mueve ni cambia de tamano nada: solo colores, degradados, bordes y sombras. No se toca ninguna funcion ni calculo.
Necesita la v3.23 (pasala antes). Solo cambia www/index.html (nada de Java). Se puede pasar mas de una vez. Todo o nada.
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "20784186fb3c745c398037ac2f84bcb62ec2199917f96da96e23bdd83e805a8c"
MARK = '/*v324-lt*/'

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v324.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.24 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    quedan = [n for n, old, new, c in edits if n != 'estilos' and ((orig.count(new) != 1) if old in new else (orig.count(old) != 0))]
    if orig.count('<style id="v324-style">') != 1:
        quedan.append('estilos')
    if quedan:
        fin('ERROR: la v3.24 esta a medias (falta: ' + ', '.join(quedan) + '). No se ha cambiado nada.')
    print('v3.24 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)
if orig.count('/*v323-ui*/') != 1:
    fin('ERROR: falta la v3.23 (pasa antes v323.py). No se ha cambiado nada.')

s = orig
for n, old, new, c in edits:
    k = s.count(old)
    if k != c:
        fin('ERROR: ' + n + ' no sale ' + str(c) + ' vez/veces en la pagina sino ' + str(k) + ' (la app no es la version esperada). No se ha cambiado nada.')
    s = s.replace(old, new)
if s.count(MARK) != 1 or s.count('<style id="v324-style">') != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir='www', suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('pagina: actualizada')
print('v3.24 aplicado: restyling visual claro (azul y verde) con los colores de cada plataforma')

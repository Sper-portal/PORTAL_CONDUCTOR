# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.28)

CAMBIO: Propinas en Ajustes -> Nomina: solo dos formas.
  - «Todo en facturacion» (antes «Todo en nomina»): las propinas se suman a la facturacion del mes y de ahi sale el porcentaje.
  - «En nomina, solo con una retencion (%)»: igual que antes.
  - «Aparte» desaparece de Ajustes. Los meses ya calculados con «Aparte» se quedan con sus mismos numeros.
NUEVO: en Facturacion -> Mensual, cada mes cerrado tiene el boton «Cambiar esta nomina con los ajustes actuales»: ensena el antes y el despues,
  y si confirmas se cambia de verdad (porcentaje, minimo, propinas...). Se guarda una copia: «Volver a como estaba».
  Ayuda, Jenny e Informacion al dia (version v3.28).
Solo cambia www/index.html (nada de Java). Necesita la v3.27. Se puede pasar mas de una vez. Todo o nada.
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "a58d5addc2f02db8611545c84c3de32ce6e6b5b1e0c276f15dda2550200f75e6"
MARK = '/*v328-nom*/'

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v328.py. No se ha cambiado nada.')

with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if '\r\n' in orig:
    fin('ERROR: www/index.html tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

marks = orig.count(MARK)
if marks > 1:
    fin('ERROR: el bloque v3.28 esta repetido (' + str(marks) + ' veces). No se ha cambiado nada.')
if marks == 1:
    quedan = [n for n, old, new, c in edits if ((orig.count(new) not in (c if isinstance(c, list) else [c])) if old in new else (orig.count(old) != 0))]
    if quedan:
        fin('ERROR: la v3.28 esta a medias (falta: ' + ', '.join(quedan) + '). No se ha cambiado nada.')
    print('v3.28 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)
if orig.count('/*v327-theme*/') != 1:
    fin('ERROR: falta la v3.27 (cancelaciones con Free Now y tema). Pasa primero v327.py. No se ha cambiado nada.')
if orig.count('/* ---------- Ajustes ---------- */\nconst $=id=>document.getElementById(id);') != 1 or orig.count('P.decorateBillingPayroll=function(){') != 1:
    fin('ERROR: no encuentro el calculo de la nomina mensual (v3.14). No se ha cambiado nada.')

s = orig
for n, old, new, c in edits:
    k = s.count(old)
    cs = c if isinstance(c, list) else [c]
    if k not in cs:
        fin('ERROR: ' + n + ' no sale ' + ' o '.join(str(x) for x in cs) + ' vez/veces en la pagina sino ' + str(k) + ' (la app no es la version esperada). No se ha cambiado nada.')
    s = s.replace(old, new)
if s.count(MARK) != 1 or s.count('id="v328-style"') != 1:
    fin('ERROR interno: la insercion no ha quedado bien. No se ha cambiado nada.')

fd, tmp = tempfile.mkstemp(dir='www', suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('pagina: actualizada')
print('v3.28 aplicado: propinas en dos formas y boton para cambiar una nomina con los ajustes actuales')

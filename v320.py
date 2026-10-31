# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.20)

NUEVO: la zona de la RECOGIDA se puede decidir por el CODIGO POSTAL que trae la tarjeta de Bolt (por ejemplo «Calle Goya 12, Madrid 28001»).
  - Tres listas editables en Ajustes de Bolt -> Zonas: codigos postales de zona alta, media y baja. De fabrica (la lista del conductor): alta = 27 codigos del norte y noroeste; media = 21 codigos de dentro de la M-30; baja = 76 codigos del este y del sur.
  - Si la tarjeta trae un codigo que esta en una lista, manda ese; si no sale o no esta en ninguna lista, se usa el GPS y las zonas dibujadas como hasta ahora.
    La zona forzada en Ajustes sigue mandando sobre todo. Si un codigo esta en varias listas, gana la alta, luego la media y luego la baja.
  - Se lee el codigo del texto de la recogida (el que va antes del bloque de km y minutos del viaje); el del destino no se usa.
  - El aviso dice «Zona media (codigo postal 28001)».
Cambia Java (OfferAnalyzer, BoltConfig, ScreenReaderService) y www/index.html: hay que volver a compilar el APK. Se puede pasar mas de una vez
(la segunda no hace nada). Todo o nada: si falta cualquier ancla en cualquiera de los cuatro archivos NO se cambia ninguno.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "da1ab129ead02bd3c5655c6cbff1aeb1495119660c8b8da879bcec0f99985bb2"
MARCAS = {'android/app/src/main/java/com/portal/conductor/OfferAnalyzer.java': 'v3.20-cp',
          'android/app/src/main/java/com/portal/conductor/BoltConfig.java': 'postalList(',
          'android/app/src/main/java/com/portal/conductor/ScreenReaderService.java': '"postal".equals(r.estZoneSrc)',
          'www/index.html': '/*v320-cp*/'}

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v320.py. No se ha cambiado nada.')

orig = {}
for f in edits:
    if not os.path.exists(f):
        fin('ERROR: no encuentro ' + f + ' (ejecuta el parche desde la carpeta portal). No se ha cambiado nada.')
    with open(f, encoding='utf-8', newline='') as fh:
        orig[f] = fh.read()
    if '\r\n' in orig[f]:
        fin('ERROR: ' + f + ' tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')

puestos = [f for f in edits if MARCAS[f] in orig[f]]
if len(puestos) == len(edits):
    for f in edits:
        for n, old, new in edits[f]:
            if orig[f].count(new) != 1:
                fin('ERROR: la v3.20 esta a medias en ' + f + ' (falta: ' + n + '). No se ha cambiado nada.')
    print('v3.20 ya aplicado: no hay nada que cambiar.')
    raise SystemExit(0)
if puestos:
    fin('ERROR: la v3.20 esta a medias (ya esta en ' + ', '.join(puestos) + ' pero no en los demas). No se ha cambiado nada.')

nuevo = {}
for f in edits:
    s = orig[f]
    for n, old, new in edits[f]:
        c = s.count(old)
        if c != 1:
            fin('ERROR: ' + n + (' no esta' if c == 0 else ' esta repetido (' + str(c) + ' veces)') + ' en ' + f + '. No se ha cambiado nada (la app no es la version esperada).')
        s = s.replace(old, new, 1)
    nuevo[f] = s
temps = []
try:
    for f, s in nuevo.items():
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(f) or '.', suffix='.tmp')
        os.close(fd)
        with open(tmp, 'w', encoding='utf-8', newline='') as fh:
            fh.write(s)
        temps.append((tmp, f))
except Exception as e:
    for tmp, f in temps:
        try: os.remove(tmp)
        except OSError: pass
    fin('ERROR escribiendo: ' + str(e) + '. No se ha cambiado nada.')
for tmp, f in temps:
    os.replace(tmp, f)
print('archivos: actualizados (' + str(len(temps)) + ')')
print('v3.20 aplicado: la zona de la recogida se decide por el codigo postal de la tarjeta de Bolt si esta en tus listas (hay que volver a compilar la APK)')

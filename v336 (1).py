# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.36)

CAMBIOS: VIAJES GUARDADOS · AEROPUERTO (solo la lengueta; la calculadora, Uber, Cabify y el Java no cambian)
  - Con TARJETA, el albaran final de un viaje de aeropuerto viene SIN la tasa (lo que ves al principio, p. ej. 18,35, ya la lleva); en EFECTIVO la tasa sale como una linea mas.
    Antes, el «Bruto estimado» (con tasa) se veia junto al bruto del albaran (sin tasa) y el primer viaje parecia clavado cuando en realidad fallaba 2,60 €.
  - Detalle del viaje, pestaña Albaran: caja nueva «Bruto con y sin tasa de aeropuerto»: estimado, albaran sin tasa, con la tasa (la que escribas a mano en
    «Tarifa aeropuerto» o, si no hay, la de la estimacion) y las dos diferencias (real sin tasa − estimado, real con tasa − estimado). Se actualiza sola al escribir la tasa.
    Si las lineas del albaran no cuadran con el total, no se inventa nada y la caja no sale.
  - Albaran en efectivo con la tasa como linea: ya no avisa por error de «no cuadran los importes» ni de «bruto + comision no da el neto».
  - CSV: 6 columnas nuevas AL FINAL (tasa usada, de donde sale, bruto real sin tasa, bruto real con tasa y las dos diferencias). Las de antes no se mueven.
  - El neto contra neto («Estimado contra real») no cambia.
  El instalador busca textos concretos de tu index.html (los que dejo la v3.35). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v335.py. Hay que volver a compilar la APK.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "36d7775afe2e526c9516f8e6b84db30ca427094c38ec1a2a34d8931eba9cb952"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.35';"
V_NEW = "const APP_VERSION='v3.36';"


def fin(msg):
    raise SystemExit(msg)


if not os.path.exists(HT):
    try:
        os.chdir('/workspaces/PORTAL_CONDUCTOR/portal')
    except OSError:
        pass
try:
    raw = zlib.decompress(base64.b64decode(PAYLOAD)).decode('utf-8')
    ok_sum = hashlib.sha256(raw.encode('utf-8')).hexdigest() == SHA
    PAY = json.loads(raw) if ok_sum else None
except Exception:
    ok_sum = False
if not ok_sum:
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v336.py. No se ha cambiado nada.')

RES = []


def say(part, state, text):
    RES.append((part, state, text))


def read(path):
    if not os.path.exists(path):
        return None, 'no encuentro ' + path + ' (ejecuta el parche desde la carpeta portal)'
    with open(path, encoding='utf-8', newline='') as fh:
        t = fh.read()
    if '\r\n' in t:
        return None, path + ' tiene finales de linea de Windows; este parche espera los de Linux'
    return t, None


def write_atomic(path, text):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.', suffix='.tmp')
    os.close(fd)
    try:
        with open(tmp, 'w', encoding='utf-8', newline='') as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def short(t, n=70):
    t = ' '.join(t.split())
    return t if len(t) <= n else t[:n] + '...'


def part_file(entry, extra_version):
    """Devuelve el texto nuevo del archivo, o None si no hay que escribirlo (ya estaba, o no se puede)."""
    path, name, edits = entry['path'], entry['name'], entry['edits']
    s0, err = read(path)
    if s0 is None:
        say(name, 'no', err)
        return None
    st = []
    for i, (old, new) in enumerate(edits):
        cn = s0.count(new)
        co = s0.count(old)
        if cn == 1:
            st.append('A')                 # ya aplicada
        elif cn == 0 and co == 1:
            st.append('P')                 # pendiente
        else:
            st.append(('?', i, co, cn))
    bad = [x for x in st if isinstance(x, tuple)]
    if bad:
        i = bad[0][1]
        co, cn = bad[0][2], bad[0][3]
        if cn > 1 or co > 1:
            say(name, 'no', 'el trozo %d de %d aparece repetido en %s (%s); no toco nada' % (i + 1, len(edits), path, short(edits[i][0])))
        else:
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.35 que espero (¿has pasado v335.py?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
        return None
    if all(x == 'A' for x in st):
        say(name, 'ya', 'ya estaba aplicado')
        return None
    if any(x == 'A' for x in st):
        say(name, 'no', 'esta a medias (%d de %d trozos ya estan y el resto no); no toco nada. Mandame una captura.' % (st.count('A'), len(st)))
        return None
    s = s0
    for i, (old, new) in enumerate(edits):
        if s.count(old) != 1:
            say(name, 'no', 'el trozo %d de %d ha dejado de ser unico mientras lo aplicaba (%s); no toco nada' % (i + 1, len(edits), short(old)))
            return None
        s = s.replace(old, new, 1)
    say(name, 'ok', 'aplicado (%d cambios)' % len(edits))
    return s


def part_version(base_text):
    t = base_text
    if t is None:
        t, err = read(HT)
        if t is None:
            say('Numero de version', 'no', err)
            return None
    if t.count(V_NEW) == 1:
        say('Numero de version', 'ya', 'ya es v3.36')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.35 -> v3.36')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.35; pasa v335.py primero si quieres que ponga v3.36)')
    return None


# ------------------------------------------------------------------ ejecucion: todo se calcula antes de escribir nada
writes = {}
html_text = None
for entry in PAY['files']:
    out = part_file(entry, False)
    if out is not None:
        writes[entry['path']] = out
    if entry['path'] == HT and out is not None:
        html_text = out
base = html_text
if base is None and HT not in writes:
    base, _e = read(HT)
nv = part_version(base)
if nv is not None:
    writes[HT] = nv
if any(r[1] == 'no' for r in RES):
    writes = {}   # si una parte no se puede aplicar, no se toca nada (ni siquiera el numero de version)
for path, text in writes.items():
    try:
        write_atomic(path, text)
    except Exception as e:
        say('Escritura', 'no', 'no he podido escribir ' + path + ': ' + str(e))

print('v3.36:')
bad = 0
for part, state, text in RES:
    icon = {'ok': 'OK ', 'ya': 'ya ', 'no': 'NO '}[state]
    if state == 'no':
        bad += 1
    print('  ' + icon + part + ': ' + text.replace('\n', '\n      '))
changed = list(writes.keys())
if changed:
    print('Archivos cambiados: ' + ', '.join(changed))
else:
    print('No se ha cambiado ningun archivo.')
if bad:
    print('RESULTADO: hay partes sin aplicar (las lineas «NO» de arriba). No se ha tocado nada. Haz una captura de esto y mandamela.')
    raise SystemExit(1)
print('RESULTADO: todo aplicado o ya estaba' + (' (hay que volver a compilar la APK)' if changed else ''))

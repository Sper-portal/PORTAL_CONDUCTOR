# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.38)

CAMBIOS: BOTONES DE ZONA EN EL AVISO DE BOLT (solo Bolt; Uber y Cabify no cambian)
  - Debajo del aviso de Bolt salen tres botones pequenos: Baja, Media y Alta, cada uno con el neto que saldria en esa zona.
    Solo salen cuando la oferta esta cerca de un limite entre zonas (por la ubicacion y la precision del GPS). Al tocar uno, se recalcula al instante
    y la oferta apuntada en «Viajes guardados» se actualiza (no se apunta otra).
  - La zona que eliges vale solo para esa oferta y solo unos 2 minutos.
  - El aviso dice si la zona la has elegido tu, y avisa si el codigo postal de la oferta no esta en ninguna de tus listas.
  - El CSV de Viajes guardados tiene 2 columnas nuevas al final: «Zona: de donde sale» y «CP sin zona en tus listas».
  El instalador busca textos concretos de tus archivos (los que dejo la v3.37). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v337.py. Hay que volver a compilar la APK.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "cc61c69c915951e5d7d1915506c502e5661a9bdec2823fcd25ed48eaaf5d7377"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.37';"
V_NEW = "const APP_VERSION='v3.38';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v338.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.37 que espero (¿has pasado v337.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.38')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.37 -> v3.38')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.37; pasa v337.py primero si quieres que ponga v3.38)')
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

print('v3.38:')
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

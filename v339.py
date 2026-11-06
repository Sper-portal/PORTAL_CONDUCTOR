# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.39)

CAMBIOS (solo Bolt; Uber y Cabify no cambian)
  1) LISTA DE «VIAJES GUARDADOS» POR DIAS Y ABIERTA POR ABAJO
     - Los viajes salen agrupados por dia (Hoy, Ayer, vie 6 nov...), cada dia con cuantos viajes son y su total.
     - Solo el ultimo dia sale abierto; los anteriores salen recogidos y se abren tocando su linea.
     - Al abrir la lista siempre te deja en el ultimo viaje (abajo del todo). Si abres un viaje y vuelves, te deja donde estabas.
     - La numeracion «Viaje N» no cambia (es la misma del aviso y del detalle). «Cerrar y guardar» y el CSV siguen igual.
  2) LA VOZ DE BOLT ES MAS CORTA: «Neto estimado: 8,74 euros. Viaje de 8,3 kilometros.»
     (si el viaje es corto y con demanda, dice tambien «entre A y B» despues del neto). Ya no dice zona, tarifa, comision ni minutos.
  El instalador busca textos concretos de tus archivos (los que dejo la v3.38). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v338.py. Hay que volver a compilar la APK.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "fc475ecbc7776a041d546503e89d9a64cdc2edf4c4040b9990d471fde73c5b90"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.38';"
V_NEW = "const APP_VERSION='v3.39';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v339.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.38 que espero (¿has pasado v338.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.39')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.38 -> v3.39')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.38; pasa v338.py primero si quieres que ponga v3.39)')
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

print('v3.39:')
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

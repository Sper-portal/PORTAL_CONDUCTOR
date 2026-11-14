# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.52)

CONTROL HORARIO - «OTRAS APPS» CON LISTA DE APPS (Uber, Cabify, Free Now, Pide Taxi, Otra app):
  - Al pulsar «Otras apps» sale una lista de apps y eliges con cual trabajas (Bolt, la prioritaria, no sale en la lista: sigue como siempre).
  - Las otras apps solo cuentan horas y km por separado; no tienen horas prioritarias.
  - Al tocar el circulo «OTRAS APPS» (dia, semana o mes) sale cada app con sus horas y km, y «Todas juntas».
  - Lo de antes (sin app indicada) sale como «Sin detallar»; en los tramos guardados hay un boton 📲 para ponerles app.
AJUSTES:
  - Las tarjetas del menu (y las 3 del Tema) tienen el mismo ancho y alto.
  - Los titulos y notas de los campos desactivados de «Configuracion de la app» se leen bien (el cuadro sigue apagado).

  - Solo cambia la pantalla (index.html). No cambia el lector de ofertas.

  No toca la camara ni mas archivos. Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v351.py. Hay que volver a compilar la APK.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "t1OAS456vz1f8CdTRhLA=="
)
SHA = "b348cc166659de0c6f31cafea8cdd01dded25dbdae7a66340662abc3eca21b52"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.51';"
V_NEW = "const APP_VERSION='v3.52';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v352.py. No se ha cambiado nada.')

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
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
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


def write_atomic_bytes(path, data):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.', suffix='.tmp')
    os.close(fd)
    try:
        with open(tmp, 'wb') as fh:
            fh.write(data)
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
    for i, ed in enumerate(edits):
        old, new = ed[0], ed[1]
        cn = s0.count(new)
        co = s0.count(old)
        if len(ed) > 2 and ed[2] not in s0 and cn == 0 and co == 0:
            st.append('S')                 # no aplica: el archivo no tiene el modulo (p. ej. sin odometro); se salta
        elif cn == 1:
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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.51 que espero (¿has pasado v351.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
        return None
    if all(x in ('A', 'S') for x in st):
        say(name, 'ya', 'ya estaba aplicado')
        return None
    if any(x == 'A' for x in st):
        say(name, 'no', 'esta a medias (%d de %d trozos ya estan y el resto no); no toco nada. Mandame una captura.' % (st.count('A'), len(st)))
        return None
    s = s0
    for i, ed in enumerate(edits):
        old, new = ed[0], ed[1]
        if st[i] == 'S':
            continue
        if s.count(old) != 1:
            say(name, 'no', 'el trozo %d de %d ha dejado de ser unico mientras lo aplicaba (%s); no toco nada' % (i + 1, len(edits), short(old)))
            return None
        s = s.replace(old, new, 1)
    say(name, 'ok', 'aplicado (%d cambios)' % (len(edits) - st.count('S')))
    return s


def part_create(entry):
    """Archivo nuevo: se crea si no existe; si ya esta igual, ya estaba; si existe distinto, no se toca."""
    path, name, text = entry['path'], entry['name'], entry['create']
    if os.path.exists(path):
        cur, err = read(path)
        if cur is None:
            say(name, 'no', err)
        elif cur == text:
            say(name, 'ya', 'ya estaba')
        else:
            say(name, 'no', 'ya existe %s y es distinto; no lo toco (¿tenias otra version de este archivo?)' % path)
        return None
    say(name, 'ok', 'creado')
    return text


def part_asset(entry):
    """Imagen (archivo binario): si ya es igual, ya estaba; si no, se reemplaza (el cartel de arriba)."""
    path, name = entry['path'], entry['name']
    data = base64.b64decode(entry['b64'])
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        say(name, 'no', 'la imagen incluida en este parche esta danada; no toco nada')
        return None
    cur = None
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            cur = fh.read()
    if cur == data:
        say(name, 'ya', 'ya estaba')
        return None
    say(name, 'ok', 'reemplazado' if cur is not None else 'creado')
    return data


def part_version(base_text, newer_ok=False):
    t = base_text
    if t is None:
        t, err = read(HT)
        if t is None:
            say('Numero de version', 'no', err)
            return None
    if t.count(V_NEW) == 1:
        say('Numero de version', 'ya', 'ya es v3.52')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 52:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.51 -> v3.52')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.51 (esperaba const APP_VERSION=\'v3.51\'). Pasa v351.py primero y luego este. No toco nada.')
    return None


# ------------------------------------------------------------------ ejecucion: todo se calcula antes de escribir nada
writes = {}
html_text = None
for entry in PAY['files']:
    if 'b64' in entry:
        out = part_asset(entry)
        if out is not None:
            writes[entry['path']] = out
        continue
    if 'create' in entry:
        out = part_create(entry)
        if out is not None:
            writes[entry['path']] = out
        continue
    out = part_file(entry, False)
    if out is not None:
        writes[entry['path']] = out
    if entry['path'] == HT and out is not None:
        html_text = out
base = html_text
if base is None and HT not in writes:
    base, _e = read(HT)
nv = part_version(base, newer_ok=not writes)
if nv is not None:
    writes[HT] = nv
if any(r[1] == 'no' for r in RES):
    writes = {}   # si una parte no se puede aplicar, no se toca nada (ni siquiera el numero de version)
for path, text in writes.items():
    try:
        (write_atomic_bytes if isinstance(text, bytes) else write_atomic)(path, text)
    except Exception as e:
        say('Escritura', 'no', 'no he podido escribir ' + path + ': ' + str(e))

print('v3.52:')
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

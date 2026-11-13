# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.51)

HORAS PUNTA Y VALLE (Ajustes > Rentabilidad > Estimacion de precio):
  - Tres listas de franjas, una por zona: BAJA, MEDIA y ALTA. Cada una se edita por separado (añadir, cambiar, apagar, borrar y «Franjas iniciales»).
    Antes la baja y la media compartian la lista.
  - De fabrica: baja y media igual que hasta ahora (lunes a viernes 07-10 y 17-20; sabados y domingos todo el dia).
    Alta: lunes a viernes 08-10 y 17-20, el VIERNES TAMBIEN de 20:00 a 24:00 (visto el 13-11, sin confirmar) y sabados y domingos todo el dia.
  - Quien tenia la lista de la alta de fabrica de antes pasa a la nueva UNA vez; quien la habia cambiado conserva la suya.
    La lista de la baja nace como una copia de la que ya tenias para media y baja.
  - Se cambian la pantalla (index.html) y el lector (OfferAnalyzer.java y BoltConfig.java), para que la oferta se calcule igual en los dos sitios.

  No toca la camara ni mas archivos. Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v350.py. Hay que volver a compilar la APK.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "383ff9a17e94262bbba4b8759d567b0c1ba17f28b21ffaea2b3f9cb7070f8c37"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.50';"
V_NEW = "const APP_VERSION='v3.51';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v351.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.50 que espero (¿has pasado v350.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.51')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 51:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.50 -> v3.51')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.50 (esperaba const APP_VERSION=\'v3.50\'). Pasa v350.py primero y luego este. No toco nada.')
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

print('v3.51:')
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

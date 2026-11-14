# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.53)

OTRO MOVIL VE LO MISMO + NOMBRE «DRIVER HUB 360»:
  - Tu configuracion de Bolt (precios, zonas, franjas) llega a un movil nuevo al entrar a tu cuenta. Antes se quedaba la de fabrica.
    Gana siempre la que guardaste mas tarde; la de fabrica sembrada sola nunca pisa la tuya.
  - La tasa de finalizacion (dias, limites, ultimos 100 viajes) sube a tu cuenta y se une dia a dia entre moviles, sin perder nada.
    La lista de viajes con ✓ NO sube: se queda en el movil donde la haces.
  - Al volver a la app, si en este movil no hay nada sin subir y la nube tiene algo nuevo, el movil se pone al dia (casi no gasta datos).
  - La app pasa a llamarse «Driver Hub 360»: nombre bajo el icono, entrada de Accesibilidad y los textos de ayuda que decian «Portal Lector».

  No toca la camara, ni el codigo Java, ni las carpetas de la Galeria. Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v352.py. Hay que volver a compilar la APK.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "b1979dcffc11785423183e815dcae1c04dabf0bbcc34927a74a48e78a339c070"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.52';"
V_NEW = "const APP_VERSION='v3.53';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v353.py. No se ha cambiado nada.')

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
    if entry.get('optional') and not os.path.exists(path):
        say(name, 'ya', 'este archivo no existe en esta copia (no es tu repo completo): se salta')
        return None
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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.52 que espero (¿has pasado v352.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.53')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 53:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.52 -> v3.53')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.52 (esperaba const APP_VERSION=\'v3.52\'). Pasa v352.py primero y luego este. No toco nada.')
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

print('v3.53:')
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

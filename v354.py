# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.54)

SOS SENCILLO (boton de ayuda con tu ubicacion):
  - Boton rojo «SOS» fijo, arriba a la derecha, en todas las pantallas. Se mantiene pulsado 2 segundos (se llena un aro y el movil vibra);
    un toque corto solo recuerda que hay que mantenerlo pulsado. Asi no se avisa por error.
  - Se abre la pantalla de ayuda: busca tu ubicacion, escribe el mensaje con el enlace al mapa y ofrece SMS a todos tus contactos de confianza,
    WhatsApp a cada uno, Compartir… y Llamar al 112. No envia nada solo: se abre la app y tu pulsas «enviar».
  - Ajustes: tarjeta nueva «SOS y contactos de confianza» (la primera del menu): tu nombre, contactos (nombre + telefono), mensaje y «Probar (no envia nada)».
    Los contactos se guardan tambien en tu cuenta.

  Solo cambia la pantalla (index.html). No toca la camara, ni el codigo Java, ni las carpetas de la Galeria. Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v353.py. Hay que volver a compilar para que llegue al movil.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "+Tc00Ah9CF/68Olv1PD9T/4vH8fH4+/1+sH8i7"
)
SHA = "68567105eb8a49441bb55e2f3b77a0c3f53bcb7f8679b9e50127c1c4b824158a"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.53';"
V_NEW = "const APP_VERSION='v3.54';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v354.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.53 que espero (¿has pasado v353.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.54')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 54:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.53 -> v3.54')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.53 (esperaba const APP_VERSION=\'v3.53\'). Pasa v353.py primero y luego este. No toco nada.')
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

print('v3.54:')
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

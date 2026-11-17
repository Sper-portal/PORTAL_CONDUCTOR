
# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.57)

«Calles limitrofes» (pedido de Juan, 17-11-2026):
  - En un aviso con duda entre dos zonas (los botones Baja / Media / Alta) la zona que eliges se guarda con la DIRECCION de la recogida (calle + numero + codigo postal).
    La proxima vez que sale esa misma direccion, el aviso usa esa zona sin preguntar y lo dice («calle guardada»); los botones siguen para poder corregirla.
    Otro numero de la misma calle NO se da por bueno. Si la oferta no trae numero queda como «tramo dudoso»: se apunta, pero no se usa sola hasta que le pongas el numero.
  - Rentabilidad: apartado nuevo «Calles limitrofes» (despues de «Zonas y mapa»): la lista con anadir, corregir (tambien el tramo dudoso), borrar y deshacer, buscar y «Copiar mi lista».
  - Maximo 300 direcciones (unos 25-40 KB); se guardan aparte de tus ajustes de Bolt y se unen entre tus moviles y tu cuenta (por direccion gana el cambio mas reciente).
  - NO cambia ninguna formula ni tarjeta: solo decide QUE zona (baja, media o alta) se usa para la recogida.

  Cambia www/index.html y 3 archivos Java (OfferAnalyzer, ScreenReaderService, ScreenReaderPlugin) y crea 1 archivo Java nuevo (StreetMemory.java). No toca manifiesto, camara ni la nube.
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v356.py (la v3.56). Hay que volver a compilar.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "79bcc49f19a450208ee066037e74519c4fc3b6a0cbea22fd2887e1d3f3197480"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.56';"
V_NEW = "const APP_VERSION='v3.57';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v357.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.56 que espero (¿has pasado v356.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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


def part_json(entry):
    """JSON (package.json): anade las claves que faltan leyendo el JSON, asi no depende de como este escrito. Si ya estan, no toca nada."""
    path, name, ops = entry['path'], entry['name'], entry['json']
    s0, err = read(path)
    if s0 is None:
        say(name, 'no', err)
        return None
    try:
        obj = json.loads(s0)
    except Exception:
        obj = None
    if not isinstance(obj, dict):
        say(name, 'no', path + ' no se puede leer como JSON; no lo toco')
        return None
    pend = 0
    for keys, val in ops:
        d = obj
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
            if not isinstance(d, dict):
                say(name, 'no', 'en %s «%s» no es lo que espero; no lo toco' % (path, k))
                return None
        if keys[-1] not in d:
            d[keys[-1]] = val
            pend += 1
    if not pend:
        say(name, 'ya', 'ya estaba aplicado')
        return None
    m = re.search(r'^([ \t]+)"', s0, re.M)
    out = json.dumps(obj, indent=(m.group(1) if m else '  '), ensure_ascii=False) + ('\n' if s0.endswith('\n') else '')
    say(name, 'ok', 'aplicado (%d cambios)' % pend)
    return out


def part_version(base_text, newer_ok=False):
    t = base_text
    if t is None:
        t, err = read(HT)
        if t is None:
            say('Numero de version', 'no', err)
            return None
    if t.count(V_NEW) == 1:
        say('Numero de version', 'ya', 'ya es v3.57')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 57:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.56 -> v3.57')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.56 (esperaba const APP_VERSION=\'v3.56\'). Pasa v356.py primero y luego este. No toco nada.')
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
    if 'json' in entry:
        out = part_json(entry)
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

print('v3.57:')
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

# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.64)

Un cambio pedido por Juan (20-11, 23:19, 23:23 y 23:25): la nomina «Nomina variable + fijo».
  Antes el fijo (por ejemplo 2.000 €) se SUMABA encima de tu parte (45 % de la facturacion). Para Juan el fijo sale DE esa parte:
  con 8.000 € de facturacion, el 45 % son 3.600 €; de ahi salen 2.000 de fijo (en efectivo) y lo que sobra (1.600) va a nomina; el IRPF es solo de esa nomina.
  Hay companeros con el pacto contrario (todo su porcentaje a nomina y el fijo aparte, encima): se mantiene.
  En Ajustes, con el perfil «Nomina variable + fijo», sale un desplegable nuevo «El fijo»: «Sale de mi parte» o «Se suma aparte» (lo de siempre: es lo que hay si no eliges nada).
  Los meses cerrados no se mueven; si quieres cambiar uno, el boton de siempre «Cambiar esta nomina con los ajustes actuales» tambien cambia esto.

  Cambia SOLO www/index.html (ningun archivo Java, ni manifiesto, ni la nube). Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v363.py (la v3.63). Hay que volver a compilar la APK.
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "VeKQ=="
)
SHA = "057f0b8a066c97036211a789748402a29abbb1091c52938ec09d831d64bd2709"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.63';"
V_NEW = "const APP_VERSION='v3.64';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v364.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.63 que espero (¿has pasado v363.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.64')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.63 -> v3.64')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.63 (esperaba const APP_VERSION=\'v3.63\'). Pasa v363.py primero y luego este. No toco nada.')
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

print('v3.64:')
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

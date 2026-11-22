# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.66)

Cuatro cambios pedidos por Juan (22-11):
  1) El cartel de tasa («SIN PENALIZACION», «ACTUALIZACION DE TASA») se quita DESLIZANDO (a un lado o hacia arriba); un toque suelto sigue abriendo la pagina de tasa.
  2) Kilometros: al finalizar la jornada y volver a iniciarla al momento ya no salen dobles.
  3) Metas MENSUALES con barras (Resumen mensual), en la lengüeta «Metas y horarios prioritarios».
  4) «Gasolina y odometro» con encabezados; Ajustes → Rentabilidad: Burbuja, Voz y Objetivos a la vista y el resto en «Datos del fabricante» con contrasena.

  Cambia SOLO www/index.html (Java, manifiesto y nube sin cambios; hay que COMPILAR porque la pagina va dentro de la APK).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v365.py (la v3.65). Hay que volver a compilar la APK.
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "fd6e7a81056f4afb2e507f0b6f705a2622f78a7b94801ce01a165ed5d3cee73e"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.65';"
V_NEW = "const APP_VERSION='v3.66';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v366.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.65 que espero (¿has pasado v365.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.66')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.65 -> v3.66')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.65 (esperaba const APP_VERSION=\'v3.65\'). Pasa v365.py primero y luego este. No toco nada.')
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

print('v3.66:')
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

# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.67)

Cambios pedidos por Juan (23 y 24-11):
  1) Control → «Metas y horarios prioritarios»: «Mis días libres y límites» y «Plan para cumplir» (te dice desde qué hora hasta qué hora trabajar cada día para llegar a las horas).
  2) «Eventos Madrid hoy» (antes «Madrid hoy»): ahora también lee Matadero Madrid y reconoce el Autocine Madrid (The Lenovo Garage, por Ticketmaster).
  3) Últimos viajes: cada viaje guarda la hora de aceptación y la de finalización; las dos se pueden editar y la lista se ordena por hora.
  4) Ajustes: «Configuración de la app» pasa a «Nóminas y comisiones» (nómina por un lado; comisión y tasa de aeropuerto de Bolt aparte; sin «control horario»).
  5) Tasa de finalización: «Finalizados» solo los que terminas; «Rechazados» y «Cancelados» por separado; «Ofertas».

  Cambia SOLO www/index.html (Java, manifiesto y nube sin cambios; hay que COMPILAR porque la pagina va dentro de la APK).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v366.py (la v3.66). Hay que volver a compilar la APK.
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "vGt3"
)
SHA = "de1ffa7ecd1969595105da0aee9b850c1e8813feca171b23098dbce869db3f27"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.66';"
V_NEW = "const APP_VERSION='v3.67';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v367.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.66 que espero (¿has pasado v366.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.67')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.66 -> v3.67')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.66 (esperaba const APP_VERSION=\'v3.66\'). Pasa v366.py primero y luego este. No toco nada.')
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

print('v3.67:')
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

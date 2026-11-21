# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.65)

Tres cambios pedidos por Juan (21-11):
  1) Control horario → Resumen semanal: metas de horas PRIORITARIAS y NO PRIORITARIAS (circulos «de 30 h / de 25 h / de 55 h», dos barras con «Faltan X h» o «✓ Cumplido»,
     lengüeta «Metas y horarios prioritarios»; en Ajustes queda una tarjeta con boton «Ir a Control horario ›»). Sin metas puestas, todo como antes.
  2) Interruptor «Preguntarme la zona cuando hay duda» (botones baja / media / alta del aviso en zona limitrofe): APAGADO de fabrica (tambien en los moviles con ajustes ya guardados).
     Esta en «Zonas y mapa» y como tercer interruptor de «Viajes guardados» → «Lista de viajes y datos que enseña».
  3) La burbuja se queda encima de Waze y Google Maps si hace menos de 2 horas estabas en una app de conductor.

  Cambia www/index.html y 3 archivos Java: OfferAnalyzer.java, BoltConfig.java y ScreenReaderService.java (ni manifiesto, ni la nube).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v364.py (la v3.64). Hay que volver a compilar la APK.
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "10071fb75575e99be4f2bee775a3b668f5b5cadc593e88fa90a2b1df32f89a05"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.64';"
V_NEW = "const APP_VERSION='v3.65';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v365.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.64 que espero (¿has pasado v364.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.65')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.64 -> v3.65')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.64 (esperaba const APP_VERSION=\'v3.64\'). Pasa v364.py primero y luego este. No toco nada.')
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

print('v3.65:')
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

# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.75)

Cambios pedidos por Juan (25-11, mañana):
  1) Isleta: la barra de abajo de los temas Claro y Oscuro flota como la de Personalizado (mas arriba, esquinas redondas, mas estrecha), cada una con sus iconos. Personalizado no cambia.
  2) Jenny: tercer boton «No es esto lo que busco, es otra cosa» (elegir otro tema o escribir otra pregunta) sin cerrar el caso ni mandar nada a soporte.
  3) Jenny: puntitos de «escribiendo…» antes de cada respuesta.
  4) Uber y Cabify: el cartel del lector saca ✓ «La acepte»; la hora se guarda POR DENTRO (no sale en «Viajes guardados» ni toca la tasa de Bolt), la nueva sustituye a la vieja, y al apuntar el viaje sale «Aceptado hh:mm · Finalizado hh:mm».
  5) Casos y mensajes de soporte: se borran UNA vez todos (abiertos, cerrados y pendientes) para empezar de cero.
  De regalo: el recuadro oscuro de Ayuda y de Jenny se lee blanco en Claro y Personalizado.
  Nada mas cambia, salvo el numero de version (v3.75). Hay que COMPILAR y volver a instalar la APK (la pagina y el lector van dentro).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v374.py (la v3.74).
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "DMMs8fznqZeXD5cP/wstfbji"
)
SHA = "e0ff4e6d30fd89a9875dae63ffccb1d27cddabc7292ca1b8238657e0c02ff9af"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.74';"
V_NEW = "const APP_VERSION='v3.75';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v375.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.74 que espero (¿has pasado v374.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.75')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.74 -> v3.75')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.74 (esperaba const APP_VERSION=\'v3.74\'). Pasa v374.py primero y luego este. No toco nada.')
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

print('v3.75:')
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

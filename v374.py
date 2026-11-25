# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.74)

Cambios pedidos por Juan (25-11, mañana):
  1) Isleta: la barra de abajo de los temas Claro y Oscuro flota como la de Personalizado (mas arriba, esquinas redondas, mas estrecha), cada una con sus iconos. Personalizado no cambia.
  2) Jenny: tercer boton «No es esto lo que busco, es otra cosa» (elegir otro tema o escribir otra pregunta) sin cerrar el caso ni mandar nada a soporte.
  3) Jenny: puntitos de «escribiendo…» antes de cada respuesta.
  4) Uber y Cabify: el cartel del lector saca ✓ «La acepte»; la hora se guarda POR DENTRO (no sale en «Viajes guardados» ni toca la tasa de Bolt), la nueva sustituye a la vieja, y al apuntar el viaje sale «Aceptado hh:mm · Finalizado hh:mm».
  5) Casos y mensajes de soporte: se borran UNA vez todos (abiertos, cerrados y pendientes) para empezar de cero.
  De regalo: el recuadro oscuro de Ayuda y de Jenny se lee blanco en Claro y Personalizado.
  Nada mas cambia, salvo el numero de version (v3.74). Hay que COMPILAR y volver a instalar la APK (la pagina y el lector van dentro).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v373.py (la v3.73).
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "+/c372/+H35/FrE="
)
SHA = "4f425de0e08188d669cf56e50bb997f20d3b611985430184e1f7288f3cbd10f8"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.73';"
V_NEW = "const APP_VERSION='v3.74';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v374.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.73 que espero (¿has pasado v373.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.74')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.73 -> v3.74')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.73 (esperaba const APP_VERSION=\'v3.73\'). Pasa v373.py primero y luego este. No toco nada.')
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

print('v3.74:')
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

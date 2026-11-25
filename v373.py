# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.73)

Cambios pedidos por Juan (25-11, mañana):
  1) Isleta: la barra de abajo de los temas Claro y Oscuro flota como la de Personalizado (mas arriba, esquinas redondas, mas estrecha), cada una con sus iconos. Personalizado no cambia.
  2) Jenny: tercer boton «No es esto lo que busco, es otra cosa» (elegir otro tema o escribir otra pregunta) sin cerrar el caso ni mandar nada a soporte.
  3) Jenny: puntitos de «escribiendo…» antes de cada respuesta.
  4) Uber y Cabify: el cartel del lector saca ✓ «La acepte»; la hora se guarda POR DENTRO (no sale en «Viajes guardados» ni toca la tasa de Bolt), la nueva sustituye a la vieja, y al apuntar el viaje sale «Aceptado hh:mm · Finalizado hh:mm».
  5) Casos y mensajes de soporte: se borran UNA vez todos (abiertos, cerrados y pendientes) para empezar de cero.
  De regalo: el recuadro oscuro de Ayuda y de Jenny se lee blanco en Claro y Personalizado.
  Nada mas cambia, salvo el numero de version (v3.73). Hay que COMPILAR y volver a instalar la APK (la pagina y el lector van dentro).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v372.py (la v3.72).
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "769hU2KlGkqw14eDg5nPwvBxjy/A=="
)
SHA = "ab888a342d7ff96de352658700c20a847efffdcaa01ab44ff9da95d91c38b862"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.72';"
V_NEW = "const APP_VERSION='v3.73';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v373.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.72 que espero (¿has pasado v372.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.73')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.72 -> v3.73')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.72 (esperaba const APP_VERSION=\'v3.72\'). Pasa v372.py primero y luego este. No toco nada.')
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

print('v3.73:')
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

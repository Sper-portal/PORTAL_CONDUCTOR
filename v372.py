# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.72)

Cambios pedidos por Juan (24-11, tarde-noche):
  1) Control: el desplegable «Aplicacion prioritaria» y el boton de «Ahora trabajo con» salen con el color de la app elegida tambien en los temas Oscuro y Personalizado (antes solo en Claro).
  2) El tema (Automatico / Claro / Oscuro / Personalizado) viaja con la cuenta: al abrir sesion en otro movil sale el mismo tema.
  3) Facturacion -> Semanal: se puede editar una cancelacion o compensacion SIN escribir la fecha (se abre la ventana de editar con el dia ya puesto; el dia se puede cambiar dentro de la misma semana).
     Tambien se arregla el rotulo «Bolt por cancelaciones» que salia siempre aunque fuera de Uber o Cabify.
  4) Tema «Personalizado» con el diseno 3D (la cabecera con la foto y el cartel es igual en los tres temas; SOS 3D, barra de abajo con iconos 3D, iconos en tarjetas y circulos, fondo liso, menu de Ajustes claro).
     Claro y Oscuro NO cambian. Los dibujos de las filas de Ajustes (SOS, Rentabilidad, Tasa, Nominas, Tema, Cuenta) son iguales en los tres temas.
  Nada mas cambia, salvo el numero de version (v3.72). Hay que COMPILAR y volver a instalar la APK (la pagina va dentro).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v371.py (la v3.71).
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "mHNOloRkXSXTUkOXMnz79uzt2f8DxazMAw=="
)
SHA = "481ceae7c88a299acf351112f6c95b1c0745bbcf1510da5f8793cee03a7cf254"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.71';"
V_NEW = "const APP_VERSION='v3.72';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v372.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.71 que espero (¿has pasado v371.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.72')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.71 -> v3.72')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.71 (esperaba const APP_VERSION=\'v3.71\'). Pasa v371.py primero y luego este. No toco nada.')
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

print('v3.72:')
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

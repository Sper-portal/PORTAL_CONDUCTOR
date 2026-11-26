# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.76)

Cambios pedidos por Juan (26-11):
  1) Cobro con datafono: al apuntar un viaje salen tres botones: Efectivo (igual que siempre), App (tarjeta roja = pago por la aplicacion; es lo que antes se llamaba Tarjeta) y Datafono (tarjeta azul con contactless = tarjeta fisica con el aparato del jefe). El datafono cuenta como TARJETA y nunca como efectivo, aunque la plataforma lo marque como efectivo. Tambien sale en la ventana del efectivo de Bolt, Uber y Cabify («Lo ha pagado con datafono»).
  2) Facturacion (diaria, semanal y mensual): debajo de Tarjeta salen dos islas del mismo tamano que las demas, App y Datafono (suman la Tarjeta). El Informe tiene filas nuevas: Tarjeta por App, Tarjeta por datafono y Cobrado con el datafono (lo que pagaron los clientes). El Efectivo sigue siendo lo que hay que entregar.
  3) Editar un viaje (Calculadora): se puede pasar entre Efectivo, App y Datafono.
  4) Jenny y la Ayuda explican el datafono.
  De regalo: la ventana del efectivo decia «Importe de Uber» aunque fuera Bolt o Cabify; ahora dice «Importe del viaje».
  Nada mas cambia, salvo el numero de version (v3.76). Hay que COMPILAR y volver a instalar la APK (la pagina va dentro).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v375.py (la v3.75).
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "/L9BlsUXjo1EfvRoVNirPXt2+ezy/yF2tiI="
)
SHA = "b7bdefbac8a2861a99257886af7b4cacf6590b6f55fdc0c8af993341b835fe9e"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.75';"
V_NEW = "const APP_VERSION='v3.76';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v376_definitiva.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.75 que espero (¿has pasado v375.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.76')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.75 -> v3.76')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.75 (esperaba const APP_VERSION=\'v3.75\'). Pasa v375.py primero y luego este. No toco nada.')
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

print('v3.76:')
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

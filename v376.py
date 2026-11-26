# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.76)

Cambios pedidos por Juan (26-11):
  1) Cobro con datafono: al apuntar un viaje salen tres botones: Efectivo (igual que siempre), App (tarjeta roja = pago por la aplicacion; es lo que antes se llamaba Tarjeta) y Datafono (tarjeta azul con contactless = tarjeta fisica con el aparato del jefe). El datafono cuenta como TARJETA y nunca como efectivo, aunque la plataforma lo marque como efectivo. Tambien sale en la ventana del efectivo de Bolt, Uber y Cabify («Lo ha pagado con datafono»).
  2) Facturacion (diaria, semanal y mensual) e Informe: la tarjeta se reparte en App y Datafono, y sale cuanto se ha cobrado con el datafono (lo que pagaron los clientes). El Efectivo sigue siendo lo que hay que entregar.
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
)
SHA = "0d2321835e39b9128d28df9e94b33175f3104a6b5befaaad1d70dc337af07865"

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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v376.py. No se ha cambiado nada.')

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

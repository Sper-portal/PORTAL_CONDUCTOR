# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.78 · version oficial 1.0)

Cambios pedidos por Juan (26-11):
  1) Cobro con datafono: al apuntar un viaje salen tres botones: Efectivo (igual que siempre), App (tarjeta roja = pago por la aplicacion; es lo que antes se llamaba Tarjeta) y Datafono (tarjeta azul con contactless = tarjeta fisica con el aparato del jefe). El datafono cuenta como TARJETA y nunca como efectivo, aunque la plataforma lo marque como efectivo. Tambien sale en la ventana del efectivo de Bolt, Uber y Cabify («Lo ha pagado con datafono»).
  2) Facturacion (diaria, semanal y mensual): debajo de Tarjeta salen dos islas del mismo tamano que las demas, App y Datafono (suman la Tarjeta). El Informe tiene filas nuevas: Tarjeta por App, Tarjeta por datafono y Cobrado con el datafono (lo que pagaron los clientes). El Efectivo sigue siendo lo que hay que entregar.
  3) Editar un viaje (Calculadora): se puede pasar entre Efectivo, App y Datafono.
  4) Jenny y la Ayuda explican el datafono.
  De regalo: la ventana del efectivo decia «Importe de Uber» aunque fuera Bolt o Cabify; ahora dice «Importe del viaje».
  Nada mas cambia, salvo el rotulo de version: arriba a la derecha pone «Driver 1.0» (antes «v3.15h lector») y en Informacion pone «Version 1.0» y la compilacion v3.78. Hay que COMPILAR y volver a instalar la APK (la pagina va dentro).
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Se pasa sobre la pagina de la v3.75 (el bloque de pegar la recupera solo de GitHub antes de pasarlo).
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "29A0dhneFy/OX5z/D4ZUraY="
)
SHA = "1a4415b822b7ba42a056ff6f68eec4c379dd3a1608c952902ae3e1dbefe2ff5f"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.75';"
V_NEW = "const APP_VERSION='v3.78';const APP_RELEASE='1.0';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v378.py. No se ha cambiado nada.')

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
        say('Numero de version', 'ya', 'ya es v3.78 (version 1.0)')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.75 -> v3.78 (version 1.0)')
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

print('v3.78 (version 1.0):')
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

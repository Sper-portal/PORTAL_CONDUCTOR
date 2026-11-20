# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.62)

Cuentas (Juan, 19-11 19:33): una cuenta DISTINTA empieza de cero, AUTOMATICAMENTE y sin preguntar, aunque sea en el mismo movil (tambien la tasa de finalizacion y lo guardado del lector). Antes se guarda copia en el movil.

Aeropuerto: la tabla «Ajuste por distancia» (viajes largos) vale tambien en los viajes HACIA el aeropuerto (la recogida en el aeropuerto sigue como estaba).

Rentabilidad: se enciende sola la primera vez que activas el lector. Ayuda en pantalla para el interruptor gris de Accesibilidad («Ajustes restringidos» de Android 13 o superior).

Ofertas «Asignar» de Bolt: solo cuentan como oferta cuando llevan N segundos seguidos en pantalla (30 de fabrica, se cambia entre 5 y 300 en la pantalla de la tasa). Si «Asignar» pasa a «Aceptar», cuenta como una oferta normal.

Cartel plegable del neto: el aviso sale pequeño (veredicto, tres datos y neto) con la lengüeta «Más datos» y, debajo, los botones «✕ No la hice» y «✓ La acepté» (cuentan en la tasa de finalizacion).
  Lengüeta: nivel 1 = 4 lineas sencillas (viaje, recogida, bruto y comision, «Es una reserva») + boton «Cálculo completo»; nivel 2 = todas las lineas de siempre. Ajustes de Bolt → General → «Cartel plegado» (encendido de fabrica; apagado = aviso entero como antes).
  Etiqueta RESERVA en el aviso cuando la oferta es una reserva.

Lista de viajes (Ajustes → Rentabilidad → «Viajes guardados (lengüeta)»): flechita «Lista de viajes y datos que enseña» con el boton «Abrir lista de viajes» y 2 interruptores APAGADOS de fabrica:
  «Neto y datos del neto» y «Datos del albarán y de la calculadora» (ajustes de este movil). Apagados, la lista solo enseña hora, tipo y como acabo, y cada viaje solo «¿Cómo acabó este viaje?». Los viajes se guardan igual.
«¿Cambió el trayecto o el precio?»: opcion nueva «Es una reserva (se cobra distinto)».
Ayudas (guia y Jenny) al dia.

  Cambia www/index.html, OfferAnalyzer.java, ScreenReaderService.java y ScreenReaderPlugin.java y crea TabLogic.java. No toca el manifiesto, la camara ni la nube.
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v361.py (la v3.61). Hay que volver a compilar la APK.
"""



import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "8e5a12922a67baf75c42da308f1789f4c6700128705b7fe420fe0be87678aa3b"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.61';"
V_NEW = "const APP_VERSION='v3.62';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v362.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.61 que espero (¿has pasado v361.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.62')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 61:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.61 -> v3.62')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.61 (esperaba const APP_VERSION=\'v3.61\'). Pasa v361.py primero y luego este. No toco nada.')
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

print('v3.62:')
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

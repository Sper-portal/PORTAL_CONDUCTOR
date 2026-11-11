# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.45)

NUEVO: COMPARATIVA EN EL INFORME. La pestana Informe ahora tiene tres lengüetas: Semana, Mes y Personalizado.
  Semana: lo que llevas facturado esta semana (de lunes a hoy) contra la semana pasada hasta el mismo dia, con flechas ▲▼ verdes/rojas.
  Mes: del dia 1 a hoy contra el mes anterior hasta el mismo dia.
  En las dos: total de todas las apps (facturacion, viajes, horas, € por hora), grafico y una tarjeta por aplicacion con los colores de cada una.
  Al tocar una app: su desglose por dia (y al tocar un dia, sus viajes uno a uno). El informe de siempre (PDF, comision, gasolina, km) sigue en «Personalizado»
  y tambien con el boton «Informe completo» de abajo.
  Las horas solo las guarda la app como «prioritaria» u «Otras apps», asi que las horas y los € por hora salen para tu app prioritaria y para las otras juntas.
  Solo cambia index.html (no crea archivos nuevos). Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez.
  Pasalo despues de v344.py. Hay que volver a compilar la APK.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "b3a4f87fc93f22475e24ac7937e4894da39631ab7467ef153a4f5ab1eab9084e"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.44';"
V_NEW = "const APP_VERSION='v3.45';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v345.py. No se ha cambiado nada.')

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


def short(t, n=70):
    t = ' '.join(t.split())
    return t if len(t) <= n else t[:n] + '...'


def part_file(entry, extra_version):
    """Devuelve el texto nuevo del archivo, o None si no hay que escribirlo (ya estaba, o no se puede)."""
    path, name, edits = entry['path'], entry['name'], entry['edits']
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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.44 que espero (¿has pasado v344.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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


def part_version(base_text, newer_ok=False):
    t = base_text
    if t is None:
        t, err = read(HT)
        if t is None:
            say('Numero de version', 'no', err)
            return None
    if t.count(V_NEW) == 1:
        say('Numero de version', 'ya', 'ya es v3.45')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 45:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.44 -> v3.45')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.44 (esperaba const APP_VERSION=\'v3.44\'). Pasa v344.py primero y luego este. No toco nada.')
    return None


# ------------------------------------------------------------------ ejecucion: todo se calcula antes de escribir nada
writes = {}
html_text = None
for entry in PAY['files']:
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
        write_atomic(path, text)
    except Exception as e:
        say('Escritura', 'no', 'no he podido escribir ' + path + ': ' + str(e))

print('v3.45:')
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

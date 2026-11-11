# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.46)

NUEVO: CATEGORIAS DE BOLT (Comfort, XL y Premium). La oferta de Bolt trae arriba una palabra, donde pone «Bolt»: Comfort, XL, Premium o Electric.
  La app lee esa palabra y calcula el neto con la tarjeta de ESA categoria. «Electric» y «Bolt» a secas se calculan como siempre (Bolt normal).
  Si no reconoce la palabra, usa el Bolt normal (no se rompe nada).
  De fabrica cada categoria lleva tus precios de hora VALLE de las tres zonas (los de tu pantalla de tarifas de Bolt).
  La hora PUNTA de las categorias va APROXIMADA (la tarjeta de punta del Bolt normal mas la misma diferencia): pon tus precios reales en
  Ajustes → Rentabilidad de viajes → Estimacion de Bolt → Tarjetas → Categorias de Bolt (Comfort, XL y Premium, cada una con 6 tarjetas).
  En el aviso de la oferta la linea de la tarjeta dice «Tarjeta Comfort de zona media · valle» (o XL / Premium). La prueba de Ajustes tiene un selector de categoria.
  La recogida en el aeropuerto sigue con la tarjeta del aeropuerto aunque la oferta sea de una categoria.
  Cambia index.html, OfferAnalyzer.java, BoltConfig.java y ScreenReaderService.java (no crea archivos nuevos). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v345.py. Hay que volver a compilar la APK.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "769e1b2aefb9901e769cb72f216eb8450d80cd42413a85d25083da68c9ce2d07"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.45';"
V_NEW = "const APP_VERSION='v3.46';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v346.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.45 que espero (¿has pasado v345.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.46')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 46:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.45 -> v3.46')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.45 (esperaba const APP_VERSION=\'v3.45\'). Pasa v345.py primero y luego este. No toco nada.')
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

print('v3.46:')
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

# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.43)

NUEVO 1: MI TASA DE FINALIZACION (Ajustes -> «Tasa de finalizacion»). Tu cuenta propia, de lunes a domingo y por meses, porque Bolt no enseña la suya.
  - Toda oferta que lee la app suma a «Recibidas». Si trae el cartel «Fuera del radio / Rechazar no afectara tu tasa de aceptacion» suma tambien a «Con aviso» y NO cuenta
    (si la aceptas con ✓ pasa a contar).
  - Sin cartel y sin ✓: cuenta como no aceptada y baja la tasa. ✓ y la haces: sube. ✓ y luego la borras de la lista: es una cancelacion y baja.
  - Si el cliente cancela a los pocos minutos (3 por defecto, se cambian) no penaliza: te sale una pregunta al borrar el viaje.
  - Pagina con «Semanal» y «Mensual», anillo con el porcentaje, margen hasta el 85 %, y cada dia se puede corregir con − + ✎ (tambien dias pasados).
  - Avisos grandes (naranja desde 90 %, rojo por debajo de 85 %; los limites se cambian) cuando cancelas o dejas pasar una oferta.
  - Todo se queda en tu movil. Es una estimacion: la tasa interna de Bolt no se ve.
NUEVO 2: la barra ✗ / ✓ de la lengüeta baja abajo, encima del menu (arriba la tapaba el aviso del neto estimado). Con la lista de viajes abierta se queda arriba.
NUEVO 3: CAMARA. Si el video salia al reves (boca abajo): ahora se orienta con el sensor del movil, y en «Grabacion finalizada» hay un boton
  «Se ve al reves: girar 180°» que gira ese video y recuerda la correccion para los siguientes.
  El instalador crea 2 archivos nuevos de Java (RateNotice.java y Mp4Rotate.java) y cambia 5 de Java, index.html y el numero de version.
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v342.py. Hay que volver a compilar la APK.
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "4b4967278a8077831ab9d1e0f7935dd634b01aaf0f3b59a93a49b41d26da018e"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.42';"
V_NEW = "const APP_VERSION='v3.43';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v343.py. No se ha cambiado nada.')

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
    for i, (old, new) in enumerate(edits):
        cn = s0.count(new)
        co = s0.count(old)
        if cn == 1:
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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.42 que espero (¿has pasado v342.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
        return None
    if all(x == 'A' for x in st):
        say(name, 'ya', 'ya estaba aplicado')
        return None
    if any(x == 'A' for x in st):
        say(name, 'no', 'esta a medias (%d de %d trozos ya estan y el resto no); no toco nada. Mandame una captura.' % (st.count('A'), len(st)))
        return None
    s = s0
    for i, (old, new) in enumerate(edits):
        if s.count(old) != 1:
            say(name, 'no', 'el trozo %d de %d ha dejado de ser unico mientras lo aplicaba (%s); no toco nada' % (i + 1, len(edits), short(old)))
            return None
        s = s.replace(old, new, 1)
    say(name, 'ok', 'aplicado (%d cambios)' % len(edits))
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


def part_version(base_text):
    t = base_text
    if t is None:
        t, err = read(HT)
        if t is None:
            say('Numero de version', 'no', err)
            return None
    if t.count(V_NEW) == 1:
        say('Numero de version', 'ya', 'ya es v3.43')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.42 -> v3.43')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.42; pasa v342.py primero si quieres que ponga v3.43)')
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
nv = part_version(base)
if nv is not None:
    writes[HT] = nv
if any(r[1] == 'no' for r in RES):
    writes = {}   # si una parte no se puede aplicar, no se toca nada (ni siquiera el numero de version)
for path, text in writes.items():
    try:
        write_atomic(path, text)
    except Exception as e:
        say('Escritura', 'no', 'no he podido escribir ' + path + ': ' + str(e))

print('v3.43:')
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

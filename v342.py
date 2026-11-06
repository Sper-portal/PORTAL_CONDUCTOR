# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.42)

NUEVO: GRABAR VIDEO DEL VIAJE (como una dashcam). Lo empiezas tu, cuando quieres. No graba nada solo.
  1) Arriba, en la tarjeta «Tu impulso de hoy» (Calculadora), hay un boton pequeño con una camara.
  2) Lo pulsas, eliges 15 o 30 minutos y con o sin audio. Graba el interior del coche en Full HD.
  3) Mientras graba ves «● 29:58» en esa esquina (y en otras pestañas, arriba a la derecha). Android tambien enseña un aviso y un punto verde: es normal y no se puede quitar.
  4) Al acabar sale «Grabacion finalizada» con la duracion y el tamaño (30 minutos ≈ 1,4 GB) y eliges: Guardar y descargar en el movil (queda en la Galeria,
     carpeta Portal del Conductor) o Eliminar.
  El video se queda en TU movil: no se sube a internet, no gasta datos y no usa tu base de datos.
  No toca nada de Uber, Bolt, la subida a la nube ni tus datos.
  El instalador crea 3 archivos nuevos de Java y cambia 4 cosas: AndroidManifest.xml (permisos de camara y microfono), MainActivity.java, index.html y el numero de version.
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v341.py. Hay que volver a compilar la APK
  (la primera vez que grabes, Android pedira permiso de camara, y de microfono si eliges «Con audio»).
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "v3t/8XOXAt+g=="
)
SHA = "416b8bcda3303c120639dba3d5c378e0cc2b6e4716784ba766302c91d1caa367"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.41';"
V_NEW = "const APP_VERSION='v3.42';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v342.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.41 que espero (¿has pasado v341.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
            say(name, 'no', 'ya existe %s y es distinto; no lo toco (¿tenias otra version de la grabadora?)' % path)
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
        say('Numero de version', 'ya', 'ya es v3.42')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.41 -> v3.42')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.41; pasa v341.py primero si quieres que ponga v3.42)')
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

print('v3.42:')
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

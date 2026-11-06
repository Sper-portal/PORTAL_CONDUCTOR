# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.40)

CAMBIOS: MENOS DATOS DEL MOVIL (Bolt, Uber y Cabify: no cambia nada de lo que ves)
  - Antes la app subia tus datos a la nube cada ~45 segundos mientras hubiera cambios (unos 3 GB al mes de tu plan de datos).
  - Ahora sube COMO MUCHO UNA VEZ POR HORA, y ademas al dejar la app (si hace mas de 5 minutos de la ultima subida) y al pasar a segundo plano.
  - «Cerrar sesion» sube primero lo pendiente (espera como mucho 4 segundos si la nube va lenta) y despues pregunta.
  - «Sincronizar ahora» sigue subiendo al momento. Sin conexion no pasa nada: lo pendiente queda marcado y sube cuando vuelve.
  - La copia de la nube puede ir hasta 1 hora por detras de tu movil; en el movil nunca se pierde nada.
  El instalador busca textos concretos de tus archivos (los que dejo la v3.39). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v339.py. Hay que volver a compilar la APK.
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "602cc366d88b48239d8d3714e3d61149bbb54779c61100c097a41b771016d787"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.39';"
V_NEW = "const APP_VERSION='v3.40';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v340.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.39 que espero (¿has pasado v339.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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


def part_version(base_text):
    t = base_text
    if t is None:
        t, err = read(HT)
        if t is None:
            say('Numero de version', 'no', err)
            return None
    if t.count(V_NEW) == 1:
        say('Numero de version', 'ya', 'ya es v3.40')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.39 -> v3.40')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.39; pasa v339.py primero si quieres que ponga v3.40)')
    return None


# ------------------------------------------------------------------ ejecucion: todo se calcula antes de escribir nada
writes = {}
html_text = None
for entry in PAY['files']:
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

print('v3.40:')
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

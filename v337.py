# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.37)

CAMBIOS: CODIGOS POSTALES DE MADRID (solo Bolt; Uber y Cabify no cambian)
  - Faltaban 10 codigos postales de Madrid en tus listas. Ahora se ponen solos, cada uno en su zona:
        zona baja : 28011 28017 28024 28027 28051 28052 28053
        zona media: 28040 28046 28048
    Solo se anade el que no esta en NINGUNA de tus tres listas. Lo que ya tenias puesto no se mueve ni se quita. Se hace una sola vez.
  - El cuadro de codigos postales de Ajustes ya deja escribir bien: puedes separar con espacio, coma o punto, y tambien pegar varios seguidos (de 5 cifras cada uno).
    El teclado ya no es solo de numeros, para poder poner el espacio.
  - Si quitas un codigo a proposito, no vuelve.
  El instalador busca textos concretos de tus archivos (los que dejo la v3.36). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v336.py. Hay que volver a compilar la APK.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "c6c902b5b060d21cf00d580c1685c0d02606a5f0dd97857275f14067f5f06b51"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.36';"
V_NEW = "const APP_VERSION='v3.37';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v337.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.36 que espero (¿has pasado v336.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.37')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.36 -> v3.37')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.36; pasa v336.py primero si quieres que ponga v3.37)')
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

print('v3.37:')
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

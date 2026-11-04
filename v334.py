# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.34)

CAMBIOS (solo Bolt; Uber y Cabify no cambian)
  - HORA PUNTA: la tarifa de punta solo se usa en los viajes CORTOS (menos de 6,5 km, editable). Los largos, con la tarifa de valle.
  - VIAJES LARGOS CON DEMANDA: desde 10 km (editable) la tarjeta baja un 13 % (editable) antes de multiplicar por la demanda. El aeropuerto no se toca.
  - LUGARES DE EVENTOS (IFEMA, Bernabeu, Metropolitano, Palacio Vistalegre, WiZink Center): tarifa normal, SIN ese descuento. Es una suposicion tuya
    (solo se ha visto un viaje a IFEMA); se puede apagar en Ajustes -> Bolt -> Demanda. Se detecta por el texto de la oferta y por la ubicacion de recogida.
  - El extra del inicial en viajes cortos con demanda viene apagado de fabrica (0 y 0); si lo habias cambiado, se respeta.
  - Los ajustes que ya tenias guardados se pasan a estas reglas una sola vez (se conservan comision, tasa de aeropuerto, tarjetas y franjas que hubieras cambiado).
  - Ajustes -> Bolt: casillas nuevas en General (km de la punta) y en Demanda (viajes largos y lugares de eventos), con su prueba.
  - El aviso de la burbuja dice «Viaje largo con demanda: precio base -N %» o «Lugar de evento (X): sin descuento», y «Hora punta, pero es un viaje largo».
  El instalador busca textos concretos de tus archivos (los que dejo la v3.33). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v333.py. Hay que volver a compilar la APK.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "SIFbSB+vIra4bPM58B9S9F+vPR5f8DgYZOEA=="
)
SHA = "82e415948d2327eec2e495af77f4eee9b2c82291e4bc4f7ce11dc7f85ceb0299"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.33';"
V_NEW = "const APP_VERSION='v3.34';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v334.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.33 que espero (¿has pasado v333.py?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.34')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.33 -> v3.34')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.33; pasa v333.py primero si quieres que ponga v3.34)')
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

print('v3.34:')
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

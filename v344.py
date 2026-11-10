# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.44)

NUEVO 1: LA CALCULADORA DA SIEMPRE UN SOLO NETO. Nunca mas «entre X y Y»: sale «Neto estimado: 7,09 €» (en el aviso, en la voz y en la bandeja).
  Se quito el extra de los viajes cortos con demanda: con tus viajes de verdad hacia que la estimacion se pasara casi 3 € en los cortos.
  Sin ese extra el error medio es 1,26 € por viaje (8,8 %); el 60 % de los viajes queda a menos de 1 € y el 80 % a menos de 2 €.
  Las tarjetas de precios y el descuento de los largos no se tocan (probados con tus ~170 viajes: no mejoraban de forma fiable).
  Es de fabrica: no hay que tocar ningun ajuste. Lo que ya tuvieras guardado en «viajes cortos» se ignora (no se borra).
NUEVO 2: «Cuenta» y «Configuracion de la app»: la flecha ← vuelve a Ajustes (ya no abre sola el menu lateral). Desde el menu lateral sigue como siempre.
NUEVO 3: En Rentabilidad hay una isla nueva «Ajustes de rentabilidad» arriba del todo con: Activar rentabilidad, Odometro automatico y Viajes guardados.
  Ya no estan sueltos en Ajustes. Las secciones de Rentabilidad quedan en este orden: isla, objetivos, burbuja flotante, semaforos, opciones avanzadas,
  estimacion de Bolt, Guardar, probar el aviso, estado de la lectura, diagnostico, como se calcula. En la estimacion de Bolt el apartado de demanda
  se llama «Demanda y viajes largos» y los apartados van en este orden: General, Zonas y mapa, Tarjetas, Horas punta, Aeropuerto, Demanda, Voz.
  La lista de Ajustes queda en este orden: Rentabilidad de viajes, Tasa de finalizacion, Configuracion de la app, Tema y Cuenta (la mas delicada, al final).
  El instalador cambia index.html y OfferAnalyzer.java (no crea archivos nuevos). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v343.py. Hay que volver a compilar la APK.
"""


import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "e0a7c5bb47fe163ac75870bfdce6f31906c225adf817504e6e16d82835dcd8e5"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.43';"
V_NEW = "const APP_VERSION='v3.44';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v344.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.43 que espero (¿has pasado v343.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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


def part_version(base_text):
    t = base_text
    if t is None:
        t, err = read(HT)
        if t is None:
            say('Numero de version', 'no', err)
            return None
    if t.count(V_NEW) == 1:
        say('Numero de version', 'ya', 'ya es v3.44')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.43 -> v3.44')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.43 (esperaba const APP_VERSION=\'v3.43\'). Pasa v343.py primero y luego este. No toco nada.')
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

print('v3.44:')
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

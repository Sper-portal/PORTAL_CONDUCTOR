cd /workspaces/PORTAL_CONDUCTOR && git add -A && git commit -m "v3.48 barras del informe, categoria en viajes y Child Seat valle" && git push && SHA=$(git rev-parse HEAD) && echo "Esperando a GitHub..." && until [ -n "$(gh run list --commit $SHA --json databaseId -q '.[0].databaseId')" ]; do sleep 5; done && gh run watch $(gh run list --commit $SHA --json databaseId -q '.[0].databaseId') --exit-status && echo "COMPILADO OK"# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.48)

INFORME DE FACTURACION - BARRAS NUEVAS (Semana, Mes, detalle de cada app y Comparar; tema claro y oscuro):
  - Las barras son mas oscuras (la actual en azul fuerte, la anterior en gris mas marcado).
  - Toca un grupo de barras y sale un cuadrito con lo facturado (actual y anterior) y la diferencia (verde si facturaste mas, rojo si menos).
    Vuelve a tocar para quitarlo. No se vuelve a pintar la pantalla, asi que no salta.
  - La barra mas baja enseña lo que le falta como un degradado transparente de su mismo color (sin rayas), hasta la altura de la otra.
    En el detalle de cada app, con el color de esa app.

CATEGORIAS DE BOLT - REVISION con todos tus datos:
  - CHILD SEAT (y Booster Seat): la hora VALLE ya lleva tus precios reales (baja 3,80 · 0,92 · 0,15 · min 7,30 / media 3,00 · 0,89 · 0,17 · min 7,85 /
    alta 2,77 · 0,99 · 0,18 · min 7,80). Antes iba igual que la punta. Si guardaste los de antes sin tocarlos, pasan solos; si los habias cambiado tu, se respetan.
  - COMFORT, XL y PREMIUM, zona media en valle: el precio por minuto es el de tu pantalla de Bolt (Comfort 0,17 · XL 0,25 · Premium 0,21; antes 0,18 · 0,26 · 0,22).
    Misma regla: si lo tenias de fabrica pasa solo; si lo habias cambiado, se respeta.
  - El resto de categorias (km, minuto y minima de baja y alta en valle y todas las de hora punta, y el aeropuerto) ya coincidian con tus capturas.
    Las tarjetas de Bolt (la normal) no se tocan.

VIAJES GUARDADOS - CATEGORIA EN CADA VIAJE:
  - Cada viaje lleva su categoria (Bolt, Comfort, XL, Premium, Child Seat): la que trae la oferta. En la lista sale una etiqueta (no sale en Bolt normal);
    dentro del viaje sale en la Calculadora y es lo primero del Desglose del albarán, donde tambien la puedes elegir o corregir a mano (viajes añadidos desde el albarán).
  - Sale como ultima columna «Categoría» del CSV que exportas.
  - «Por categoría»: en la lista y en cada jornada cerrada, un resumen por categoria con cuantos viajes, el estimado y, con los que tienen albarán, estimado contra real y la diferencia.

  Cambia index.html, OfferAnalyzer.java y BoltConfig.java (no crea archivos nuevos). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v347.py. Hay que volver a compilar la APK.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "6a5ef1f3eeebb0b95c503a4b12eec15422e7bb094732fc806e443c8980ae68b5"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.47';"
V_NEW = "const APP_VERSION='v3.48';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v348.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.47 que espero (¿has pasado v347.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.48')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 48:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.47 -> v3.48')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.47 (esperaba const APP_VERSION=\'v3.47\'). Pasa v345.py, v346.py y v347.py primero y luego este. No toco nada.')
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

print('v3.48:')
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

# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.35)

CAMBIOS: VIAJES GUARDADOS (solo Bolt; Uber y Cabify no cambian)
  - Arriba de la Calculadora hay una lengueta pequeña (▾), siempre recogida. Al tocarla (o deslizarla hacia abajo) se abre la lista de viajes del dia.
  - Cuando sale una oferta de Bolt, la app la apunta y arriba aparece un aviso con ✗ (no la haces: se borra) y ✓ (la aceptas: pasa a la lista del dia).
    Lo que no decides pasa a «Ofertas sin decidir» (por si aceptaste y se te olvido el ✓). Para pulsar ✗/✓ el Portal tiene que estar a la vista (pantalla dividida).
  - La lista: Viaje 1, 2, 3... con la hora y el neto estimado. Botones: Nuevo viaje, Leer albaran de Bolt, Cerrar y guardar (archiva el dia), Limpiar lista,
    Jornadas cerradas y Exportar (CSV, para Excel).
  - El detalle de cada viaje: pestaña «Calculadora (Estimacion)» con los datos de la oferta y pestaña «Albaran (Desglose)» con neto, tarifa base, alta demanda,
    espera, aeropuerto, comision y bruto. «Capturar albaran» lee la pantalla de Bolt (el albaran a la vista); si es largo se pulsa dos veces (arriba y abajo).
    Lo que no se lea se escribe a mano. Se compara el neto estimado con el real.
  - Ajustes: interruptor «Viajes guardados (lengueta)» para encenderlo y apagarlo.
  - Los viajes se guardan en el movil (no en la nube) y por usuario. Si borras los datos de la app o la desinstalas, se pierden: exporta el CSV de vez en cuando.
  El instalador busca textos concretos de tus archivos (los que dejo la v3.34). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v334.py. Hay que volver a compilar la APK.
"""
import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "c7ed928a28f85e1c2fa3be8423c29f25ffc9dfc62eec3cbd6e13f728b8fb9f31"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.34';"
V_NEW = "const APP_VERSION='v3.35';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v335.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.34 que espero (¿has pasado v334.py?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.35')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.34 -> v3.35')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.34; pasa v334.py primero si quieres que ponga v3.35)')
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

print('v3.35:')
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

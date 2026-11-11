# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.47)

NUEVO: AEROPUERTO (recogidas). Reglas nuevas con tus viajes del miercoles 11-nov (el 118 y el 121) y tus tarifas de pasajero de Bolt.
  - Recogida de hasta 11 km: el cliente paga la MINIMA (13,70 € en Bolt) y la TASA (2,57 €) APARTE, encima. Tu neto sale de la minima sola:
    recogida de 10,6 km -> 13,70 + 2,57 = 16,27 (16,25 como en el albarán); sin la tasa quedan 13,68; comision 25 %: neto 10,26 €.
    La demanda multiplica la minima pero NO la tasa.
  - Recogida de mas de 11 km: se calcula como hasta ahora (inicial + km + minutos), con la tasa ya dentro y restada antes de la comision.
  - Tarjeta del aeropuerto nueva (tarifa de pasajero de Bolt): 3,04 · 0,86 · 0,15 · minima 13,70. Si la tenias de fabrica (la de antes), pasa sola a la nueva;
    si la habias cambiado tu, se respeta.
  - Comfort, XL y Premium tienen su PROPIA tarjeta de aeropuerto (recogidas): Comfort 3,56 · 1,01 · 0,17 · min 16,00 / XL 5,20 · 1,47 · 0,25 · min 23,40 /
    Premium 4,41 · 1,25 · 0,22 · min 19,85. Estan en Ajustes → Rentabilidad de viajes → Estimacion de Bolt → Aeropuerto (valle y hora punta; la punta va igual que el valle hasta que tengas el precio real).
    El aviso dice «Aeropuerto (recogida) · tarjeta Comfort del aeropuerto · valle». La prueba del aeropuerto tiene el selector de categoria.

INFORME DE FACTURACION:
  - Pestañas Semana y Mes: ademas de la comparacion de «los mismos dias», sale el MES PASADO COMPLETO (o la SEMANA PASADA completa) con su total, viajes, horas y €/hora
    y cuanto llevas ya de ese total. (Antes, con los viajes de octubre desde el dia 14, el mes anterior salia en 0.)
  - Pestaña NUEVA «Comparar»: eliges dos periodos cualesquiera (A y B, de tal dia a tal dia) y se comparan en total, viajes, horas, € por hora, € por dia, € por viaje,
    dias trabajados y cada aplicacion. Los dias en los que solo anotaste el total cuentan con ese total (0 viajes); si no hay nada, sale 0,00 €. Atajos: esta semana / la pasada,
    este mes / el anterior, mes pasado / el anterior.

TARJETAS DE PRECIOS (Ajustes → Rentabilidad de viajes → Estimacion de Bolt):
  - Salen como botones cerrados: Bolt, Comfort, XL, Premium y Child Seat. Solo ves los numeros cuando tocas el boton. Lo mismo en Aeropuerto.

HORA PUNTA DE COMFORT, XL Y PREMIUM: ya llevan minima, km y minuto REALES de tu pantalla de tarifas de Bolt (Las Rozas, 11-nov): baja (Bolt 8,90), media (Bolt 7,90) y alta (Bolt 8,50).
  El "Inicial" de Comfort baja/media, Premium baja/media y XL media salia inflado por la demanda: Comfort usa el de Child Seat + 0,04 y Premium/XL el de fabrica de antes.
  Si tenias guardados los de fabrica de antes (aproximados), pasan solos a los nuevos; si los habias cambiado tu, se respetan. Las tarjetas de Bolt (la normal) no cambian.

CHILD SEAT (y Booster Seat): categoria NUEVA con su boton en Tarjetas. Se reconoce por la palabra de arriba de la oferta. Hora punta real (baja 3,44 · 0,93 · 0,18 · min 10,25 /
  media 3,50 · 0,97 · 0,23 · min 8,90 / alta 4,13 · 1,06 · 0,24 · min 9,70); la hora valle va igual que la punta hasta que pongas la real; el aeropuerto usa la tarjeta de Comfort.

  Cambia index.html, OfferAnalyzer.java, BoltConfig.java y ScreenReaderService.java (no crea archivos nuevos). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v346.py. Hay que volver a compilar la APK.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "KfrtpA9H0ihry4uLu4+/8hUMkn"
)
SHA = "4d569dc9202ad7f619b1e10b29c266b0ebe9b0973ca4dcdd5593dafa534b2ced"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.46';"
V_NEW = "const APP_VERSION='v3.47';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v347.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.46 que espero (¿has pasado v346.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.47')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 47:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.46 -> v3.47')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.46 (esperaba const APP_VERSION=\'v3.46\'). Pasa v345.py y v346.py primero y luego este. No toco nada.')
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

print('v3.47:')
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

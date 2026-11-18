# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.61)

Movistar Arena y Fabrik en «Madrid hoy»: Ticketmaster casi no trae los conciertos ni los partidos del Movistar Arena (antes WiZink Center), asi que no salia ninguno.
Ahora la app tambien lee la programacion oficial del recinto (movistararena.es/programacion, pagina publica) y las fiestas de Fabrik (sitemap de fabrikmadrid.com: solo fecha y nombre) y las une a Ticketmaster, IFEMA y Deportes SIN pisarlos:
  - lo que ya salia sigue igual; si el Arena trae el mismo evento, se queda el de la otra fuente (no se repite);
  - lo «Cancelado» o «Aplazado» no sale; lo «Entradas agotadas» si (mas gente);
  - un rango «del 19 al 21 de nov.» sale un dia cada uno; si la web no da hora (00:00) sale «Hora por confirmar»;
  - si la web falla o cambia, siguen las demas fuentes y el pie de la pantalla lo dice.
Ayudas (guia, «Como funciona» y Jenny) al dia con esta fuente.

Cuentas (Juan, 18:06: «me abren el mismo»): al CREAR una cuenta nueva, o ENTRAR en una que aun no tiene datos, desde un movil que tenia los datos de OTRA cuenta, la nueva empieza VACIA
(antes heredaba los viajes, el nombre y los ajustes de la otra y se los subia; a la tercera cuenta ni se le subia nada). Antes se guarda copia en el movil y la otra cuenta queda intacta en la nube.
Si el movil no tenia cuenta antes (datos locales de siempre), se conservan y pasan a la cuenta nueva, como hasta ahora.

Tasa de finalizacion (Juan, 18:31: «me sale 100 %»): al unir dos copias del libro de la tasa, un libro casi vacio pero mas reciente ya NO pisa la lista de los ultimos 100 viajes, los limites propios,
el punto de partida ni las cifras de Bolt (la lista se une por viaje).

Botones con voz para el pasajero (Juan, 18:52): el sol de la frase del dia desaparece y en su lugar van 2 botones, «Cinturon» («Por favor, pongase el cinturon de seguridad.») y «Gracias» («Gracias por viajar con nosotros.»).
Tocar = el movil lo dice en voz alta (voz de texto a voz del movil, volumen de multimedia). Mantener pulsado = cambiar el nombre, lo que dice y el idioma (Probar / Guardar / Restaurar). Se guarda en la cuenta.

  Cambia www/index.html (lector del Arena y Fabrik, pie, ayudas, cambio de cuenta y botones con voz), crea SpeakPlugin.java y suma 1 linea a MainActivity.java para registrarlo. No toca el manifiesto, la camara ni la nube.
  Los eventos guardados de la v3.60 se descargan otra vez al abrir Madrid hoy.
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v360.py (la v3.60). Hay que volver a compilar la APK.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "a227550f0bea207198da8d0f187ac4d7f562d914bef5bb234e05c0ef328558bc"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.60';"
V_NEW = "const APP_VERSION='v3.61';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v361.py. No se ha cambiado nada.')

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


def write_atomic_bytes(path, data):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.', suffix='.tmp')
    os.close(fd)
    try:
        with open(tmp, 'wb') as fh:
            fh.write(data)
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
    if entry.get('optional') and not os.path.exists(path):
        say(name, 'ya', 'este archivo no existe en esta copia (no es tu repo completo): se salta')
        return None
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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.60 que espero (¿has pasado v360.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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


def part_asset(entry):
    """Imagen (archivo binario): si ya es igual, ya estaba; si no, se reemplaza (el cartel de arriba)."""
    path, name = entry['path'], entry['name']
    data = base64.b64decode(entry['b64'])
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        say(name, 'no', 'la imagen incluida en este parche esta danada; no toco nada')
        return None
    cur = None
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            cur = fh.read()
    if cur == data:
        say(name, 'ya', 'ya estaba')
        return None
    say(name, 'ok', 'reemplazado' if cur is not None else 'creado')
    return data


def part_json(entry):
    """JSON (package.json): anade las claves que faltan leyendo el JSON, asi no depende de como este escrito. Si ya estan, no toca nada."""
    path, name, ops = entry['path'], entry['name'], entry['json']
    s0, err = read(path)
    if s0 is None:
        say(name, 'no', err)
        return None
    try:
        obj = json.loads(s0)
    except Exception:
        obj = None
    if not isinstance(obj, dict):
        say(name, 'no', path + ' no se puede leer como JSON; no lo toco')
        return None
    pend = 0
    for keys, val in ops:
        d = obj
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
            if not isinstance(d, dict):
                say(name, 'no', 'en %s «%s» no es lo que espero; no lo toco' % (path, k))
                return None
        if keys[-1] not in d:
            d[keys[-1]] = val
            pend += 1
    if not pend:
        say(name, 'ya', 'ya estaba aplicado')
        return None
    m = re.search(r'^([ \t]+)"', s0, re.M)
    out = json.dumps(obj, indent=(m.group(1) if m else '  '), ensure_ascii=False) + ('\n' if s0.endswith('\n') else '')
    say(name, 'ok', 'aplicado (%d cambios)' % pend)
    return out


def part_version(base_text, newer_ok=False):
    t = base_text
    if t is None:
        t, err = read(HT)
        if t is None:
            say('Numero de version', 'no', err)
            return None
    if t.count(V_NEW) == 1:
        say('Numero de version', 'ya', 'ya es v3.61')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 60:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.60 -> v3.61')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.60 (esperaba const APP_VERSION=\'v3.60\'). Pasa v360.py primero y luego este. No toco nada.')
    return None


# ------------------------------------------------------------------ ejecucion: todo se calcula antes de escribir nada
writes = {}
html_text = None
for entry in PAY['files']:
    if 'b64' in entry:
        out = part_asset(entry)
        if out is not None:
            writes[entry['path']] = out
        continue
    if 'json' in entry:
        out = part_json(entry)
        if out is not None:
            writes[entry['path']] = out
        continue
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
        (write_atomic_bytes if isinstance(text, bytes) else write_atomic)(path, text)
    except Exception as e:
        say('Escritura', 'no', 'no he podido escribir ' + path + ': ' + str(e))

print('v3.61:')
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

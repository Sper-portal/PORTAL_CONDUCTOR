# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.55)

SOS COMPLETO (avisos a tus contactos de confianza que tienen la app, aunque su WhatsApp este en silencio):
  - Ajustes -> «SOS y contactos de confianza» -> «Avisos por la app»: invitas a un contacto por su CORREO (el de su cuenta de Driver Hub 360).
    Solo recibe tus avisos si ACEPTA la invitacion. Puedes quitarlo cuando quieras; el tambien puede salirse.
  - «Activar avisos en este movil»: pide permiso de notificaciones y registra el movil. El sonido es de ALARMA (se oye con el movil en silencio);
    para que tambien pase por «No molestar» hay un boton «Sonido y No molestar» que abre el ajuste de Android (solo lo puede activar la persona).
  - Al mantener pulsado el boton SOS: cuenta atras de 5 s (se puede cancelar o «Avisar ya») y se avisa a los contactos con tu ubicacion.
    Les sale una pantalla roja con el mapa, tu telefono para llamarte y «Llamar al 112». Tu pantalla tiene «Ya estoy bien» para cerrar el aviso.
  - Los SMS / WhatsApp / Compartir / 112 de la v3.54 siguen igual.

  Cambia la pantalla (index.html), MainActivity.java, AndroidManifest.xml, package.json y crea SosNotifyPlugin.java e ic_stat_sos.xml.
  No toca la camara ni las carpetas de la Galeria. Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v354.py.
  Hay que volver a compilar (la APK nueva baja el plugin de Firebase). El servidor (tablas + funcion + clave de Firebase) se sube aparte, con Juan presente.
"""


import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "5cbe4f355ebae661f15d92818e899103c61a1fd90b751118f4355377eb4be8a9"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.54';"
V_NEW = "const APP_VERSION='v3.55';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v355.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.54 que espero (¿has pasado v354.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.55')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 55:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.54 -> v3.55')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.54 (esperaba const APP_VERSION=\'v3.54\'). Pasa v354.py primero y luego este. No toco nada.')
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

print('v3.55:')
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

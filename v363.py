# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.63)

Cuatro cambios pedidos por Juan (20-11, 18:24, 18:59, 19:05 y 19:55):
  1) La barra ✗ / ✓ de ABAJO de la app ya no sale de fabrica: el cartel del lector ya trae sus botones ✕ «No la hice» y ✓ «La acepté», y la barra repetia lo mismo.
     Todo lo demas sigue igual (marcar en el cartel, los 90 segundos, «sin decidir», la tasa). Para volver a verla: Ajustes de Bolt → General → «Barra ✗ / ✓ de abajo de la app».
  2) «¿Cómo acabó este viaje?»: «Hecho» pasa a «Aceptado». Aceptado y «Pasajero: sin penalización» van en VERDE y «Cancelé yo» y «Canceló el pasajero» en ROJO, siempre (no solo al marcarlos),
     y en la lista las etiquetas de cancelado salen en rojo. Ayudas al dia.
  3) La línea «Dejarla: 87,5 %  ·  Aceptarla: 90,0 %» (lo que le pasa a tu tasa) sale ahora EN EL CARTEL, encima de los botones ✕ / ✓ (antes solo estaba en la barra de abajo).
     El Portal le pasa al lector la cuenta de la semana y el lector hace la cuenta al leer la oferta (verde / naranja / rojo, aviso «fuera de radio» y «Asignar»).
  4) El cartel (neto, «Más datos» y botones ✕ / ✓) un 20 % más pequeño: letras, huecos y ancho. Los botones ✕ / ✓ quedan algo más altos que el 80 % para acertar con el dedo.

  Cambia www/index.html y 3 archivos Java del lector (TabLogic.java, ScreenReaderPlugin.java, ScreenReaderService.java). No toca manifiesto, camara ni la nube.
  Si algo no encaja, no toca NADA y lo dice claro. Se puede pasar mas de una vez. Pasalo despues de v362.py (la v3.62). Hay que volver a compilar la APK.
"""




import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "RM9VTvLOM29eEDu6UpznCtyGNZID/GWGnLWit6zKePUhjIS/BG8YQ7eVoVA6BAn0EzD8MkiGWZ+JXDjyF3GCY8xNwjSh3/ZqZP3SiHqemmjqe/"
    "hJbUJXK6aYUxTcVHz5l5FqiXzQrnlC4nE7YZJIVEC8Sgd60R06X+VWp9phrpCFDvlOcmz3ECyJAJjsuS7wC3G3wVCUIeNMV+fu7ydyJORRRat+"
    "Ky4XHdvL3RkMh41jGNLMimB12FzYOnmweeXuAnGoST6PURvRzJqrop5sQ0/U5d/+nEtZjlABgEoFWIhZWYKkfuqYwXoquuz2WjctbPZ7Otkt1r"
    "2MzIcGvJ7RcSYCBpDnBsTYyfQV2lxbWkX6Yp82J0p6sBvfMoFmPTSsIQjApfTHnhuABlFqGQVS4yFCC3ftn8vWxdgI7K3Wup9LCtmlB8QYDaE+"
    "GpY4mZZ8fypG8hZzpPLwDPrTTZV+BPEQsEuBEEUm0W0zrEmiKtQ/E+fuUAkof4cujELqRXcPXCD+XFnk8//4zvjeHzSH4p8bso0C/GnY3sarNT"
    "xn+7qJJwl5/7SZz26ZQjOzxFria3bfzVUu7Fdazpg3K99M/m9NqMvUjvFCN3KjJW2WCu6aQ1PI6sEKMJzetHZxK56k4BpRX7v35zOa2kyVQ9JT"
    "6lV59gUM+5ENrWd5g2rlfdQfU6D8QAD6/SC3N759nG97uHbzf3d7frx3wTQgocn2vq19za2TvceVnf9wD0R6+YUSzU1kAUW09Do/agfLtWdzsj"
    "p1fTVxotmobSamnzyvyonZ4X4iuYrJCePm4a4DrkWurN29JHTjNfMtCnRMJp74cObpUEl4qymd/uv3z+x/29w43dGvtYTLlp54JlKpOoasKUPw"
    "ewLY8j3H9mNpr/9HLj4O0WCAbsDNYa6Atw3Lx5jqCQV07k9CHJBZ2QQ36zv7czx1G/nMsTEFooKpTC0ISpzyXRbobDyqG7IoQD6yb46nnv+ebu"
    "zpQ/UZhcRCOK++IcqwQ+k11evymExv+PKqDNCl93PJSWI49D8AjIFlhvpuq/0kb1BLNS5MCSJcKQLXydSJM125IGVf5N7bLMILteUPF1KIuvtx"
    "89gGi+Jcuyxars7Wdb26tr24WGMGvYWN9YVxXA2xvPtjafPcszwvIbMNl7fOXIqF7Sv+6INT9fZRrlgmOMl+o4IUgEfmiA352G01UgqiGUtHzd"
    "mwnF8zf8QnleVQjtNdtaZL1EZ6VXjdM/2at68kgQy7eVg7isaFTlW83v6TC0euBHb0F4/uB9fuLXmSaBdhIJPDypZBvrRl5NXm02jdLJGtGG5B"
    "sQsIXkV5vT6QYZGc4qm2iYmvRs7K7MHU86YVJYI6ubFXL2vXxeOMqq8p9MKxLFSdfkcv4eka5blVS6YaYoCeiavMb5S52kd+UuCWMuuD5j1GaR"
    "dH9epzrS/WtJF+aLDKZeZsuUAF48J6DOUmHNiDnlyuw73OKS8RfgqWnRVGd0W0KnrUdlSL3QIAlpHxW33an3KDd6veff7L1N4WxvZwtsebXZqb"
    "zxOn9AzfuQlPAykALUbT4adKqvqWeJWZTQt0eJwP9uoiY9Q2ApMO4ZbJQIC+7PU8gJ9gtRMvAjh95d9dJPavIpT+VagYOv2U+/oinFxdIg+OJL"
    "EflJCFFSo09CtuX/qfACpHAsfGYLLwIrmJ3RfUkusIxb31VzuLJ9rFVSrhpDWKviL4q6sXxz6lIOWTxEfAGd/Q1lqGq0tG32E8e1N1zYhG/MTG"
    "6IT52h8K2RE5TMAd8MK67BdA8yGOpWJjU3Li0UhKjjNn1Ge60R1/WZYcrcDczzbHvXHjYpKS5Tq+myuGarDPG/fPkjBCBUHXTrzIVLHNeZIkO2"
    "ORfXv7LlfCHv+ruV8lr/QyS4E8XOGJEFMd4fAGjdAGbnFyI0gUfiAvBfBKX+1dX+f34mdTEk86E9Ee/2K167Uvaz6/pK713RryH/ipeHrK7NJl"
    "/tS+RX12aS7yXjsujrM2hXO2bFwWnCNTGxhuqsuFgiWZu7bQ4xYOEHMze6F90YuzpzUukjGfOtmenjF0QYN8msFpyp6tq1dlHbaYalqVLcPHpT"
    "fWaT2+KuNY/cVJ8Z5GaWL1nfDWpqz1P1T7Unr6el7dagLMuXYrD26PM2fSXJ1FLIeleuugfTK1HpIjX3oIbYroQlAE+yt2aeKrDSvg7PfM7Q34"
    "Zz6k6pNum/zEm/CInfx9mrRPRJn6EcKa3ZnEOGdtOZ1t9Sqjrn71+LkPuz0PGbyZvJ/wL0S5zd"
)
SHA = "c8c3bd7b5b003594f3a5a495f17bd31661f48cb6ef47c6d7aef22a7a60f934d7"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.62';"
V_NEW = "const APP_VERSION='v3.63';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v363.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.62 que espero (¿has pasado v362.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.63')
        return None
    m = re.search(r"const APP_VERSION='v3\.(\d+)';", t)
    if newer_ok and t.count(V_OLD) != 1 and m and int(m.group(1)) > 62:
        say('Numero de version', 'ya', 'ya tiene una version mas nueva (v3.%s): este parche ya estaba puesto' % m.group(1))
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.62 -> v3.63')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'no', 'tu index.html no es la v3.62 (esperaba const APP_VERSION=\'v3.62\'). Pasa v362.py primero y luego este. No toco nada.')
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

print('v3.63:')
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

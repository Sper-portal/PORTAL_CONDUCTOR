# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.41)

CAMBIOS: LECTURA DE UBER MAS SEGURA (no cambia nada de Bolt ni de Cabify)
  1) La etiqueta «Viaje largo (mas de 30 minutos)» ya no se confunde con el viaje: antes el aviso decia
     «No se pudo leer la distancia del viaje» en esas ofertas (era el fallo de tu segunda foto).
  2) Uber se lee tambien con la camara (OCR) y la camara se equivoca a veces: «kn» en vez de «km», «rnin» en vez de «min»,
     una «l» en vez de un «1», o el km separado del minuto por la direccion. Ahora se arreglan esas lecturas
     (solo en la lectura por camara; el texto normal no se toca).
  3) Probado con tus tres fotos y con 60.000 pantallas de Uber inventadas con esos fallos: se leen las 4 cifras bien.
  Si una oferta sigue sin leerse, pulsa «Enviar ultima lectura» en Ajustes (Lectura de ofertas) justo despues y mandamela.
  El instalador busca textos concretos de tus archivos (los que dejo la v3.40). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v340.py. Hay que volver a compilar la APK.
"""

import os, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "eNrNWGtz4jgW/SsK1TXYCTGQ9HwY6HQq6cnUUN0JXU12PizQXcIWRI0fjGTn0SG/a7/vL9tzJWPsAP2Y2todqhLL0tXV0X2cK/mxNpWh0LUOGz"
    "7WFjy9QavG40AlMmjyxaKpld+MuIybn/ktb/pJ1FwkKuUhmnGQ+Wmimv3pVKizmIcPX4TySK7WYLWYR4KUvRN+minOAsH+MRGKORVxl0RFIFMD"
    "YVhj+C2UvOWpYDrlqfTZVEKWvedpKlTMLi+u2cnqzQOeBfA7o5pz+mpvOMIv8Bpj1zGtx6PGyyeXmno/ck73hvzwy9nhP8fuqOZ2aWFardlkt8"
    "fey3aHiVT+mYmU6wIr9sgiGWdpohmG2FWfaXRlMUsVj5IOG42yVuvs/A/JPwsWcjVLmBOZzou2UXPcWilwTff5uccGSZgwLZicxYniMdMSU1lo"
    "p/0aC87ihBYQbB55o/ibJuld/db/9Ob33vuthvl4uwZHppgsP9LDOY3sRo2lDqyRnNMO0C5vjM3u9um/e/qCrGVhrGzFHE17CHPXIiKYjPhMxG"
    "4HxpEBD4Q1mAhZ/80HsuM0iwPxHZuB+Ke3lztcLHPHugXcebycK/xJei7nUbwM59FS4m9uZA7QiIZeo9tBUNgIaB3+YiPgO9Fc9q6+G46KASQK"
    "8dfGH3Vbny4jGS0VbPtXQVz33+4GQaGPuLZqTfgP0egnYW85PgAq7H9c6nFPLW5rwGhJsExk/Aigd/2rix1++jg0ERaMH1uN46c8FdtoEo7V29"
    "EqMZ1hKMen82EUKzQwBSPDj8V2xvuIv0axypuzwcWn3tXg4mrQu+79cfEjXtwF1/FMpAc5UcjYGKOMAahAJH+Dnfz32G/cYFvZdpIkoQAp3XDt"
    "DFIl4xnTDWZbwzGb32mXPbIpMn41PGcd2y2n4AWAilPUC+3MXZcpAYIgtsxEd/Uy5aHG29MoXlHw/xFCzmv7+6siwJUSM6LjpExgOhMhOFSgJk"
    "Rwh6AaABlJZB0QubIERS3lOTGC3DPNTfnYwpFsv2mXzfebb2Iq7/u+KnaMPVop+uWd93C+7q676f3eU2IRcl+cheFOQhhS4jsVkn9OVV8jKpcC"
    "d1Rrv2hT7NhCMKqFVNpGNWDAUN52Uh5NJOxj9s7zamCMFgo03Sr4PDO9iKf+jVDOvVvdzYtcr9vdnPf28mvT5lF1FhD7cqpQ86xXUF91h4WmPL"
    "PD16xtWg3Wb/yMudTTsi3r0YWY8QCTOXU1zaQHo4mHMwoFo5tC4VYobLi0zUuLkUU5bDB5CXf3uY/PMzoeMT2BeCzuKr1OWfzuBqmP04YHhggc"
    "txIupZBJkzk0Rd5MJdnCaZc10G+Va0rAQyd5YlRFTKLJOGUSAq0uHq9IqxeKeJbeABOTBwc29ajbv+HqLHWky16fsHqrzn76iVX7X6H/l7q7Wt"
    "Nk5lbsyAgRQMIInhotuZuder/eIO3uuifZ6Ampp13u6W30LPMeMAj0P8MReTgCizj4YKUjEaeOnjRWPvX+zJJUlAct4oPC3keuW7b407q5Un3N"
    "ZQidzwNcT7w0sWZwnoXxqPaziT+k7FHr6IgdeS/ZHDnSWXGWTiaIRZzAcE4NhC8p+Q5Y+/A4D3umOP0/oRzZCFO+zspKgpUwkKd5Hnbk3T2e7/"
    "bYBeh3yZ1Qb7gWzrvE56HwPvT7126uSSM5iXwiubxBfhbszIv4BFJeGA8v4BRK5e4m0kmO1J5EdkOdlKFOCt1/FeqkDHUTXS51n3dRlStKbZFN"
    "BZ134Iu7qwTHZbcyQpUFgz7lJrGbXoQyBSBi8NigoZ2RlIcJkeMW2chAXGanv14Mrs2toLAMbhuRmePmk9yCO2KC4PEgKOtc35F+DHjr68i385"
    "TZ8QkiNEb1SJHteTk0Cik7TeNZfu40wgmYii2X7IeMQMcG3NXElkWKK9a39Rjjl+LRymyswap3z1HtW3dI1OAqrh0+K7FNNfKw2BSxzs47dKqx"
    "t1J2y9nnTKPB41TQaqGpeeUqDhYh9xmyQbzDO0qwCHd2Dt8nDbq+xnhYNYC0yIRen+2+99qIxcyVuwJt0Lu4fP/hogKuSwve8AdzAgukEr4vjb"
    "V+O45JCyEjVIJNMu1ziPqSM56qwqQODpY4qh2TBXEvL7RjYTAjIaABLDPLKBZFlU7yCN2IY5MFvVREoNAOk2joDZk1e+LCGrA9FMJ5neKUe5kW"
    "wc4QpJ9RPRE6pYNBFoZbRIpKTUWz3cUDpfaYAtLOyyeygOr1Gu9kjdfypQEH6XpUz0mT0Bk9HkUdjXHbOmQBHcZzXJMum6BYz7vlSlfhYpLbsz"
    "hont336hBg1FR7FlwqG+R0GCK4w/EjbxjJJ3djnaettfZ/HPmVrKPPYV6WytB7k4QU+TKJtacThZOEmOFeQ/sqC0ULVOc0Ua8GYvbaISMtskmI"
    "awI51jfDwsEYu8edCI8HEllVHfCMgoUP2YNtwUDsiTihnI5/E0jP2aFD9nzgJreRl/YTmzb6cW5By4F/HorPaQ0cd0go+YIH3c9WH+nM8Semb2"
    "h+Bpdx8mWUAI+fzHADYbG0Hea7WCm3871gLYFNaHPYXQ/bIofNaWQLmWl12QSovORqj45leHErig4OulsZhKZUFsR5+Wg7raydgQxYuwJZO6Cz"
    "IiZ7Mh8w5/F04IHjrsR9Sq/kDYv8xAzFeT9h2duxA9dIKhElt8Kp5pk50oyfGmz9wfju7q4JzhD33k0aheWvv1dZJFSSX4w0Ao0IaiX4/ONv/b"
    "35tGzCocX+/a+iUmD6eRKm1FWnOWXB9k5BgBw//Qf6Ig1D"
)
SHA = "af748f4a685fbbbcf66e4dab69ae28b6e420cf7bd19aeaa04b943dc35d30696a"

HT = 'www/index.html'
V_OLD = "const APP_VERSION='v3.40';"
V_NEW = "const APP_VERSION='v3.41';"


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v341.py. No se ha cambiado nada.')

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
            say(name, 'no', 'no encuentro en %s el texto del trozo %d de %d: «%s». Tu archivo no es el de la v3.40 que espero (¿has pasado v340.py antes?). No toco nada.' % (path, i + 1, len(edits), short(edits[i][0])))
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
        say('Numero de version', 'ya', 'ya es v3.41')
        return None
    if t.count(V_OLD) == 1:
        say('Numero de version', 'ok', 'v3.40 -> v3.41')
        return t.replace(V_OLD, V_NEW, 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.40; pasa v340.py primero si quieres que ponga v3.41)')
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

print('v3.41:')
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

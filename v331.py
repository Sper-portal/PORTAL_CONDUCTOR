# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.31)

CAMBIOS
  DEPORTES (nuevo, aparte; lo demas de la app no cambia)
  - Menu -> Deportes: partidos de LaLiga y Champions de hoy y de manana (hora de España), clasificaciones y equipos.
    Los marcadores llegan con retraso: la fuente gratuita (Football-Data) no es en directo.
  - Los partidos que se juegan en estadios de Madrid (Bernabeu, Metropolitano, Vallecas) salen tambien en «Madrid hoy»,
    con su salida estimada. Se pueden apagar con un boton en Deportes.
  - La app NO lleva ninguna clave de deportes: habla con una funcion tuya de Supabase («deportes») que guarda los datos en una cache
    compartida y llama a Football-Data muy pocas veces. Esa funcion se crea aparte (mira PASOS_SUPABASE.txt del paquete).
  - Si la funcion no esta creada o falla, Deportes lo explica y «Madrid hoy» queda exactamente como antes.
  Este instalador solo cambia www/index.html. Se puede pasar mas de una vez. Hay que volver a compilar la APK.
"""
import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
    "xIyz2/8PBf93ow=="
)
SHA = "e5562c41fc78d2553db5901562caeb5da9ab979eeae1433ebb845675e49607bf"

HT = 'www/index.html'
MARK = '/*v331-sports*/'
PART = 'Deportes'


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v331.py. No se ha cambiado nada.')
HTML_EDITS = PAY['html']

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


def part_html():
    t, err = read(HT)
    if t is None:
        say(PART, 'no', err)
        return None
    marks = t.count(MARK)
    if marks > 1:
        say(PART, 'no', 'el bloque v3.31 esta repetido (' + str(marks) + ' veces)')
        return None
    if marks == 1:
        for n, old, new in HTML_EDITS:
            if t.count(new) != 1:
                say(PART, 'no', 'la v3.31 esta a medias en la pagina (falta: ' + n + ')')
                return None
        say(PART, 'ya', 'ya estaba aplicado')
        return None
    if t.count('/*v330-bill*/') != 1 or t.count('/*v330-tema*/') != 1:
        say(PART, 'no', 'falta la v3.30 (Tema y comision); pasala primero')
        return None
    s = t
    for n, old, new in HTML_EDITS:
        c = s.count(old)
        if c != 1:
            say(PART, 'no', n + (' no esta' if c == 0 else ' esta repetido (' + str(c) + ' veces)') + ' en ' + HT + ' (la pagina no es la version esperada)')
            return None
        s = s.replace(old, new, 1)
    if s.count(MARK) != 1:
        say(PART, 'no', 'error interno: la insercion no ha quedado bien')
        return None
    say(PART, 'ok', 'aplicado: pantalla Deportes en el menu y partidos de estadios de Madrid en «Madrid hoy»')
    return s


new_html = part_html()
writes = []
if new_html is not None:
    writes.append((HT, new_html))
for path, text in writes:
    try:
        write_atomic(path, text)
    except Exception as e:
        say('Escritura', 'no', 'no he podido escribir ' + path + ': ' + str(e))

print('v3.31:')
bad = 0
for part, state, text in RES:
    icon = {'ok': 'OK ', 'ya': 'ya ', 'no': 'NO '}[state]
    if state == 'no':
        bad += 1
    print('  ' + icon + part + ': ' + text.replace('\n', '\n      '))
changed = [w[0] for w in writes]
if changed:
    print('Archivos cambiados: ' + ', '.join(changed))
else:
    print('No se ha cambiado ningun archivo.')
if bad:
    print('RESULTADO: hay partes sin aplicar (las lineas «NO» de arriba). Haz una captura de esto y mandamela.')
    raise SystemExit(1)
print('RESULTADO: todo aplicado o ya estaba' + (' (hay que volver a compilar la APK; Deportes necesita ademas los pasos de Supabase)' if changed else ''))

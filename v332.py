# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.32)

CAMBIOS
  DEPORTES DENTRO DE «MADRID HOY» (cambia la pagina de la v3.31; lo demas de la app no cambia)
  - Madrid hoy tiene una pestaña nueva, «Deportes», junto a Hoy, Mañana y Semana: partidos de LaLiga y Champions de hoy y de mañana con su
    resultado, y (con la funcion de Supabase, que ahora es OPCIONAL) tambien Tablas y Equipos.
  - La entrada «Deportes» suelta del menu desaparece: todo esta en un solo sitio.
  - Sin Supabase: la app lee directamente la web publica de ESPN (como ya hace con IFEMA), sin ninguna clave. ESPN no es una fuente oficial:
    puede fallar o cambiar sin aviso. Si tienes la funcion de Supabase, se usa primero (Football-Data) y ESPN queda de respaldo.
  - Los partidos en estadios de Madrid (Bernabeu, Metropolitano, Vallecas) siguen saliendo mezclados con los eventos de Hoy, Mañana y Semana.
  Este instalador solo cambia www/index.html y necesita la v3.31 puesta. Se puede pasar mas de una vez. Hay que volver a compilar la APK.
"""
import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "b23609d0d4101fad903ad48d9a578b3bf09225e820e1ee48d3e66f7046a09bfe"

HT = 'www/index.html'
MARK = '/*v332-sports*/'
PART = 'Deportes dentro de Madrid hoy'


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v332.py. No se ha cambiado nada.')
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
        say(PART, 'no', 'el bloque v3.32 esta repetido (' + str(marks) + ' veces)')
        return None
    if marks == 1:
        for n, old, new in HTML_EDITS:
            if t.count(new) != 1:
                say(PART, 'no', 'la v3.32 esta a medias en la pagina (falta: ' + n + ')')
                return None
        say(PART, 'ya', 'ya estaba aplicado')
        return None
    if t.count('/*v331-sports*/') != 1:
        say(PART, 'no', 'falta la v3.31 (Deportes); pasala primero (o ya llevas la v3.32 a medias)')
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
    say(PART, 'ok', 'aplicado: pestaña Deportes dentro de Madrid hoy (ESPN directo si no hay Supabase) y sin entrada suelta en el menu')
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

print('v3.32:')
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
print('RESULTADO: todo aplicado o ya estaba' + (' (hay que volver a compilar la APK; Tablas y Equipos siguen necesitando Supabase (opcional))' if changed else ''))

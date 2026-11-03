# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.30)

CAMBIOS
  1. FACTURACION: «Mi comisión» del diario, semanal y mensual (y de la pantalla principal y del Informe) ahora sigue la MISMA regla que la nomina de ese mes.
     Si el mes tiene las propinas dentro de la facturacion, las propinas cuentan para el porcentaje (el 45 %); si no, no cuentan, como hasta ahora.
     El porcentaje, el minimo y la regla son los de ese mes. El mensual da exactamente lo mismo que la nomina.
  2. BURBUJA: ya no deberia parpadear.
     - Si Android cambia la ventana activa y vuelve a Bolt/Uber/Cabify en menos de 0,8 s, la burbuja ni se entera (antes se quitaba y se ponia).
     - Los avisos y la propia burbuja del Portal ya no cuentan como «has salido de Bolt».
     - Aparece con un fundido suave y tiene un aro luminoso que late despacio (si el movil tiene las animaciones apagadas, queda quieto).
     - El diagnostico de la burbuja (Ajustes) ahora cuenta cuantas veces se puso y se quito y los ultimos cambios de ventana, para afinar con datos.
  El instalador mira la ESTRUCTURA de tu ScreenReaderService.java (no lineas exactas), asi que vale aunque no sea identico al mio. Cada parte es independiente:
  lo que no pueda aplicar lo dice claro y no toca nada de esa parte. Se puede pasar mas de una vez. Hay que volver a compilar la APK.
"""
import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "865d1a619df15a2bce7585004e2b9e437f39105e7f465cc8ef603ddf462cfd82"

HT = 'www/index.html'
SRS = 'android/app/src/main/java/com/portal/conductor/ScreenReaderService.java'
PLG = 'android/app/src/main/java/com/portal/conductor/ScreenReaderPlugin.java'
MARK_H = '/*v330-bill*/'
MARK_B = '/*v330-bub*/'
MARK_HALO = '/*v330-halo*/'
MARK_GUARD = '/*v330-guard*/'
MARK_DIAG = '/*v330-diag*/'


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v330.py. No se ha cambiado nada.')
HTML_EDITS = PAY['html']
JV = PAY['java']

RES = []      # (parte, estado, texto)   estado: ok | ya | no


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


# ------------------------------------------------------------------ Java: lector de llaves (salta textos y comentarios)
def match_brace(s, i):
    depth = 0
    n = len(s)
    j = i
    while j < n:
        c = s[j]
        if c == '"':
            j += 1
            while j < n and s[j] != '"':
                j += 2 if s[j] == '\\' else 1
        elif c == "'":
            j += 1
            while j < n and s[j] != "'":
                j += 2 if s[j] == '\\' else 1
        elif s.startswith('//', j):
            k = s.find('\n', j)
            j = n if k < 0 else k
        elif s.startswith('/*', j):
            k = s.find('*/', j + 2)
            j = n if k < 0 else k + 1
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1


def find_method(s, name):
    """(inicio de la declaracion, posicion de '{', posicion de '}') de un metodo, o None"""
    rx = re.compile(r'^[ \t]*(?:@\w+(?:\([^)]*\))?\s+)*(?:(?:public|private|protected|static|final|synchronized)\s+)*[\w<>\[\],. ]+?\s+' + re.escape(name) + r'\s*\([^)]*\)\s*(?:throws\s+[\w., ]+)?\{', re.M)
    ms = [m for m in rx.finditer(s) if not re.match(r'\s*(?:return|new|else|if|for|while)\b', m.group(0))]
    if len(ms) != 1:
        return None
    m = ms[0]
    ob = m.end() - 1
    cb = match_brace(s, ob)
    if cb < 0:
        return None
    return m.start(), ob, cb


class Falta(Exception):
    pass


def method_body(s, name):
    r = find_method(s, name)
    if not r:
        raise Falta('no encuentro (o esta repetido) el metodo ' + name + '()')
    return r


def replace_in_body(s, name, fn):
    st, ob, cb = method_body(s, name)
    body = s[ob + 1:cb]
    nb = fn(body)
    return s[:ob + 1] + nb + s[cb:]


def sub_once(body, pat, rep, what, flags=0):
    ms = list(re.finditer(pat, body, flags))
    if len(ms) != 1:
        raise Falta(what + (' no esta' if not ms else ' esta repetido (' + str(len(ms)) + ' veces)'))
    m = ms[0]
    return body[:m.start()] + (rep(m) if callable(rep) else rep) + body[m.end():]


REQ = [
    ('el campo shown', r'\bboolean\s+shown\b'),
    ('el campo fgPkg', r'\bString\s+fgPkg\b'),
    ('el campo wm', r'\bWindowManager\s+wm\b'),
    ('el campo lp', r'\bLayoutParams\s+lp\b'),
    ('el campo bubble', r'\b(?:ImageView|TextView|View)\s+bubble\s*[;=]'),
    ('el metodo hideCard()', r'\bvoid\s+hideCard\s*\('),
    ('el metodo bubbleOn(Context)', r'\bboolean\s+bubbleOn\s*\(\s*Context\b'),
    ('que sea un AccessibilityService', r'extends\s+AccessibilityService\b'),
]
NEW_NAMES = ['hidePending', 'hideLater', 'bubbleBox', 'halo', 'haloAnim', 'wantBubble', 'noteFg', 'bubbleRoot', 'fgLog', 'fgLogText', 'showCount', 'hideCount', 'ui330', 'hideSoon', 'cancelHide', 'wrapHalo', 'startHalo', 'stopHalo', 'bubblePad', 'beforeShow330', 'afterShow330', 'beforeHide330']


def diag_service(s, extra=''):
    lines = ['Esto es lo que veo en tu ScreenReaderService.java (haz una captura y mandamela):']
    for what, pat in REQ:
        lines.append('  - ' + what + ': ' + ('si' if re.search(pat, s) else 'NO ESTA'))
    for nm in ('refreshBubble', 'showBubble', 'hideBubble', 'buildBubble', 'onAccessibilityEvent'):
        r = find_method(s, nm)
        if not r:
            lines.append('  - metodo ' + nm + '(): NO ESTA (o esta repetido)')
        else:
            body = s[r[1] + 1:r[2]].strip().split('\n')
            lines.append('  - metodo ' + nm + '(): ' + str(len(body)) + ' lineas; empieza por: ' + (body[0].strip()[:90] if body and body[0].strip() else ''))
    if extra:
        lines.append('  - ' + extra)
    return '\n'.join(lines)


def apply_core(s):
    """parte principal: espera antes de quitar la burbuja. Devuelve el texto nuevo o levanta Falta"""
    for what, pat in REQ:
        if not re.search(pat, s):
            raise Falta('no encuentro ' + what)
    for nm in NEW_NAMES:
        if re.search(r'\b' + nm + r'\b', s):
            raise Falta('ya existe algo llamado ' + nm + ' (parece que hay otra version de la burbuja puesta a mano)')
    # la condicion «se quiere la burbuja» se copia tal cual de la que ya tienes
    st, ob, cb = method_body(s, 'refreshBubble')
    rb = s[ob + 1:cb]
    mw = re.search(r'boolean\s+want\s*=\s*([^;]+);', rb)
    if not mw:
        raise Falta('refreshBubble() no tiene la linea «boolean want = ...;»')
    if not re.search(r'\bhideBubble\s*\(\s*\)\s*;', rb):
        raise Falta('refreshBubble() no llama a hideBubble()')
    want_expr = mw.group(1).strip()
    # 1) refreshBubble: se anula cualquier espera pendiente si se quiere la burbuja, y al quitarla se espera un poco
    def fix_refresh(b):
        b = re.sub(r'(boolean\s+want\s*=\s*[^;]+;)', lambda m: m.group(1) + ' if (want) cancelHide();', b, count=1)
        return re.sub(r'\bhideBubble\s*\(\s*\)\s*;', 'hideSoon();', b)
    s = replace_in_body(s, 'refreshBubble', fix_refresh)
    # 2) showBubble
    def fix_show(b):
        b = sub_once(b, r'wm\s*\.\s*addView\s*\(\s*bubble\s*,', 'wm.addView(bubbleRoot(),', 'showBubble(): wm.addView(bubble, ...)')
        b = sub_once(b, r'\bshown\s*=\s*true\s*;', 'shown = true; afterShow330();', 'showBubble(): shown = true;')
        return '\n        beforeShow330();' + b
    s = replace_in_body(s, 'showBubble', fix_show)
    # 3) hideBubble
    def fix_hide(b):
        b = sub_once(b, r'wm\s*\.\s*removeView\s*\(\s*bubble\s*\)', 'wm.removeView(bubbleRoot())', 'hideBubble(): wm.removeView(bubble)')
        return '\n        beforeHide330();' + b
    s = replace_in_body(s, 'hideBubble', fix_hide)
    # 4) arrastrar la burbuja (si existe)
    s = re.sub(r'wm\s*\.\s*updateViewLayout\s*\(\s*bubble\s*,', 'wm.updateViewLayout(bubbleRoot(),', s)
    left = re.findall(r'\bwm\s*\.\s*(?:addView|removeView|updateViewLayout)\s*\(\s*bubble\b', s)
    if left:
        raise Falta('hay otro sitio que pone o quita la burbuja directamente (' + str(len(left)) + ')')
    # 5) los metodos nuevos, justo antes de refreshBubble()
    st, ob, cb = method_body(s, 'refreshBubble')
    block = JV['core'].replace('@@WANT@@', want_expr)
    s = s[:st] + block + s[st:]
    if s.count(MARK_B) != 1:
        raise Falta('la insercion no ha quedado bien')
    return s


def apply_halo(s):
    if MARK_B not in s:
        raise Falta('falta la parte principal')
    def fix(b):
        if not re.search(r'\blp\s*=\s*new\s+WindowManager\.LayoutParams\s*\(', b):
            raise Falta('buildBubble() no crea «lp = new WindowManager.LayoutParams(...)»')
        if 'setOnTouchListener' not in b:
            raise Falta('buildBubble() no tiene el arrastre con el dedo')
        b = sub_once(b, r'\.putInt\(\s*"bx"\s*,\s*lp\.x\s*\)\s*\.putInt\(\s*"by"\s*,\s*lp\.y\s*\)',
                     '.putInt("bx", lp.x + bubblePad).putInt("by", lp.y + bubblePad)', 'buildBubble(): el guardado de la posicion')
        tail = b[len(b.rstrip()):]
        return b.rstrip() + '\n' + JV['halo_call'] + tail
    return replace_in_body(s, 'buildBubble', fix)


def apply_guard(s):
    if MARK_B not in s:
        raise Falta('falta la parte principal')
    m = re.search(r'onAccessibilityEvent\s*\(\s*(?:final\s+)?AccessibilityEvent\s+(\w+)\s*\)', s)
    if not m:
        raise Falta('no encuentro onAccessibilityEvent(AccessibilityEvent e)')
    ev = m.group(1)
    def fix(b):
        if not re.search(r'\bString\s+pkg\s*=', b):
            raise Falta('onAccessibilityEvent() no tiene «String pkg = ...»')
        b = sub_once(b, r'\bfgPkg\s*=\s*pkg\s*;', JV['guard'].replace('@@EV@@', ev), 'onAccessibilityEvent(): «fgPkg = pkg;»')
        b = re.sub(r'\bfgPkg\s*=\s*ap\s*;', 'noteFg(ap);', b)
        return b
    return replace_in_body(s, 'onAccessibilityEvent', fix)


def apply_diag_service(s):
    if MARK_B not in s:
        raise Falta('falta la parte principal')
    def fix(b):
        return sub_once(b, r'o\.put\(\s*"shown"\s*,\s*shown\s*\)\s*;', lambda m: m.group(0) + JV['diag_service'], 'bubbleDiag(): «o.put("shown", shown);»')
    return replace_in_body(s, 'bubbleDiag', fix)


def apply_diag_plugin(p):
    return sub_once(p, r'r\.put\(\s*"shown"\s*,\s*o\.optBoolean\(\s*"shown"\s*\)\s*\)\s*;', lambda m: m.group(0) + JV['diag_plugin'], 'ScreenReaderPlugin: «r.put("shown", ...)»')


# ------------------------------------------------------------------ parte 1: pagina (comision y Tema)
def part_html():
    t, err = read(HT)
    if t is None:
        say('Pagina (comision y Tema)', 'no', err)
        return None
    marks = t.count(MARK_H)
    if marks > 1:
        say('Pagina (comision y Tema)', 'no', 'el bloque v3.30 esta repetido (' + str(marks) + ' veces)')
        return None
    if marks == 1:
        for n, old, new in HTML_EDITS:
            if t.count(new) != 1:
                say('Pagina (comision y Tema)', 'no', 'la v3.30 esta a medias en la pagina (falta: ' + n + ')')
                return None
        say('Pagina (comision y Tema)', 'ya', 'ya estaba aplicado')
        return None
    if t.count('/*v328-nom*/') < 1:
        say('Pagina (comision y Tema)', 'no', 'falta la v3.28 (la nomina con propinas); pasala primero')
        return None
    s = t
    for n, old, new in HTML_EDITS:
        c = s.count(old)
        if c != 1:
            say('Pagina (comision y Tema)', 'no', n + (' no esta' if c == 0 else ' esta repetido (' + str(c) + ' veces)') + ' en ' + HT + ' (la pagina no es la version esperada)')
            return None
        s = s.replace(old, new, 1)
    if s.count(MARK_H) != 1:
        say('Pagina (comision y Tema)', 'no', 'error interno: la insercion no ha quedado bien')
        return None
    say('Pagina (comision y Tema)', 'ok', 'aplicada: Mi comision con las propinas como la nomina (diario, semanal, mensual, inicio e Informe) y Tema dentro de Ajustes')
    return s


# ------------------------------------------------------------------ parte 2 y 3: Java
def part_java():
    out = {}
    s0, err = read(SRS)
    if s0 is None:
        say('Burbuja', 'no', err)
        return out
    if '/*v329-bub*/' in s0:
        say('Burbuja', 'no', 'tu ScreenReaderService.java ya lleva la v3.29 (el aro de antes); no se puede poner encima')
        return out
    for mk in (MARK_B, MARK_HALO, MARK_GUARD, MARK_DIAG):
        if s0.count(mk) > 1:
            say('Burbuja', 'no', 'la marca ' + mk + ' esta repetida; no toco nada')
            return out
    s = s0
    has_core = MARK_B in s
    if has_core:
        say('Burbuja (no parpadea)', 'ya', 'ya estaba aplicado')
    else:
        try:
            s = apply_core(s)
            say('Burbuja (no parpadea)', 'ok', 'aplicada: espera 0,8 s antes de quitarla y fundido al aparecer')
            has_core = True
        except Falta as e:
            say('Burbuja (no parpadea)', 'no', str(e) + '\n' + diag_service(s0))
    optional = [
        ('Burbuja (aro luminoso)', MARK_HALO, apply_halo, 'aplicada: aro que late despacio'),
        ('Burbuja (avisos propios)', MARK_GUARD, apply_guard, 'aplicada: los avisos del Portal no cuentan como salir de Bolt'),
        ('Diagnostico de la burbuja', MARK_DIAG, apply_diag_service, 'aplicado: cuenta puestas/quitadas y los ultimos cambios de ventana'),
    ]
    for name, mk, fn, okmsg in optional:
        if mk in s:
            say(name, 'ya', 'ya estaba aplicado')
            continue
        if not has_core:
            say(name, 'no', 'no se intenta porque la parte principal de la burbuja no se ha podido poner')
            continue
        try:
            s = fn(s)
            say(name, 'ok', okmsg)
        except Falta as e:
            say(name, 'no', 'no aplicado (' + str(e) + '); lo demas funciona igual')
    # comprobacion final: las llaves del archivo siguen cuadrando (si cuadraban antes)
    def cuadra(t):
        cl = t.find('class ScreenReaderService')
        ob = t.find('{', cl) if cl >= 0 else -1
        return ob >= 0 and match_brace(t, ob) == len(t.rstrip()) - 1
    if s != s0:
        if cuadra(s0) and not cuadra(s):
            say('Burbuja', 'no', 'error interno: las llaves del archivo no cuadran despues del cambio; no se toca nada')
            RES[:] = [r for r in RES if not r[0].startswith(('Burbuja (', 'Diagnostico'))]
            say('Burbuja', 'no', 'cancelado por seguridad (no se ha cambiado el archivo)')
        else:
            out[SRS] = s
    p0, err = read(PLG)
    if p0 is None:
        say('Diagnostico (plugin)', 'no', err)
    elif MARK_DIAG in p0:
        say('Diagnostico (plugin)', 'ya', 'ya estaba aplicado')
    elif MARK_DIAG not in out.get(SRS, s0):
        say('Diagnostico (plugin)', 'no', 'no se intenta porque el servicio no lleva el diagnostico nuevo')
    else:
        try:
            out[PLG] = apply_diag_plugin(p0)
            say('Diagnostico (plugin)', 'ok', 'aplicado')
        except Falta as e:
            say('Diagnostico (plugin)', 'no', 'no aplicado (' + str(e) + '); lo demas funciona igual')
    return out


# ------------------------------------------------------------------ ejecucion: todo se calcula antes de escribir nada
new_html = part_html()
new_java = part_java()
writes = []
if new_html is not None:
    writes.append((HT, new_html))
for k, v in new_java.items():
    writes.append((k, v))
for path, text in writes:
    try:
        write_atomic(path, text)
    except Exception as e:
        say('Escritura', 'no', 'no he podido escribir ' + path + ': ' + str(e))

print('v3.30:')
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
print('RESULTADO: todo aplicado o ya estaba' + (' (hay que volver a compilar la APK)' if changed else ''))

# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.33)

CAMBIOS
  BURBUJA: SIN PARPADEO Y CON ARO AZUL NITIDO (solo cambia el Java de la burbuja, el diagnostico y el numero de version)
  - Causa probable del parpadeo: cuando la burbuja se pone, Android avisa de una ventana nueva del propio Portal, la app cree que has salido de Bolt, quita la burbuja,
    Android avisa otra vez... y vuelve a ponerla. Ahora los avisos del propio Portal (la burbuja, las tarjetas) no cuentan como «has salido de Bolt».
  - Si Android cambia de ventana y vuelve a Bolt, Uber o Cabify en menos de 1,5 s, la burbuja ni se quita ni se pone. Aparece con un fundido suave.
  - La burbuja lleva un aro azul NITIDO, pegado al icono (como el aro verde de la de Bolt), y se queda fijo: no late.
  - El diagnostico de la burbuja (Ajustes -> Burbuja flotante -> Diagnostico) cuenta cuantas veces se puso y se quito y los ultimos cambios de ventana.
  El instalador mira la ESTRUCTURA de tu ScreenReaderService.java (no lineas exactas). Si algo no encaja, no toca NADA y lo dice claro.
  Se puede pasar mas de una vez. Pasalo despues de v332.py (el numero de version). Hay que volver a compilar la APK.
"""
import os, re, json, zlib, base64, hashlib, tempfile

PAYLOAD = (
    "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"
)
SHA = "4ddf15278e265373e5bdea89e5cdf6bcbc761e9e445fca436b555b3c8bb30460"

HT = 'www/index.html'
SRS = 'android/app/src/main/java/com/portal/conductor/ScreenReaderService.java'
PLG = 'android/app/src/main/java/com/portal/conductor/ScreenReaderPlugin.java'
MARK_B = '/*v330-bub*/'
MARK_HALO = '/*v330-halo*/'
MARK_GUARD = '/*v330-guard*/'
MARK_DIAG = '/*v330-diag*/'
MARK_CALM = '/*v333-calm*/'
MARK_WAIT = '/*v333-wait*/'
MARK_RING = '/*v333-ring*/'


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
    fin('ERROR: el parche esta danado (la suma de control no coincide). Vuelve a subir v333.py. No se ha cambiado nada.')
JV = dict(PAY['java'])      # texto de la burbuja (v3.30) y los cambios de la v3.33

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


# ------------------------------------------------------------------ Java: lector de llaves y partes de la v3.30 (por estructura)
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


# ------------------------------------------------------------------ cambios de la v3.33 sobre la burbuja de la v3.30
def edits_v333(s):
    """aro azul nitido, aro quieto y espera de 1,5 s. Devuelve (texto, mensajes) o levanta Falta."""
    msgs = []
    EDS = [
        (MARK_RING, JV['ring_old'], JV['ring_new'], 'private void wrapHalo()', 'esta burbuja no tiene aro (no hay nada que cambiar)', 'aro azul nitido', 'aro azul ya puesto',
         'no encuentro el aro de la v3.30 en '),
        (MARK_CALM, JV['halo_old'], JV['halo_new'], 'private void startHalo()', 'esta burbuja no tiene aro (no hay nada que parar)', 'aro quieto', 'aro ya quieto',
         'no encuentro el aro que late en '),
        (MARK_WAIT, JV['delay_old'], JV['delay_new'], None, '', 'espera de 1,5 s', 'espera ya de 1,5 s', 'no encuentro la espera de 0,8 s en '),
    ]
    for mk, old, new, need, nomsg, okmsg, yamsg, nfmsg in EDS:
        m = s.count(mk)
        if m > 1:
            raise Falta('la marca ' + mk + ' esta repetida (' + str(m) + ' veces); no toco nada')
        if m == 1:
            if s.count(new) != 1:
                raise Falta('esta a medias en ' + SRS + ' (' + yamsg + ' pero con el texto cambiado)')
            msgs.append(yamsg)
            continue
        if need is not None and need not in s:
            msgs.append(nomsg)
            continue
        c = s.count(old)
        if c != 1:
            raise Falta(nfmsg + SRS + ' (' + str(c) + ' veces): el archivo no es el esperado')
        s = s.replace(old, new, 1)
        msgs.append(okmsg)
    return s, msgs


def part_java():
    out = {}
    NOM = 'Burbuja'
    s0, err = read(SRS)
    if s0 is None:
        say(NOM, 'no', err)
        return out
    if '/*v329-bub*/' in s0:
        say(NOM, 'no', 'tu ScreenReaderService.java lleva la burbuja de la v3.29 (otra version); no se puede poner encima')
        return out
    for mk in (MARK_B, MARK_HALO, MARK_GUARD, MARK_DIAG, MARK_CALM, MARK_WAIT, MARK_RING):
        if s0.count(mk) > 1:
            say(NOM, 'no', 'la marca ' + mk + ' esta repetida; no toco nada')
            return out
    s = s0
    errs = []
    # --- 1) la burbuja de la v3.30 (espera, avisos propios, diagnostico), si todavia no esta
    if MARK_B in s:
        say('Burbuja (sin parpadeo)', 'ya', 'ya estaba puesta la base (v3.30)')
    else:
        try:
            s = apply_core(s)
            say('Burbuja (sin parpadeo)', 'ok', 'aplicada: espera antes de quitarla y fundido al aparecer')
        except Falta as e:
            say('Burbuja (sin parpadeo)', 'no', str(e) + '\n' + diag_service(s0))
            errs.append(1)
    if not errs:
        optional = [
            ('Burbuja (aro)', MARK_HALO, apply_halo, 'aplicado: aro alrededor del icono'),
            ('Burbuja (avisos propios)', MARK_GUARD, apply_guard, 'aplicado: los avisos del Portal no cuentan como salir de Bolt'),
            ('Diagnostico de la burbuja', MARK_DIAG, apply_diag_service, 'aplicado: cuenta puestas/quitadas y los ultimos cambios de ventana'),
        ]
        for name, mk, fn, okmsg in optional:
            if mk in s:
                say(name, 'ya', 'ya estaba aplicado')
                continue
            try:
                s = fn(s)
                say(name, 'ok', okmsg)
            except Falta as e:
                say(name, 'no', 'no aplicado (' + str(e) + ')')
                errs.append(1)
    # --- 2) los cambios de la v3.33
    if not errs:
        try:
            s, msgs = edits_v333(s)
            say('Burbuja (aro azul fijo y espera de 1,5 s)', 'ok' if any(m in msgs for m in ('aro azul nitido', 'aro quieto', 'espera de 1,5 s')) else 'ya', ', '.join(msgs))
        except Falta as e:
            say('Burbuja (aro azul fijo y espera de 1,5 s)', 'no', str(e))
            errs.append(1)
    # --- 3) las llaves del archivo siguen cuadrando
    def cuadra(t):
        cl = t.find('class ScreenReaderService')
        ob = t.find('{', cl) if cl >= 0 else -1
        return ob >= 0 and match_brace(t, ob) == len(t.rstrip()) - 1
    if not errs and s != s0 and cuadra(s0) and not cuadra(s):
        say('Burbuja', 'no', 'error interno: las llaves del archivo no cuadran despues del cambio; no se toca nada')
        errs.append(1)
    if not errs and s != s0:
        out[SRS] = s
    # --- 4) el diagnostico en el plugin (necesita el del servicio)
    p0, err = read(PLG)
    if p0 is None:
        say('Diagnostico (plugin)', 'no', err)
    elif MARK_DIAG in p0:
        say('Diagnostico (plugin)', 'ya', 'ya estaba aplicado')
    elif errs:
        say('Diagnostico (plugin)', 'no', 'no se intenta porque la burbuja no se ha podido poner')
    else:
        try:
            out[PLG] = apply_diag_plugin(p0)
            say('Diagnostico (plugin)', 'ok', 'aplicado')
        except Falta as e:
            say('Diagnostico (plugin)', 'no', 'no aplicado (' + str(e) + ')')
    return out


def part_version():
    t, err = read(HT)
    if t is None:
        say('Numero de version', 'no', err)
        return None
    if t.count("const APP_VERSION='v3.33';") == 1:
        say('Numero de version', 'ya', 'ya es v3.33')
        return None
    if t.count("const APP_VERSION='v3.32';") == 1:
        say('Numero de version', 'ok', 'v3.32 -> v3.33')
        return t.replace("const APP_VERSION='v3.32';", "const APP_VERSION='v3.33';", 1)
    say('Numero de version', 'ya', 'no la toco (no es la v3.32; pasa v332.py primero si quieres que ponga v3.33)')
    return None


# ------------------------------------------------------------------ ejecucion: todo se calcula antes de escribir nada
new_java = part_java()
new_ver = part_version()
writes = []
for k, v in new_java.items():
    writes.append((k, v))
if new_ver is not None:
    writes.append((HT, new_ver))
if any(r[1] == 'no' for r in RES):
    writes = []   # si una parte no se puede aplicar, no se toca nada (ni siquiera el numero de version)
for path, text in writes:
    try:
        write_atomic(path, text)
    except Exception as e:
        say('Escritura', 'no', 'no he podido escribir ' + path + ': ' + str(e))

print('v3.33:')
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
    print('RESULTADO: hay partes sin aplicar (las lineas «NO» de arriba). No se ha tocado nada. Haz una captura de esto y mandamela.')
    raise SystemExit(1)
print('RESULTADO: todo aplicado o ya estaba' + (' (hay que volver a compilar la APK)' if changed else ''))

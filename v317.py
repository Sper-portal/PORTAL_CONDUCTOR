# -*- coding: utf-8 -*-
"""Super portal del conductor 1.0  (v3.17)

ARREGLO: Uber salia «DATOS INSUFICIENTES» («No se pudo leer la distancia del viaje») en las tarjetas que traen la linea «A 46 min del destino».
  - Esa linea es la distancia a TU destino (el filtro de destino de Uber), no es un dato del viaje. La app la leia como si fuera el tiempo del viaje,
    sin kilometros, y por eso no podia calcular nada. Pasaba igual con la version original: no lo ha provocado ninguna actualizacion nuestra.
  - Ahora esa linea se ignora al leer kilometros y minutos. El resto de la lectura (Uber, Cabify y Bolt) no cambia.
Solo cambia un archivo de Java (OfferAnalyzer.java): hay que volver a compilar la APK (git push y GitHub Actions).
Se puede aplicar mas de una vez (la segunda no hace nada). Todo o nada: si falta cualquier ancla NO se cambia nada.
"""
import os, tempfile

REL = 'android/app/src/main/java/com/portal/conductor/OfferAnalyzer.java'

# ancla 1: la constante KM (esta una sola vez; justo debajo se anade la nueva constante)
A1 = r'    private static final Pattern KM = Pattern.compile("(\\d+(?:[.,]\\d+)?)\\s*km\\b", Pattern.CASE_INSENSITIVE);' + '\n'
N1 = A1 + (
    '    // «A 46 min del destino» / «A 12 km de tu destino»: distancia hasta TU destino (filtro de destino de Uber). No es un dato del viaje.\n'
    + r'    private static final Pattern DEST_CHIP = Pattern.compile("^a\\s+\\d[\\d.,]*\\s*(?:min\\w*|km|kilometros?|h\\w*)\\b.*\\bdestino\\b");' + '\n')
# ancla 2: donde se arma la lista de textos de la pantalla (una sola vez): ahi se descarta la linea del destino
A2 = (r'        for (String x : rawNodes) for (String line : clean(x).split("\\n")) if (line.trim().length() > 0) nodes.add(line.trim());' + '\n')
N2 = (r'        for (String x : rawNodes) for (String line : clean(x).split("\\n")) if (line.trim().length() > 0 && !DEST_CHIP.matcher(norm(line).trim()).find()) nodes.add(line.trim());' + '\n')


def fin(msg):
    raise SystemExit(msg)


p = REL
if not os.path.exists(p):
    try:
        os.chdir('/workspaces/PORTAL_CONDUCTOR/portal')
    except OSError:
        pass
if not os.path.exists(p):
    fin('ERROR: no encuentro ' + REL + ' (ejecuta el parche desde la carpeta portal). No se ha cambiado nada.')
with open(p, encoding='utf-8', newline='') as f:
    orig = f.read()
if 'DEST_CHIP' in orig:
    if orig.count('DEST_CHIP') == 2 and orig.count(N2) == 1 and orig.count(N1) == 1:
        print('v3.17 ya aplicado: no hay nada que cambiar.')
        raise SystemExit(0)
    fin('ERROR: el archivo ya tiene algo llamado DEST_CHIP pero no es lo de este parche. No se ha cambiado nada.')
if '\r' in orig:
    fin('ERROR: OfferAnalyzer.java tiene finales de linea de Windows; este parche espera los de Linux. No se ha cambiado nada.')
for a, name in ((A1, 'la constante KM de OfferAnalyzer'), (A2, 'la linea que arma la lista de textos de la pantalla')):
    n = orig.count(a)
    if n != 1:
        fin('ERROR: ' + name + (' no esta' if n == 0 else ' esta repetido (' + str(n) + ' veces)') + '. No se ha cambiado nada (la app no es la version esperada).')
s = orig.replace(A1, N1, 1).replace(A2, N2, 1)
if s.count('DEST_CHIP') != 2 or s == orig:
    fin('ERROR interno: el cambio no ha quedado bien. No se ha cambiado nada.')
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix='.tmp')
os.close(fd)
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, p)
print('OfferAnalyzer.java: actualizado')
print('v3.17 aplicado: la linea «A N min del destino» de Uber ya no se confunde con el viaje (hay que volver a compilar la APK)')

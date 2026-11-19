BASE = "."  # carpeta del proyecto
"""Codifica cada nota de Carrillo: encuadre, voz, dolencias y localidades.
Se mira el pasaje que lo nombra (oraciones con 'Carrillo' y la siguiente), no la nota entera."""
import json, os, re, sys, unicodedata, collections
D = BASE
O = os.path.join(D, 'dossier_datos')
L = json.load(open(os.path.join(O, 'carrillo_notas.json'), encoding='utf-8'))


def norm(s):
    return unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()


ENCUADRES = {
    'Judicial o disciplinario': r'procuradur|suspen|tribunal|rectific|fiscal|denuncia penal|investigaci|demanda|consejo de estado|corte suprema|tutela|imputa',
    'Pelea con otros políticos': r'pelea|arremete|responde|respondio|critica|crític|acus|choque|enfrent|ataca|ataque|contra |duro mensaje|dardo|cruce|replica|polemi|controversia',
    'UNGRD y gestión del riesgo': r'ungrd|gestion del riesgo|emergencia|damnificad|carrotanque|olmedo|sneyder|lluvias|nino|fondo adaptacion|libro de la verdad|desastre',
    'Política nacional y gobierno': r'petro|cepeda|pacto historico|gobierno|presidencial|segunda vuelta|de la espriella|abelardo|quintero|guerrero|benedetti|ministro',
    'Aspiración 2027': r'2027|alcaldia de bogota|aspiracion|candidat|consulta|precandidat|aval|firmas|sondeo|regionales',
    'Bogotá y sus problemas': r'seguridad ciudadana|inseguridad|transmilenio|metro de bogota|movilidad|salud|educacion|desempleo|empleo|vivienda|pobreza|hambre|agua|basura|localidad|barrio|galan',
}
VOZ = r'(dijo|afirmo|aseguro|sostuvo|senalo|expreso|manifesto|escribio|trino|publico|respondio|advirtio|indico|explico|agrego|declaro|cuestiono|denuncio)'
DOLENCIAS = {'salud': r'\bsalud\b|eps\b|hospital', 'educación': r'educaci|colegio|universidad publica', 'empleo': r'desempleo|empleo\b', 'seguridad': r'inseguridad|seguridad ciudadana|hurto|homicid|extorsi',
             'pobreza': r'pobreza|hambre|ingreso minimo', 'movilidad': r'transmilenio|movilidad|metro de bogota|trancon', 'vivienda': r'vivienda|arriendo', 'agua': r'acueducto|racionamiento|agua potable|chingaza'}
LOCS = ['Usaquén', 'Chapinero', 'Santa Fe', 'San Cristóbal', 'Usme', 'Tunjuelito', 'Bosa', 'Kennedy', 'Fontibón', 'Engativá', 'Suba', 'Barrios Unidos', 'Teusaquillo', 'Los Mártires',
        'Antonio Nariño', 'Puente Aranda', 'La Candelaria', 'Rafael Uribe Uribe', 'Ciudad Bolívar', 'Sumapaz']
LRX = {l: re.compile(r'\b' + norm(l).replace('los ', '(los )?').replace('la ', '(la )?') + r'\b') for l in LOCS}
FALSOS = {'Santa Fe': r'santa fe (de antioquia|de bogota)|independiente santa fe|club santa fe', 'Kennedy': r'john f|j\. ?f\. kennedy|robert kennedy|kennedy center', 'Antonio Nariño': r'antonio narino (y|fue|escribio|tradujo)|precursor', 'Sumapaz': r'paramo', 'Suba': r'subasta'}


def pasaje(texto, titulo):
    o = re.split(r'(?<=[\.\?\!])\s+', texto or '')
    idx = [i for i, s in enumerate(o) if 'carrillo' in norm(s)]
    sel = set()
    for i in idx:
        sel.update([i, i + 1])
    return norm(titulo) + ' ' + ' '.join(norm(o[i]) for i in sorted(sel) if i < len(o))


for n in L:
    p = pasaje(n.get('texto'), n['titulo'])
    t = norm(n['titulo'])
    n['encuadres'] = [k for k, rx in ENCUADRES.items() if re.search(rx, p)]
    # encuadre principal: el que aparece en el titular; si ninguno, el primero en el pasaje según orden de prioridad
    ORDEN = ['Bogotá y sus problemas', 'Aspiración 2027', 'Judicial o disciplinario', 'Pelea con otros políticos', 'UNGRD y gestión del riesgo', 'Política nacional y gobierno']
    tit = [k for k in ORDEN if re.search(ENCUADRES[k], t)]
    n['principal'] = (tit or [k for k in ORDEN if k in n['encuadres']] or ['Otro'])[0]
    n['voz_propia'] = bool(re.search(r'carrillo[^.]{0,80}' + VOZ, p) or re.search(VOZ + r'[^.]{0,40}carrillo', p) or re.search(r'^["“‘\']', n['titulo']))
    n['dolencias'] = [k for k, rx in DOLENCIAS.items() if re.search(rx, p)]
    x = norm(n.get('texto'))
    locs = []
    for l, rx in LRX.items():
        if rx.search(x) and not (l in FALSOS and re.search(FALSOS[l], x)):
            locs.append(l)
    n['localidades_nota'] = locs
    n['localidades_pasaje'] = [l for l, rx in LRX.items() if rx.search(p)]
    n['bogota_en_pasaje'] = bool(re.search(r'bogota|capital del pais|distrito', p))
json.dump(L, open(os.path.join(O, 'carrillo_codificado.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('notas', len(L))
print('principal', collections.Counter(n['principal'] for n in L).most_common())
print('cualquier encuadre', collections.Counter(k for n in L for k in n['encuadres']).most_common())
print('voz propia', sum(n['voz_propia'] for n in L))
print('dolencias en pasaje', collections.Counter(k for n in L for k in n['dolencias']).most_common(), 'notas con alguna', sum(bool(n['dolencias']) for n in L))
print('localidad en nota', sum(bool(n['localidades_nota']) for n in L), collections.Counter(k for n in L for k in n['localidades_nota']).most_common())
print('localidad en pasaje', sum(bool(n['localidades_pasaje']) for n in L), collections.Counter(k for n in L for k in n['localidades_pasaje']).most_common())
print('bogota en pasaje', sum(n['bogota_en_pasaje'] for n in L))

BASE = "."  # carpeta del proyecto
"""Codificación a mano, ventana de 12 meses (12 nov 2025 - 11 nov 2026), de los tres medios del mapa de menciones.
Se conservan los códigos ya asignados (jun-nov) por enlace y se agregan las notas nuevas, leídas por titular y pasaje.
J judicial o disciplinario (procesos, denuncias, investigaciones) · U gestión o salida de la UNGRD (emergencias, obras)
P pelea con un político nombrado · N política nacional e izquierda · A aspiración 2027 · B Bogotá y sus problemas · X aparece de pasada"""
import json, os, sys, collections
D = BASE; O = os.path.join(D, 'dossier_datos')
L = json.load(open(os.path.join(O, 'carrillo_codificado.json'), encoding='utf-8'))
VIEJO = {o['url']: o['codigo'] for o in json.load(open(os.path.join(O, 'mapa_menciones_manual_jun_nov.json'), encoding='utf-8'))}
MEDIOS = ['Revista Semana', 'Caracol Radio', 'El Tiempo']
# notas nuevas, en el orden del listado (Semana, Caracol Radio, El Tiempo; por fecha)
NUEVOS = ('UJPPPPPPPXUUXUXPUXUXNJPPPPPPJPXJJXJJJXJXPJXXPUX'   # Semana 0-46
          'UJUUJUUAPP' 'PUPPPUJPXP' 'PXXNXXUNUU' 'UUUUUXXXXX' 'UUXUXUUUPP' 'JXUUUXJPPX' 'XPJXJXPUJU' 'UUXXXUU'  # Caracol 47-123
          'PPPPJJJJUU')  # El Tiempo 124-133
NOMBRE = {'J': 'Judicial o disciplinario', 'U': 'Gestión o salida de la UNGRD', 'P': 'Pelea con un político', 'N': 'Política nacional e izquierda',
          'A': 'Aspiración 2027', 'B': 'Bogotá y sus problemas', 'X': 'Aparece de pasada'}
nuevas = [n for m in MEDIOS for n in sorted([x for x in L if x['medio'] == m], key=lambda x: x['fecha']) if n['url_real'] not in VIEJO]
assert len(nuevas) == len(NUEVOS), (len(nuevas), len(NUEVOS))
cod = dict(zip([n['url_real'] for n in nuevas], NUEVOS))
out = []
for m in MEDIOS:
    for n in sorted([x for x in L if x['medio'] == m], key=lambda x: x['fecha']):
        k = VIEJO.get(n['url_real']) or cod[n['url_real']]
        out.append({'medio': m, 'fecha': n['fecha'], 'titulo': n['titulo'], 'url': n['url_real'], 'codigo': k, 'encuadre': NOMBRE[k], 'en_titular': n['en_titular'],
                    'localidades_nota': n['localidades_nota'], 'auto': n['principal'], 'lectura': 'jun-nov' if n['url_real'] in VIEJO else 'nueva 12m'})
json.dump(out, open(os.path.join(O, 'mapa_menciones_manual.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('viejas sin hallar en corpus nuevo:', sum(1 for u in VIEJO if u not in {o['url'] for o in out}))
for m in MEDIOS:
    s = [o for o in out if o['medio'] == m]
    print(m, len(s), collections.Counter(o['encuadre'] for o in s).most_common())
print('total', len(out), collections.Counter(o['encuadre'] for o in out).most_common())
mes = collections.defaultdict(collections.Counter)
for o in out:
    mes[o['medio']][o['fecha'][:7]] += 1
for m in mes:
    print(m, dict(sorted(mes[m].items())))

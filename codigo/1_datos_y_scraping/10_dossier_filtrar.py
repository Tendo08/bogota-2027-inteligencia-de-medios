BASE = "."  # carpeta del proyecto
"""Filtra el barrido de Carrillo: deja solo notas sobre este Carlos Carrillo y mide cuánto lo nombran."""
import json, os, re, sys, unicodedata, collections
D = BASE
O = os.path.join(D, 'dossier_datos')
B = json.load(open(os.path.join(O, 'carrillo_bruto_12m.json'), encoding='utf-8'))


def norm(s):
    return unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()


CONTEXTO = re.compile(r'ungrd|gestion del riesgo|petro|pacto historico|polo democratico|concejal|alcaldia de bogota|quintero|angie rodriguez|procuraduria|cepeda|olmedo|carrotanques|benedetti|trujillo|fondo adaptacion')
FUERA = {'Transfermarkt', 'TUDN', 'Excélsior', 'El Sol de México', 'Telemetro', 'Emisoras Unidas', 'Publinews', 'Facebook'}
vistos, L, descartes = set(), [], collections.Counter()
for n in B['notas']:
    t = norm(n['titulo']); x = norm(n.get('texto'))
    todo = t + ' ' + x
    if n['medio'] in FUERA:
        descartes['medio ajeno'] += 1; continue
    if 'carrillo' not in todo:
        descartes['no nombra a Carrillo'] += 1; continue
    if not CONTEXTO.search(todo):
        descartes['otro Carlos Carrillo'] += 1; continue
    if not ('2025-11-12' <= n['fecha'] <= '2026-11-11'):
        descartes['fuera de ventana'] += 1; continue
    k = (n['url_real'] or n['url']).split('?')[0].rstrip('/')
    if k in vistos:
        descartes['repetida'] += 1; continue
    vistos.add(k)
    n['en_titular'] = 'carrillo' in t
    n['menciones'] = len(re.findall(r'carrillo', x))
    n['con_texto'] = len(x) > 300
    L.append(n)
print('quedan', len(L), dict(descartes))
print('en titular', sum(n['en_titular'] for n in L), '| con texto', sum(n['con_texto'] for n in L))
c = collections.Counter(n['medio'] for n in L)
ct = collections.Counter(n['medio'] for n in L if n['en_titular'])
for m, v in c.most_common(30):
    meses = collections.Counter(n['fecha'][:7] for n in L if n['medio'] == m)
    print(f'{m:28s} {v:3d} titular {ct[m]:3d}', dict(sorted(meses.items())))
print(collections.Counter(n['fecha'][:7] for n in L))
json.dump(L, open(os.path.join(O, 'carrillo_notas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

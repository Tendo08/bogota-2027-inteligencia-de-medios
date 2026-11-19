BASE = "."  # carpeta del proyecto
"""Baja la geometría oficial de las localidades y la deja en coordenadas de dibujo, con los datos de cada una."""
import json, os, re, sys, unicodedata
from collections import Counter
import requests
B = BASE
H = {'User-Agent': 'Mozilla/5.0'}
U = 'https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/CifrasSCJ/MapServer/0/query'
def norm(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()
g = requests.get(U, params={'where': '1=1', 'outFields': 'CMNOMLOCAL', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.0009, 'geometryPrecision': 4, 'f': 'json'}, headers=H, timeout=60).json()
ALT = {'CANDELARIA': 'La Candelaria'}
loc = {norm(a['Localidad']): a for a in json.load(open(os.path.join(B, 'localidades.json'), encoding='utf-8'))}
v23 = {norm(a['L']): a for a in json.load(open(os.path.join(B, 'fuentes_primarias', 'registraduria', 'alcaldia_2023_localidad.json'), encoding='utf-8'))}
v26 = {}
for a in json.load(open(os.path.join(B, 'fuentes_primarias', 'registraduria', 'presidente_2026_localidad.json'), encoding='utf-8')):
    k = {'CANDELARIA': 'LA CANDELARIA', 'MARTIRES': 'LOS MARTIRES', 'RAFAEL URIBE URIB': 'RAFAEL URIBE URIBE'}.get(a['L'], a['L'])
    v26[k] = a
F = {x['titulo']: x for x in json.load(open(os.path.join(B, 'alternativos_filtradas.json'), encoding='utf-8'))}
men = Counter(norm(l).replace('RAFAEL URIBE', 'RAFAEL URIBE URIBE') for f in F.values() for l in f['localidades'])
out = []
for f in g['features']:
    n = f['attributes']['CMNOMLOCAL']
    if n in ('Sin Localización',) or 'geometry' not in f:
        continue
    k = norm(ALT.get(norm(n), n))
    out.append({'nombre': ALT.get(norm(n), n), 'rings': f['geometry']['rings'], 'pobreza': loc.get(k, {}).get('Pobreza monetaria %'), 'uno_hora': loc.get(k, {}).get('Más de 1 hora al trabajo %'), 'oviedo': v23.get(k, {}).get('JUAN DANIEL OVIEDO ARANGO'), 'valencia': v26.get(k, {}).get('Valencia'), 'lopez': v26.get(k, {}).get('López'), 'menciones': men.get(k, 0)})
json.dump(out, open(os.path.join(B, 'mapa_localidades.json'), 'w', encoding='utf-8'), ensure_ascii=False)
for o in out:
    print(o['nombre'], len(o['rings']), sum(len(r) for r in o['rings']), o['pobreza'] and round(o['pobreza'], 1), o['oviedo'], o['valencia'], o['lopez'], o['menciones'])
print(sum(sum(len(r) for r in o['rings']) for o in out), 'notas', len(F), 'con localidad', sum(bool(f['localidades']) for f in F.values()))

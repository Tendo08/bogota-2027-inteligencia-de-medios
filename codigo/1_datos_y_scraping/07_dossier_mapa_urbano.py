BASE = "."  # carpeta del proyecto
"""Parte urbana de cada localidad: unión de sus UPZ (capa oficial SCJ). La pobreza del DANE (cuadro 216A) es de la localidad urbana,
así que el mapa no debe pintar la zona rural de Usme, Ciudad Bolívar, Santa Fe, Chapinero, Usaquén ni San Cristóbal."""
import json, os, sys, requests
from shapely.geometry import Polygon, MultiPolygon, mapping, shape
from shapely.ops import unary_union
D = BASE
U = 'https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/CifrasSCJ/MapServer/3/query'
g = requests.get(U, params={'where': '1=1', 'outFields': 'CMIUUPLA,CMNOMUPLA', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': 0.0004, 'geometryPrecision': 5, 'f': 'json'}, timeout=90).json()
LOC = json.load(open(os.path.join(D, 'mapa_localidades.json'), encoding='utf-8'))
lp = {o['nombre']: unary_union([Polygon(r).buffer(0) for r in o['rings']]) for o in LOC}
asig = {}
for f in g['features']:
    if f['attributes']['CMIUUPLA'].startswith('UPR'):
        continue  # unidades rurales: fuera del cuadro 216A
    p = unary_union([Polygon(r).buffer(0) for r in f['geometry']['rings']])
    pt = p.representative_point()
    dueños = [n for n, poly in lp.items() if poly.contains(pt)]
    n = dueños[0] if dueños else max(lp, key=lambda k: lp[k].intersection(p).area)
    if f['attributes']['CMIUUPLA'] == 'UPZ94':
        n = 'La Candelaria'
    asig.setdefault(n, []).append(p)
    print(f"{f['attributes']['CMIUUPLA']:7s} {f['attributes']['CMNOMUPLA'][:30]:30s} -> {n}")
out = {}
for n, ps in asig.items():
    u = unary_union(ps).buffer(0.00025).buffer(-0.00025)  # cierra rendijas entre UPZ
    u = u.intersection(lp[n])
    out[n] = mapping(u)
json.dump(out, open(os.path.join(D, 'dossier_datos', 'localidades_urbanas.json'), 'w', encoding='utf-8'))
print({n: len(v) for n, v in asig.items()})
print('sin UPZ:', [n for n in lp if n not in asig])

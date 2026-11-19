BASE = "."  # carpeta del proyecto
"""Une por localidad la Encuesta Multipropósito 2025 (DANE/SDP) y los delitos de la Secretaría de Seguridad, ene-sep 2026."""
import json, math, os, sys
from openpyxl import load_workbook
import pandas as pd
B = BASE
D = os.path.join(B, 'fuentes_primarias', 'dane')
LOC = ['Usaquén', 'Chapinero', 'Santa Fe', 'San Cristóbal', 'Usme', 'Tunjuelito', 'Bosa', 'Kennedy', 'Fontibón', 'Engativá', 'Suba', 'Barrios Unidos', 'Teusaquillo', 'Los Mártires', 'Antonio Nariño', 'Puente Aranda', 'La Candelaria', 'Rafael Uribe Uribe', 'Ciudad Bolívar']
WB = {}
def cuadro(a, c):
    w = WB.setdefault(a, load_workbook(os.path.join(D, a), read_only=True, data_only=True))
    s = next(w[n] for n in w.sheetnames if n.strip() == c)
    return {str(f[0]).strip(): f for f in s.iter_rows(values_only=True) if f[0] is not None}
HO, PE, VI, PO, DE = 'anex-EM-hogares-2025.xlsx', 'anex-EM-personas-2025.xlsx', 'anex-EM-viviendas-2025.xlsx', 'anex-EM-pobreza-2025.xlsx', 'anex-EM-discapacidad-y-deficit-habitacional-2025.xlsx'
c216, c219, c215, c201, c212, c211 = cuadro(PO, 'Cuadro 216A'), cuadro(PO, 'Cuadro 219A'), cuadro(DE, 'Cuadro 215A'), cuadro(HO, 'Cuadro 201A'), cuadro(HO, 'Cuadro 212A'), cuadro(HO, 'Cuadro 211A')
c321, c322, c317, c104 = cuadro(PE, 'Cuadro 321A'), cuadro(PE, 'Cuadro 322A'), cuadro(PE, 'Cuadro 317A'), cuadro(VI, 'Cuadro 104A')
scj = {a['CMNOMLOCAL']: a for a in json.load(open(os.path.join(B, 'fuentes_primarias', 'scj_delitos_localidad.json'), encoding='utf-8'))}
scj['La Candelaria'] = scj['Candelaria']
filas = []
for l in LOC + ['Total']:
    k216 = 'Estimación' if l == 'Total' else l
    p = c216[k216]; pop = p[1]
    a = {'Localidad': 'Bogotá urbana' if l == 'Total' else l, 'Personas': round(pop), 'Pobreza monetaria %': p[7], 'CVE pobreza': p[8], 'Pobreza extrema %': p[13], 'CVE extrema': p[14], 'IPM %': c219[l][10], 'CVE IPM': c219[l][11],
         'Déficit habitacional %': 100 * c215[l][13] / c215[l][1], 'CVE déficit': c215[l][14], 'Hogares en arriendo %': c201[l][22], 'Se considera pobre %': c212[l][8], 'Ingreso no alcanza %': c211[l][8],
         'Más de 1 hora al trabajo %': c321[l][22], 'Desempleo % (cálculo propio)': 100 * c322[l][12] / (c322[l][5] + c322[l][12]), 'Satisfacción seguridad (0-10)': c317[l][25], 'Satisfacción ingreso (0-10)': c317[l][13], 'Satisfacción salud (0-10)': c317[l][17],
         'Cerca de ollas %': c104[l][50], 'Cerca de lotes oscuros %': c104[l][57], 'Cerca de basureros %': c104[l][15]}
    if l == 'Total':
        S = [x for n, x in scj.items() if n not in ('Candelaria',)]
        s = lambda cod, y: sum((x.get(f'CM{cod}{y}CONT') or 0) for x in S)
    else:
        s = lambda cod, y: scj[l].get(f'CM{cod}{y}CONT') or 0
    for cod, nom in [('H', 'Homicidios'), ('HP', 'Hurto a personas'), ('LP', 'Lesiones'), ('VI', 'Violencia intrafamiliar'), ('E', 'Extorsión'), ('DS', 'Delitos sexuales')]:
        a[f'{nom} ene-sep 2026'] = s(cod, 26); a[f'{nom} ene-sep 2025'] = s(cod, 25)
        a[f'{nom} por 100 mil'] = 1e5 * s(cod, 26) / pop
    filas.append(a)
d = pd.DataFrame(filas)
d.to_json(os.path.join(B, 'localidades.json'), orient='records', force_ascii=False, indent=0)
pd.set_option('display.width', 250, 'display.max_columns', 60)
print(d[['Localidad', 'Personas', 'Pobreza monetaria %', 'Pobreza extrema %', 'IPM %', 'Déficit habitacional %', 'Hogares en arriendo %', 'Se considera pobre %', 'Más de 1 hora al trabajo %', 'Desempleo % (cálculo propio)']].round(1).to_string())
print(d[['Localidad', 'Satisfacción seguridad (0-10)', 'Satisfacción salud (0-10)', 'Cerca de ollas %', 'Cerca de lotes oscuros %', 'Homicidios ene-sep 2026', 'Homicidios por 100 mil', 'Hurto a personas por 100 mil', 'Extorsión por 100 mil', 'Violencia intrafamiliar por 100 mil', 'Lesiones por 100 mil']].round(1).to_string())
n = d.iloc[:-1]
for x in ['Homicidios por 100 mil', 'Hurto a personas por 100 mil', 'Extorsión por 100 mil', 'Violencia intrafamiliar por 100 mil', 'Más de 1 hora al trabajo %', 'Déficit habitacional %', 'Satisfacción seguridad (0-10)', 'Hogares en arriendo %']:
    print('corr pobreza vs', x, round(n['Pobreza monetaria %'].corr(n[x]), 2))
sc = n[n['Localidad'] != 'La Candelaria']
print('sin Candelaria y sin centro', round(n[~n['Localidad'].isin(['La Candelaria', 'Santa Fe', 'Los Mártires', 'Chapinero'])]['Pobreza monetaria %'].corr(n['Homicidios por 100 mil']), 2), round(n[~n['Localidad'].isin(['La Candelaria', 'Santa Fe', 'Los Mártires', 'Chapinero'])]['Pobreza monetaria %'].corr(n['Hurto a personas por 100 mil']), 2))
print('Personas pobres en 5 más pobres', n.sort_values('Pobreza monetaria %', ascending=False).head(5)[['Localidad', 'Pobreza monetaria %']].values.tolist())
print('Sumapaz homicidios', scj['Sumapaz']['CMH26CONT'], 'Sin loc', scj['Sin Localización']['CMH26CONT'])
print('total SCJ H26', sum((x.get('CMH26CONT') or 0) for k, x in scj.items() if k != 'Candelaria'))

BASE = "."  # carpeta del proyecto
"""Votos oficiales de la Alcaldía de Bogotá 2023 por localidad, con los nombres de localidad corregidos."""
import json, os, re, sys, zipfile, unicodedata
import pandas as pd
B = BASE
R = os.path.join(B, 'fuentes_primarias', 'registraduria')
def norm(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()
pob = {norm(a['Localidad']): a['Pobreza monetaria %'] for a in json.load(open(os.path.join(B, 'localidades.json'), encoding='utf-8'))}
ALT = {'CANDELARIA': 'LA CANDELARIA', 'MARTIRES': 'LOS MARTIRES', 'RAFAEL URIBE URIB': 'RAFAEL URIBE URIBE', 'KENNEDY': 'KENNEDY'}
NOMBRE = {'USME': 'Usme', 'CIUDAD BOLIVAR': 'Ciudad Bolívar', 'TUNJUELITO': 'Tunjuelito', 'SANTA FE': 'Santa Fe', 'BOSA': 'Bosa', 'SAN CRISTOBAL': 'San Cristóbal', 'LOS MARTIRES': 'Los Mártires', 'LA CANDELARIA': 'La Candelaria', 'PUENTE ARANDA': 'Puente Aranda', 'ENGATIVA': 'Engativá', 'SUBA': 'Suba', 'ANTONIO NARINO': 'Antonio Nariño', 'FONTIBON': 'Fontibón', 'CHAPINERO': 'Chapinero', 'USAQUEN': 'Usaquén', 'BARRIOS UNIDOS': 'Barrios Unidos', 'TEUSAQUILLO': 'Teusaquillo', 'KENNEDY': 'Kennedy', 'RAFAEL URIBE URIBE': 'Rafael Uribe Uribe', 'SUMAPAZ': 'Sumapaz', 'NACIONAL': 'Nacional'}
def loc(s):
    x = re.sub(r'^LOCALIDAD\s+\d+\s+', '', norm(s)).strip()
    return ALT.get(x, x)
ps = []
with zipfile.ZipFile(os.path.join(R, 'MMV_TERRITORIALES2023_BOGOTA.zip')).open('MMV_2023_16_BOGOTA DC.csv') as f:
    for ch in pd.read_csv(f, encoding='utf-8', dtype=str, chunksize=500000):
        ps.append(ch[ch['Nombre Corporación'] == 'ALCALDE'])
d = pd.concat(ps); d['v'] = pd.to_numeric(d['Total Votos'], errors='coerce').fillna(0); d['L'] = d['Nombre Comuna'].map(loc)
p = d.pivot_table(index='L', columns='Nombre Candidato', values='v', aggfunc='sum', fill_value=0)
p['validos'] = p[[c for c in p.columns if not re.search('NO MARCADOS|NULOS', c)]].sum(axis=1)
C = ['CARLOS FERNANDO GALAN PACHON', 'JUAN DANIEL OVIEDO ARANGO', 'GUSTAVO BOLIVAR MORENO', 'VOTOS EN BLANCO', 'RODRIGO LARA RESTREPO']
s = (100 * p[C].div(p['validos'], axis=0)).round(1)
s['pobreza'] = [pob.get(i) for i in s.index]; s['votos validos'] = p['validos'].astype(int)
print(s.sort_values('pobreza', ascending=False).to_string())
print({c[:14]: round(s[c].corr(s['pobreza']), 2) for c in C}, s['pobreza'].notna().sum())
s = s.reset_index(); s['L'] = s['L'].map(lambda x: NOMBRE.get(x, x))
s.to_json(os.path.join(R, 'alcaldia_2023_localidad.json'), orient='records', force_ascii=False)

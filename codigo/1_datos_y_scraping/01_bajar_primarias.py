BASE = "."  # carpeta del proyecto
"""Baja los anexos oficiales del DANE a fuentes_primarias/dane y lista las hojas de cada uno. También mira las capas de la Secretaría de Seguridad."""
import os, sys
import requests
from openpyxl import load_workbook
D = os.path.join(BASE, 'fuentes_primarias', 'dane')
os.makedirs(D, exist_ok=True)
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36'}
B = 'https://www.dane.gov.co/files/operaciones/'
A = ['EM/bol-EM-2025.pdf', 'EM/anex-EM-viviendas-2025.xlsx', 'EM/anex-EM-hogares-2025.xlsx', 'EM/anex-EM-personas-2025.xlsx', 'EM/anex-EM-pobreza-2025.xlsx', 'EM/anex-EM-discapacidad-y-deficit-habitacional-2025.xlsx',
     'GEIH/bol-GEIH-sep2026.pdf', 'GEIH/anex-GEIH-sep2026.xlsx', 'GEIH/anex-GEIHEISS-jun-ago2026.xlsx', 'PM/bol-PM-2025.pdf', 'PM/anex-PMDepartamental-2025.xlsx', 'ECSC/bol-ECSC-2024.pdf', 'ECSC/anex-ECSC-2024.xlsx']
for a in A:
    f = os.path.join(D, os.path.basename(a))
    if not os.path.exists(f):
        r = requests.get(B + a, headers=H, timeout=120)
        r.raise_for_status()
        open(f, 'wb').write(r.content)
    print(os.path.basename(a), os.path.getsize(f))
for a in A:
    if a.endswith('.xlsx'):
        w = load_workbook(os.path.join(D, os.path.basename(a)), read_only=True, data_only=True)
        print('\n##', os.path.basename(a), len(w.sheetnames))
        for n in w.sheetnames[:45]:
            s = w[n]
            tit = [str(c) for fila in s.iter_rows(min_row=1, max_row=12, values_only=True) for c in fila if isinstance(c, str) and len(c) > 15][:2]
            print('  ', n[:22], '|', ' // '.join(t[:95] for t in tit))
print('\n## Secretaría de Seguridad, capas')
j = requests.get('https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/CifrasSCJ/MapServer', params={'f': 'json'}, headers=H, timeout=30, verify=True).json()
for l in j.get('layers', [])[:60]:
    print('  ', l['id'], l['name'])

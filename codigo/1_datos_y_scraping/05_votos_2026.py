BASE = "."  # carpeta del proyecto
"""Primera vuelta presidencial 2026 en Bogotá, por localidad, desde el archivo oficial de escrutinio de la Registraduría."""
import io, json, os, re, sys, zipfile, unicodedata
import pandas as pd
pd.set_option('display.width', 200, 'display.max_columns', 20)
B = BASE
R = os.path.join(B, 'fuentes_primarias', 'registraduria')
def norm(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()
z = zipfile.ZipFile(os.path.join(R, 'MMV_Presidente1V_2026.zip'))
pre = 'MMV_Presidente1V_2026/MMV_Presidente1V_2026/'
zz = zipfile.ZipFile(io.BytesIO(z.read(pre + 'ARCHIVOSBASICOS_AUDITORES_PRESIDENTE_2026_V3.zip')))
b = 'ARCHIVOSBASICOS_AUDITORES_PRESIDENTE_2026_V3/'
div = {}
for x in zz.read(b + 'DIVIPOL_20260526_132437_01.TXT').decode('latin-1').splitlines():
    if x[:2] == '16':
        div[(x[2:5], x[5:7], x[7:9])] = re.sub(r'^LOCALIDAD\s+\d+\s+', '', norm(x[-30:])).strip()
print('puestos', len(div), sorted(set(div.values())))
cand = {}
for x in zz.read(b + 'CANDIDATOS_20260516_083436_01.TXT').decode('latin-1').splitlines():
    cand[x[16:19]] = (x[20:70].strip() + ' ' + x[70:120].strip())
print(cand)
filas = []; nac = {}
with z.open(pre + '_ficheros_MMV_4_MMV_9999_ESCRUTINIO.csv') as f:
    for ln in io.TextIOWrapper(f, encoding='latin-1'):
        p = ln.strip().split(';')
        if len(p) < 12:
            continue
        nac[p[10]] = nac.get(p[10], 0) + int(p[11] or 0)
        if p[1] == '16':
            filas.append((div.get((p[2], p[3][-2:], p[4]), 'SIN'), p[10], int(p[11] or 0)))
d = pd.DataFrame(filas, columns=['L', 'c', 'v'])
print('nacional', {cand.get(k, k): v for k, v in sorted(nac.items(), key=lambda a: -a[1])[:8]})
t = d.groupby('c').v.sum().sort_values(ascending=False)
print({cand.get(k, k): int(v) for k, v in t.items()})
p = d.pivot_table(index='L', columns='c', values='v', aggfunc='sum', fill_value=0)
print(list(p.columns))
reales = [c for c in p.columns if c in cand] + [c for c in p.columns if c not in cand]
noval = [c for c in p.columns if c not in cand and c not in ('996',)]
print('códigos no candidatos', [c for c in p.columns if c not in cand], {c: int(t[c]) for c in p.columns if c not in cand})
base = p[[c for c in p.columns if c in cand or c == '996']].sum(axis=1)
s = (100 * p[['011', '002', '001', '004', '012']].div(base, axis=0)).round(1)
s.columns = ['Valencia', 'López', 'Cepeda', 'De la Espriella', 'Fajardo']
loc = {norm(a['Localidad']): a['Pobreza monetaria %'] for a in json.load(open(os.path.join(B, 'localidades.json'), encoding='utf-8'))}
ALT = {'CANDELARIA': 'LA CANDELARIA', 'MARTIRES': 'LOS MARTIRES', 'RAFAEL URIBE URIB': 'RAFAEL URIBE URIBE'}
s['pobreza'] = [loc.get(ALT.get(i, i)) for i in s.index]; s['base'] = base.astype(int)
print(s.sort_values('pobreza', ascending=False).to_string())
print('Bogotá %', {cand[c]: round(100 * t[c] / base.sum(), 2) for c in ['011', '002', '001', '004', '012']}, int(base.sum()))
print({c: round(s[c].corr(s['pobreza']), 2) for c in ['Valencia', 'López', 'Cepeda', 'De la Espriella', 'Fajardo']})
s.reset_index().to_json(os.path.join(R, 'presidente_2026_localidad.json'), orient='records', force_ascii=False)

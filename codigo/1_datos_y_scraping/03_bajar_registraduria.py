BASE = "."  # carpeta del proyecto
"""Baja el archivo oficial de votos de las territoriales de 2023 para Bogotá. No lo descomprime; solo lista lo que trae."""
import os, sys, zipfile
import requests
D = os.path.join(BASE, 'fuentes_primarias', 'registraduria')
os.makedirs(D, exist_ok=True)
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36', 'Referer': 'https://observatorio.registraduria.gov.co/views/electoral/historicos-resultados.php'}
BASE = 'https://observatorio.registraduria.gov.co'
t = requests.get(BASE + '/js/downloads.js', headers=H, timeout=30).text
i = t.index('function startDownload()')
print(t[i:i + 900])
for n in ['BOGOTÁ', 'BOGOTA']:
    for pre in ['/comprimidos/', '/anexos/', '/comprimidosTwo/']:
        u = f'{BASE}{pre}MMV_TERRITORIALES2023_{n}.zip'
        try:
            r = requests.get(u, headers={**H, 'Range': 'bytes=0-3'}, timeout=30)
            print(r.status_code, r.headers.get('content-type'), r.headers.get('content-range'), r.content[:4], u)
            if r.content[:2] == b'PK':
                f = os.path.join(D, 'MMV_TERRITORIALES2023_BOGOTA.zip')
                with requests.get(u, headers=H, timeout=600, stream=True) as g:
                    with open(f, 'wb') as o:
                        for c in g.iter_content(1 << 20):
                            o.write(c)
                print('bajado', os.path.getsize(f))
                print([(x.filename, x.file_size) for x in zipfile.ZipFile(f).infolist()][:30])
                sys.exit()
        except Exception as e:
            print('ERR', type(e).__name__, u)

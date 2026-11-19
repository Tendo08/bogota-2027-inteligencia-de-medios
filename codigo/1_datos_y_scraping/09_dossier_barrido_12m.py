BASE = "."  # carpeta del proyecto
"""Barrido ampliado a 12 meses (12 nov 2025 - 11 nov 2026), la misma ventana de 'últimos 12 meses' de Google Trends.
Ventanas de medio mes (Google News devuelve ~100 resultados por consulta: ventanas cortas = menos notas perdidas),
más variantes de búsqueda y consultas por sitio partidas por trimestre. Se suma al barrido anterior sin repetir."""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET
import pandas as pd
import requests
from bs4 import BeautifulSoup
D = BASE
OUT = os.path.join(D, 'dossier_datos')
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36', 'Accept-Language': 'es-CO,es;q=0.9'}
LIMITE = time.time() + 1800
INI, FIN = '2025-11-12', '2026-11-11'
QUINCENAS = []
for p in pd.date_range('2025-11-01', '2026-11-30', freq='MS'):
    m = p + pd.offsets.MonthBegin(1)
    QUINCENAS += [(p.strftime('%Y-%m-%d'), (p + pd.Timedelta(days=15)).strftime('%Y-%m-%d')), ((p + pd.Timedelta(days=15)).strftime('%Y-%m-%d'), m.strftime('%Y-%m-%d'))]
QUINCENAS = [(a, b) for a, b in QUINCENAS if b > INI and a <= FIN]
TRIM = [('2025-11-12', '2026-02-12'), ('2026-02-12', '2026-05-12'), ('2026-05-12', '2026-08-12'), ('2026-08-12', '2026-11-12')]
VARIANTES = ['"Carlos Carrillo"', '"Carlos Carrillo" UNGRD', '"Carlos Carrillo" Bogotá', '"Carlos Carrillo" Alcaldía', '"Carlos Carrillo" Petro',
             '"Carrillo" UNGRD', '"Carlos Carrillo" Pacto Histórico', '"Carlos Carrillo" Quintero', '"Carlos Carrillo" Procuraduría', '"Carlos Carrillo" Senado']
SITIOS = ['eltiempo.com', 'elespectador.com', 'semana.com', 'infobae.com', 'noticiascaracol.com', 'noticiasrcn.com', 'bluradio.com', 'lafm.com.co', 'caracol.com.co',
          'pulzo.com', 'publimetro.co', 'cambiocolombia.com', 'elcolombiano.com', 'wradio.com.co', 'kienyke.com', 'lasillavacia.com', 'elnuevosiglo.com.co', 'larepublica.co',
          'valoraanalitik.com', 'vanguardia.com', 'elheraldo.co', 'elpais.com.co', 'citytv.eltiempo.com', 'canalcapital.gov.co', 'hsbnoticias.com', 'regioncapital.co',
          'bogotaampm.com', 'qhubobogota.com', 'extra.com.co', 'alpunto.com.co', '360radio.com.co', 'las2orillas.co', 'razonpublica.com', 'rtvcnoticias.com', 'radionacional.co',
          'canal1.com.co', 'cablenoticias.tv', 'eje21.com.co', 'confidencialcolombia.com', 'lanuevaprensa.com.co', 'elolfato.com', 'minuto60.com', 'asuntoslegales.com.co', 'portafolio.co']
WP = {'La Silla Vacía': 'https://www.lasillavacia.com', '360 Radio': 'https://360radio.com.co', 'Las2orillas': 'https://www.las2orillas.co', 'Razón Pública': 'https://razonpublica.com', 'Al Punto': 'https://alpunto.com.co'}


def google(q):
    for intento in range(3):
        try:
            r = requests.get(f'https://news.google.com/rss/search?q={quote(q)}&hl=es-419&gl=CO&ceid=CO:es-419', headers=H, timeout=30)
            if r.status_code == 429:
                time.sleep(20); continue
            out = []
            for i in ET.fromstring(r.content).findall('.//item'):
                t = i.findtext('title') or ''; src = i.findtext('source') or ''
                t = re.sub(r'\s+-\s+' + re.escape(src) + r'\s*$', '', t)
                f = pd.to_datetime(i.findtext('pubDate'), errors='coerce', utc=True)
                if pd.notna(f) and INI <= f.strftime('%Y-%m-%d') <= FIN:
                    out.append({'medio': src, 'titulo': t, 'fecha': f.strftime('%Y-%m-%d'), 'url': i.findtext('link'), 'via': 'Google News', 'consulta': q})
            return out
        except Exception:
            time.sleep(3)
    return []


def wp(medio, base, q):
    out = []
    for pag in range(1, 6):
        try:
            r = requests.get(f'{base}/wp-json/wp/v2/posts', params={'search': q, 'after': INI + 'T00:00:00', 'per_page': 50, 'page': pag}, headers=H, timeout=25)
            if not (r.ok and r.headers.get('content-type', '').startswith('application/json')):
                break
            js = r.json()
            out += [{'medio': medio, 'titulo': BeautifulSoup(p['title']['rendered'], 'lxml').get_text(), 'fecha': p['date'][:10], 'url': p['link'], 'url_real': p['link'],
                     'via': 'API del medio', 'consulta': q, 'texto': BeautifulSoup(p['content']['rendered'], 'lxml').get_text(' ')} for p in js]
            if len(js) < 50:
                break
        except Exception:
            break
    return out


def real(u):
    try:
        aid = urlparse(u).path.split('/')[-1]
        h = requests.get(f'https://news.google.com/rss/articles/{aid}', headers=H, timeout=20).text
        div = BeautifulSoup(h, 'lxml').select_one('[data-n-a-sg]')
        pl = f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{aid}",{div["data-n-a-ts"]},"{div["data-n-a-sg"]}"]'
        r = requests.post('https://news.google.com/_/DotsSplashUi/data/batchexecute', headers={**H, 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'},
                          data={'f.req': json.dumps([[['Fbv4je', pl, None, 'generic']]])}, timeout=20)
        return json.loads(json.loads(r.text.split('\n\n')[1])[0][2])[1]
    except Exception:
        return None


def cuerpo(u):
    try:
        r = requests.get(u, headers=H, timeout=20)
        if not r.ok:
            return ''
        s = BeautifulSoup(r.content, 'lxml')
        for x in s(['script', 'style', 'aside', 'nav', 'footer', 'figure']):
            x.decompose()
        return ' '.join(p.get_text(' ', strip=True) for p in s.find_all('p') if len(p.get_text(strip=True)) > 40)
    except Exception:
        return ''


consultas = [f'{v} after:{a} before:{b}' for v in VARIANTES for a, b in QUINCENAS]
consultas += [f'"Carlos Carrillo" site:{s} after:{a} before:{b}' for s in SITIOS for a, b in TRIM]
print('consultas', len(consultas), flush=True)
with ThreadPoolExecutor(4) as ex:
    lotes = list(ex.map(google, consultas))
print('consultas con resultados', sum(bool(l) for l in lotes), flush=True)

viejo = json.load(open(os.path.join(OUT, 'carrillo_bruto.json'), encoding='utf-8'))['notas']
notas = {(n['medio'], n['titulo']): n for n in viejo}
nuevas = 0
for l in lotes:
    for n in l:
        k = (n['medio'], n['titulo'])
        if k in notas:
            notas[k]['consultas'] = notas[k].get('consultas', 1) + 1
        else:
            notas[k] = n; nuevas += 1
for m, b in WP.items():
    for q in ['Carlos Carrillo', 'Carrillo UNGRD']:
        for x in wp(m, b, q):
            if (x['medio'], x['titulo']) not in notas:
                notas[(x['medio'], x['titulo'])] = x; nuevas += 1
print('anteriores', len(viejo), 'nuevas', nuevas, flush=True)
L = list(notas.values())


def trabajar(n):
    if time.time() > LIMITE:
        n.setdefault('url_real', None); return n
    if not n.get('url_real'):
        n['url_real'] = real(n['url']) if 'news.google.com' in n['url'] else n['url']
        time.sleep(.2)
    if not n.get('texto') and n['url_real']:
        n['texto'] = cuerpo(n['url_real'])
    return n


with ThreadPoolExecutor(10) as ex:
    L = list(ex.map(trabajar, L))
json.dump({'ventana': [INI, FIN], 'consultas': consultas, 'notas': L}, open(os.path.join(OUT, 'carrillo_bruto_12m.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('notas', len(L), 'enlace real', sum(1 for n in L if n.get('url_real')), 'con texto', sum(1 for n in L if len(n.get('texto') or '') > 300))
print(pd.Series([n['fecha'][:7] for n in L]).value_counts().sort_index().to_string())

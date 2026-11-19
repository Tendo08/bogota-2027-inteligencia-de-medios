BASE = "."  # carpeta del proyecto
"""Dossier 12 nov: barrido dedicado a Carlos Carrillo, 1 jun - 11 nov 2026.
Google News por mes y por sitio + API WordPress de medios que la tienen; enlace real y texto de cada nota."""
import json, os, re, sys, time, unicodedata
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET
import pandas as pd
import requests
from bs4 import BeautifulSoup
D = BASE
OUT = os.path.join(D, 'dossier_datos'); os.makedirs(OUT, exist_ok=True)
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36', 'Accept-Language': 'es-CO,es;q=0.9'}
LIMITE = time.time() + 540
MESES = [('2026-06-01', '2026-07-01'), ('2026-07-01', '2026-08-01'), ('2026-08-01', '2026-09-01'), ('2026-09-01', '2026-10-01'), ('2026-10-01', '2026-11-01'), ('2026-11-01', '2026-11-12')]
VARIANTES = ['"Carlos Carrillo"', '"Carlos Carrillo" UNGRD', '"Carlos Carrillo" Bogotá', '"Carlos Carrillo" Alcaldía', '"Carlos Carrillo" Petro', '"Carrillo" exdirector UNGRD']
SITIOS = ['eltiempo.com', 'elespectador.com', 'semana.com', 'infobae.com', 'noticiascaracol.com', 'noticiasrcn.com', 'bluradio.com', 'lafm.com.co', 'caracol.com.co',
          'pulzo.com', 'publimetro.co', 'cambiocolombia.com', 'elcolombiano.com', 'wradio.com.co', 'kienyke.com', 'lasillavacia.com', 'elnuevosiglo.com.co', 'larepublica.co',
          'valoraanalitik.com', 'vanguardia.com', 'elheraldo.co', 'elpais.com.co', 'citytv.eltiempo.com', 'canalcapital.gov.co', 'hsbnoticias.com', 'regioncapital.co',
          'bogotaampm.com', 'qhubobogota.com', 'extra.com.co', 'alpunto.com.co', '360radio.com.co', 'las2orillas.co', 'razonpublica.com', 'rtvcnoticias.com', 'radionacional.co',
          'canal1.com.co', 'cablenoticias.tv', 'eje21.com.co', 'confidencialcolombia.com', 'lanuevaprensa.com.co', 'elolfato.com', 'minuto60.com', 'asuntoslegales.com.co', 'portafolio.co']
WP = {'La Silla Vacía': 'https://www.lasillavacia.com', '360 Radio': 'https://360radio.com.co', 'Las2orillas': 'https://www.las2orillas.co', 'Razón Pública': 'https://razonpublica.com', 'Al Punto': 'https://alpunto.com.co'}


def google(q):
    try:
        r = requests.get(f'https://news.google.com/rss/search?q={quote(q)}&hl=es-419&gl=CO&ceid=CO:es-419', headers=H, timeout=30)
        out = []
        for i in ET.fromstring(r.content).findall('.//item'):
            t = i.findtext('title') or ''; src = i.findtext('source') or ''
            t = re.sub(r'\s+-\s+' + re.escape(src) + r'\s*$', '', t)
            f = pd.to_datetime(i.findtext('pubDate'), errors='coerce', utc=True)
            if pd.notna(f) and '2026-06-01' <= f.strftime('%Y-%m-%d') <= '2026-11-11':
                out.append({'medio': src, 'titulo': t, 'fecha': f.strftime('%Y-%m-%d'), 'url': i.findtext('link'), 'via': 'Google News', 'consulta': q})
        return out
    except Exception:
        return []


def wp(medio, base, q):
    try:
        r = requests.get(f'{base}/wp-json/wp/v2/posts', params={'search': q, 'after': '2026-06-01T00:00:00', 'per_page': 50}, headers=H, timeout=25)
        if r.ok and r.headers.get('content-type', '').startswith('application/json'):
            return [{'medio': medio, 'titulo': BeautifulSoup(p['title']['rendered'], 'lxml').get_text(), 'fecha': p['date'][:10], 'url': p['link'], 'url_real': p['link'],
                     'via': 'API del medio', 'consulta': q, 'texto': BeautifulSoup(p['content']['rendered'], 'lxml').get_text(' ')} for p in r.json()]
    except Exception:
        pass
    return []


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


consultas = [f'{v} after:{a} before:{b}' for v in VARIANTES for a, b in MESES]
consultas += [f'"Carlos Carrillo" site:{s} after:2026-06-01' for s in SITIOS]
with ThreadPoolExecutor(6) as ex:
    lotes = list(ex.map(google, consultas))
notas = {}
for l in lotes:
    for n in l:
        k = (n['medio'], n['titulo'])
        if k in notas:
            notas[k]['consultas'] = notas[k].get('consultas', 1) + 1
        else:
            notas[k] = n
print('google', len(notas), flush=True)
for m, b in WP.items():
    for x in wp(m, b, 'Carlos Carrillo'):
        notas.setdefault((x['medio'], x['titulo']), x)
print('con wp', len(notas), flush=True)
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
json.dump({'ventana': ['2026-06-01', '2026-11-11'], 'consultas': consultas, 'notas': L}, open(os.path.join(OUT, 'carrillo_bruto.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('notas', len(L), 'enlace real', sum(1 for n in L if n.get('url_real')), 'con texto', sum(1 for n in L if len(n.get('texto') or '') > 300))
print(pd.Series([n['medio'] for n in L]).value_counts().head(50).to_string())

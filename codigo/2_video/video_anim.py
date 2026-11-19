"""Animaciones del video (1920x1080, 30 fps): cada escena es una función de tiempo que dibuja un cuadro con PIL,
más una lista de efectos de sonido (tiempo, archivo, volumen). Uso: python video_anim.py [escena ...]"""
import json, math, os, random, sys, unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from shapely.geometry import shape

D = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(D, 'ENTREGA_VIDEO'); SON = os.path.join(V, 'sonidos'); ESC = os.path.join(V, 'escenas'); os.makedirs(ESC, exist_ok=True)
FOT = os.path.join(D, 'ENTREGA_DOSSIER', 'fotos')
W, H, FPS = 1920, 1080, 30
TINTA, PAPEL, OXIDO, ORO, AZUL, NEON, ROJO = (20, 18, 16), (244, 240, 232), (217, 88, 59), (242, 182, 50), (47, 111, 143), (57, 255, 136), (235, 52, 52)
FUENTES = {'impact': 'impact.ttf', 'bold': 'segoeuib.ttf', 'reg': 'segoeui.ttf', 'serif': 'georgiab.ttf', 'mono': 'consolab.ttf', 'bahn': 'bahnschrift.ttf'}
_fc = {}


def F(nombre, tam):
    k = (nombre, tam)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(os.path.join(r'C:\Windows\Fonts', FUENTES[nombre]), tam)
    return _fc[k]


def prog(t, a, b):
    return 0.0 if t <= a else 1.0 if t >= b else (t - a) / (b - a)


def out_cubic(x):
    return 1 - (1 - x) ** 3


def out_back(x, s=1.9):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def in_out(x):
    return 3 * x * x - 2 * x * x * x


def texto(dr, xy, s, fuente, color=PAPEL, anchor='mm', borde=0, color_borde=TINTA, espacio=0):
    # PIL ignora la transparencia del texto: si el color trae alfa < 255, lo dibujo en una capa aparte
    if len(color) == 4 and color[3] < 255:
        if color[3] <= 0:
            return
        base = getattr(dr, '_image', None)
        x0, y0, x1, y1 = dr.textbbox(xy, s, font=fuente, anchor=anchor, stroke_width=borde, spacing=espacio)
        x0, y0 = int(x0) - 2, int(y0) - 2
        capa = Image.new('RGBA', (int(x1) - x0 + 4, int(y1) - y0 + 4), (0, 0, 0, 0))
        ImageDraw.Draw(capa).text((xy[0] - x0, xy[1] - y0), s, font=fuente, fill=tuple(color[:3]) + (255,), anchor=anchor, stroke_width=borde,
                                  stroke_fill=tuple(color_borde[:3]), spacing=espacio)
        capa.putalpha(capa.getchannel('A').point(lambda v: v * color[3] // 255))
        if base is not None and base.mode in ('RGB', 'RGBA'):
            base.paste(capa, (x0, y0), capa)
            return
    dr.text(xy, s, font=fuente, fill=color, anchor=anchor, stroke_width=borde, stroke_fill=color_borde, spacing=espacio)


def camara(img, zoom=1.0, cx=W / 2, cy=H / 2, dx=0, dy=0):
    zoom = max(zoom, 1.0)
    if zoom == 1 and dx == 0 and dy == 0:
        return img
    w, h = W / zoom, H / zoom
    x0 = min(max(cx - w / 2 + dx, 0), W - w); y0 = min(max(cy - h / 2 + dy, 0), H - h)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))


def sacudida(t, golpes, fuerza=22, dur=0.35):
    dx = dy = 0.0
    for g in golpes:
        if g <= t < g + dur:
            a = fuerza * (1 - (t - g) / dur)
            r = random.Random(int(t * 1000))
            dx += r.uniform(-a, a); dy += r.uniform(-a, a)
    return dx, dy


_cache = {}


def foto(nombre, w, h, gris=0.0, borde=0, color_borde=PAPEL):
    k = (nombre, w, h, round(gris, 2), borde)
    if k in _cache:
        return _cache[k]
    im = Image.open(os.path.join(FOT, nombre)).convert('RGB')
    im = ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.25))
    if gris > 0:
        im = Image.blend(im, ImageOps.grayscale(im).convert('RGB'), gris)
    if borde:
        im = ImageOps.expand(im, borde, color_borde)
    if len(_cache) > 400:
        _cache.clear()
    _cache[k] = im
    return im


def pegar(base, im, cx, cy, escala=1.0, angulo=0.0, alfa=1.0):
    if escala <= 0.01 or alfa <= 0.01:
        return
    im = im.convert('RGBA')
    if escala != 1:
        im = im.resize((max(1, int(im.width * escala)), max(1, int(im.height * escala))), Image.BICUBIC)
    if angulo:
        im = im.rotate(angulo, Image.BICUBIC, expand=True)
    if alfa < 1:
        a = im.getchannel('A').point(lambda v: int(v * alfa)); im.putalpha(a)
    base.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def lienzo(color=TINTA):
    return Image.new('RGB', (W, H), color)


def comp(base, capa):
    base.paste(capa, (0, 0), capa)


_vin = None


def viñeta(img):
    global _vin
    if _vin is None:
        y, x = np.ogrid[:H, :W]
        d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        a = (np.clip(d - 0.55, 0, 1) * 190).astype(np.uint8)
        _vin = Image.fromarray(np.dstack([np.zeros_like(a)] * 3 + [a]), 'RGBA')
    img.paste(_vin, (0, 0), _vin)
    return img


def fuente_pie(dr, s):
    texto(dr, (40, H - 34), s, F('reg', 24), (200, 194, 184), anchor='lm')


# ------------------------------------------------------------------ datos
LOC = {o['nombre']: o for o in json.load(open(os.path.join(D, 'mapa_localidades.json'), encoding='utf-8'))}
URB = json.load(open(os.path.join(D, 'dossier_datos', 'localidades_urbanas.json'), encoding='utf-8'))
LD = {a['Localidad']: a for a in json.load(open(os.path.join(D, 'localidades.json'), encoding='utf-8'))}


def poligonos(cx, cy, alto):
    """Localidades urbanas en píxeles, centradas en (cx, cy), con la altura dada."""
    lon0, lon1, lat0, lat1 = -74.225, -73.99, 4.465, 4.84
    k = alto / (lat1 - lat0)
    ox = cx - (lon1 - lon0) * k / 2; oy = cy - alto / 2
    out = {}
    for n, g in URB.items():
        sh = shape(g)
        ps = [sh] if sh.geom_type == 'Polygon' else list(sh.geoms)
        out[n] = {'polys': [[(ox + (x - lon0) * k, oy + (lat1 - y) * k) for x, y in p.exterior.coords] for p in ps],
                  'c': (ox + (sh.representative_point().x - lon0) * k, oy + (lat1 - sh.representative_point().y) * k)}
    return out


def mezcla(c1, c2, x):
    return tuple(int(a + (b - a) * x) for a, b in zip(c1, c2))


# ------------------------------------------------------------------ escenas
def esc_cifras():
    """Escena 1 (provisional): cifras que caen sobre Bogotá; luego se cambia el fondo por los clips de noticieros."""
    dur = 14.0
    fondo = Image.open(os.path.join(V, '..', 'ENTREGA_DOSSIER', 'graficas', '..', 'fotos', 'transmilenio.jpg')).convert('RGB')
    fondo = ImageEnhance.Brightness(ImageOps.fit(fondo, (W + 200, H + 120), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3))).enhance(0.45)
    CIF = [(1.0, '26 %', 'aprueba la gestión del alcalde', 'Bogotá Cómo Vamos 2025'),
           (4.8, '62 %', 'se siente inseguro: récord desde 2008', 'Bogotá Cómo Vamos 2025'),
           (8.6, '589 → 1.639', 'casos de extorsión (ene-sep, 2018 vs. 2026)', 'Secretaría de Seguridad')]
    golpes = [c[0] for c in CIF]

    def f(t):
        im = lienzo(); im.paste(fondo.crop((int(100 * t / dur), int(60 * t / dur), int(100 * t / dur) + W, int(60 * t / dur) + H)), (0, 0))
        dr = ImageDraw.Draw(im, 'RGBA')
        texto(dr, (W / 2, 120), 'BOGOTÁ, 2026', F('impact', 64), (255, 255, 255), borde=3)
        for t0, big, small, src in CIF:
            if t <= t0:
                continue
            x = prog(t, t0, t0 + 0.35); s = 2.4 - 1.4 * out_cubic(x)
            sale = prog(t, t0 + 3.3, t0 + 3.7)
            if sale >= 1:
                continue
            capa = Image.new('RGBA', (1500, 420), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
            texto(d2, (750, 160), big, F('impact', 210), ORO if 'extorsión' not in small else OXIDO, borde=6)
            texto(d2, (750, 330), small.upper(), F('bold', 54), (255, 255, 255), borde=3)
            pegar(im, capa, W / 2 - sale * 1400, H / 2 + 40, s, alfa=min(1, x * 3))
            fuente_pie(dr, 'Fuente: ' + src)
        dx, dy = sacudida(t, [g + 0.3 for g in golpes])
        return camara(viñeta(im), 1.0 + 0.04 * math.sin(t), dx=dx, dy=dy)
    sfx = [(0.0, 'musica_dramatica', 0.0)] + [(g, 'whoosh_cine', 0.7) for g in golpes] + [(g + 0.3, 'impacto', 0.9) for g in golpes]
    return dur, f, sfx[1:]


def esc_wanted():
    C = [('oviedo.jpg', 'FALSO CENTRO'), ('valencia.png', 'HABLA DEL PAÍS, NO DE BOGOTÁ'), ('lopez.jpg', 'UNA GESTIÓN RARA: PELEAS Y PROMESAS A MEDIAS'),
         ('penalosa.jpg', 'UN TRANSMILENIO QUE HOY COLAPSA')]
    T = 3.6; dur = T * len(C)

    def estrella(d, cx, cy, r, color):
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=color, outline=(0, 0, 0), width=4)

    def f(t):
        i = min(int(t // T), len(C) - 1); lt = t - i * T
        img_n, frase = C[i]
        gris = prog(lt, 2.3, 2.6)
        im = lienzo((14, 14, 16))
        fondo = foto(img_n, W, H, gris=1.0).filter(ImageFilter.GaussianBlur(25))
        im.paste(ImageEnhance.Brightness(fondo).enhance(0.35), (0, 0))
        dr = ImageDraw.Draw(im, 'RGBA')
        ent = out_back(prog(lt, 0, 0.4))
        pegar(im, foto(img_n, 560, 700, gris=gris, borde=8, color_borde=(240, 240, 240)), W / 2 - 330, H / 2 + 20, ent)
        texto(dr, (1290, 250), 'NIVEL DE BÚSQUEDA', F('impact', 64), (255, 255, 255), borde=4)
        for k in range(5):
            on = lt > 0.5 + k * 0.22
            parp = on and lt < 2.3 and int(lt * 8) % 2 == 0
            estrella(dr, 1050 + k * 120, 360, 50, (255, 210, 60) if on and not parp else (255, 255, 255) if parp else (60, 60, 60))
        if lt > 1.4:
            a = prog(lt, 1.4, 1.7)
            for k, linea in enumerate(__import__('textwrap').wrap(frase, 18)):
                texto(dr, (1290, 520 + k * 92), linea, F('impact', 84), (255, 255, 255, int(255 * a)), borde=5)
        if lt > 2.3:
            x = prog(lt, 2.3, 2.5)
            dr.rectangle([0, 820, W, 980], fill=(0, 0, 0, int(190 * x)))
            texto(dr, (W / 2, 900), 'DESCARTADO', F('impact', int(150 * (1.5 - 0.5 * out_cubic(x)))), (215, 35, 35), borde=6, color_borde=(0, 0, 0))
        sale = in_out(prog(lt, T - 0.3, T))
        if sale > 0:
            dr.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * sale)))
        dx, dy = sacudida(t, [k * T + 2.32 for k in range(len(C))], 26)
        return camara(viñeta(im), 1.0 + 0.04 * prog(lt, 0, T), dx=dx, dy=dy)
    sfx = []
    for k in range(len(C)):
        sfx += [(k * T, 'whoosh_rapido', 0.5), (k * T + 0.5, 'alarma_retro', 0.35), (k * T + 2.3, 'impacto_trailer', 0.8), (k * T + 2.32, 'vinilo_stop', 0.4)]
    return dur, f, sfx


def esc_carrillo():
    dur = 7.0
    preg = '¿Este hombre podrá cambiar el rumbo\nde la ciudad más importante de Colombia?'
    r = random.Random(5); chispas = [(r.uniform(0, W), r.uniform(0, H), r.uniform(0.5, 2.5), r.uniform(0, 6.28)) for _ in range(90)]

    def f(t):
        luz = prog(t, 0, 0.8)
        im = lienzo(mezcla((12, 10, 8), (60, 40, 10), luz)); dr = ImageDraw.Draw(im, 'RGBA')
        cx, cy = W / 2, 430
        rayos = Image.new('RGBA', (W, H), (0, 0, 0, 0)); drr = ImageDraw.Draw(rayos)
        for k in range(18):
            a = k * math.pi / 9 + t * 0.25
            drr.polygon([(cx, cy), (cx + 1600 * math.cos(a - 0.06), cy + 1600 * math.sin(a - 0.06)), (cx + 1600 * math.cos(a + 0.06), cy + 1600 * math.sin(a + 0.06))], fill=(255, 210, 90, int(55 * luz)))
        comp(im, rayos.filter(ImageFilter.GaussianBlur(6)))
        halo = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dh = ImageDraw.Draw(halo)
        rr = 330 + 12 * math.sin(t * 4)
        dh.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(255, 220, 120, int(150 * luz)))
        comp(im, halo.filter(ImageFilter.GaussianBlur(60)))
        s = out_back(prog(t, 0.6, 1.2), 2.4)
        pegar(im, foto('carrillo.jpg', 520, 660, borde=10, color_borde=(255, 236, 180)), cx, cy + 20, s * (1 + 0.015 * math.sin(t * 3)))
        for x, y, sz, ph in chispas:
            a = 0.5 + 0.5 * math.sin(t * 5 + ph)
            if luz > 0.5 and a > 0.6:
                dr.regular_polygon((x, (y - t * 30 * sz) % H, 6 * sz), 4, rotation=45, fill=(255, 240, 180, int(255 * a)))
        n = int(len(preg) * prog(t, 2.0, 5.0))
        if n:
            texto(dr, (W / 2, 900), preg[:n], F('bold', 58), (255, 255, 255), borde=4, espacio=10)
        return camara(viñeta(im), 1.0 + 0.05 * prog(t, 1.2, 7))
    sfx = [(0.0, 'redoble_angelical', 0.25), (0.55, 'coro_brillo', 0.3), (0.6, 'boing', 0.1), (2.0, 'glitch_texto', 0.15), (5.1, 'suspenso_concurso', 0.25)]
    return dur, f, sfx


def esc_problema():
    dur = 15.0

    def barra(dr, x, y, w, h, frac, color, etiqueta, valor, fuente_v):
        dr.rounded_rectangle([x, y, x + w, y + h], 14, fill=(45, 42, 38))
        if frac > 0:
            dr.rounded_rectangle([x, y, x + max(28, w * frac), y + h], 14, fill=color)
        texto(dr, (x, y - 44), etiqueta, F('bold', 42), (255, 255, 255), anchor='lm')
        texto(dr, (x + max(28, w * frac) + 30, y + h / 2), valor, fuente_v, (255, 255, 255), anchor='lm', borde=3)

    def f(t):
        im = lienzo((18, 16, 14)); dr = ImageDraw.Draw(im, 'RGBA')
        if t < 5.2:
            n = int(1093 * out_cubic(prog(t, 0.2, 2.6)))
            texto(dr, (W / 2, 380), f'{n:,}'.replace(',', '.'), F('impact', 260), (255, 255, 255), borde=6)
            texto(dr, (W / 2, 560), 'NOTICIAS HABLARON DE ÉL EN UN AÑO', F('bold', 60), (220, 214, 204))
            if t > 3.0:
                x = prog(t, 3.0, 3.25); s = 2.6 - 1.6 * out_cubic(x)
                capa = Image.new('RGBA', (1400, 260), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                texto(d2, (700, 130), 'EN UN BARRIO: 0', F('impact', 190), ROJO, borde=8, color_borde=(255, 255, 255))
                pegar(im, capa, W / 2, 800, s, angulo=-4)
            fuente_pie(dr, 'Corpus propio: 1.093 notas de 85 medios, 12 nov 2025 - 11 nov 2026')
            z = 1.0 + (0.18 * out_cubic(prog(t, 3.2, 3.6)) if t < 5.2 else 0)
            dx, dy = sacudida(t, [3.2], 30)
            return camara(viñeta(im), z, cy=760, dx=dx, dy=dy)
        lt = t - 5.2
        texto(dr, (W / 2, 120), 'LA MISMA ENTREVISTA, DOS FRASES. ¿CUÁL FUE NOTICIA?', F('impact', 80), ORO, borde=3)
        f1 = out_cubic(prog(lt, 0.6, 2.6)); n1 = int(52 * f1)
        barra(dr, 220, 380, 1250, 120, f1, OXIDO, '"SE VA A INCENDIAR EL PAÍS"', f'{n1} notas', F('impact', 90))
        if f1 > 0.05:
            r = random.Random(int(t * 20))
            for _ in range(26):
                x = 220 + r.uniform(0, 1250 * f1); y = 380 + r.uniform(-60, 20)
                dr.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(255, r.randint(120, 200), 40, 210))
        if lt > 3.4:
            f2 = out_cubic(prog(lt, 3.4, 4.0))
            barra(dr, 220, 700, 1250, 120, f2 * 2 / 52, AZUL, '"SOY UN HOMBRE LIBRE" (ALCALDÍA)', f'{int(round(2 * f2))} notas', F('impact', 90))
        fuente_pie(dr, 'Notas del corpus del 14 de junio al 5 de julio de 2026 · Entrevista en Me Vale (Eva Rey)')
        z = 1.0 + 0.9 * out_cubic(prog(lt, 4.6, 4.9)) * (1 - prog(lt, 7.6, 8.0))
        dx, dy = sacudida(t, [5.2 + 2.6], 26)
        return camara(viñeta(im), z, cx=330, cy=760, dx=dx, dy=dy)
    sfx = [(0.2, 'tictac', 0.5), (3.15, 'error', 0.8), (3.2, 'impacto', 0.9), (5.2, 'whoosh_cine', 0.6), (5.8, 'fuego', 0.7), (7.8, 'impacto_trailer', 0.8),
           (8.6, 'pop', 0.6), (9.2, 'grillos', 0.9), (9.8, 'vinilo_stop', 0.6)]
    return dur, f, sfx


def esc_dolencias():
    dur = 26.0
    PRI = [('Salud', 57.7), ('Educación', 44.7), ('Empleo', 38.2), ('Seguridad', 37.5), ('Pobreza', 33.6)]
    HOM = [784, 743, 759, 850, 745, 809, 876, 883, 819]
    pol = poligonos(1180, 560, 860)
    orden = sorted(pol, key=lambda n: LOC[n]['pobreza'])

    def f(t):
        im = lienzo((16, 18, 22)); dr = ImageDraw.Draw(im, 'RGBA')
        if t < 6.5:
            texto(dr, (160, 140), '¿QUÉ LE DUELE A BOGOTÁ?', F('impact', 84), (255, 255, 255), anchor='lm')
            texto(dr, (160, 215), 'Lo que la gente pide priorizar (% que lo menciona)', F('reg', 38), (200, 196, 190), anchor='lm')
            for i, (k, v) in enumerate(PRI):
                x = out_cubic(prog(t, 0.6 + i * 0.45, 1.3 + i * 0.45)); y = 330 + i * 130
                texto(dr, (160, y), k, F('bold', 48), (255, 255, 255), anchor='lm')
                dr.rounded_rectangle([520, y - 34, 520 + 1150 * v / 60 * x, y + 34], 12, fill=OXIDO if k == 'Seguridad' else (168, 159, 145))
                if x > 0.1:
                    texto(dr, (540 + 1150 * v / 60 * x, y), f'{v * x:.1f} %'.replace('.', ','), F('impact', 56), (255, 255, 255), anchor='lm')
            fuente_pie(dr, 'Bogotá Cómo Vamos, Encuesta de Percepción Ciudadana 2025')
            return viñeta(im)
        if t < 13.5:
            lt = t - 6.5
            texto(dr, (160, 120), 'HOMICIDIOS NO SON DE UN SOLO ALCALDE', F('impact', 76), (255, 255, 255), anchor='lm')
            texto(dr, (160, 190), 'Homicidios en Bogotá, enero a septiembre de cada año', F('reg', 38), (200, 196, 190), anchor='lm')
            x0, x1, y0, y1 = 220, 1700, 860, 330
            bandas = [('PEÑALOSA', 0, 1, (90, 90, 120)), ('LÓPEZ', 2, 5, (60, 110, 90)), ('GALÁN', 6, 8, (120, 90, 50))]
            for k, (nom, a, b, c) in enumerate(bandas):
                al = prog(lt, 0.4 + k * 0.6, 0.9 + k * 0.6)
                xa = x0 + (a - 0.45) * (x1 - x0) / 8; xb = x0 + (b + 0.45) * (x1 - x0) / 8
                dr.rectangle([xa, y1 - 20, xb, y0], fill=c + (int(45 * al),))
                texto(dr, ((xa + xb) / 2, y0 + 50), nom, F('impact', 46), (230, 226, 216))
            for i in range(9):
                texto(dr, (x0 + i * (x1 - x0) / 8, y0 + 100), str(2018 + i), F('reg', 30), (170, 166, 160))
            dr.line([(x0 - 40, y0), (x1 + 40, y0)], fill=(120, 116, 110), width=3)
            pr = prog(lt, 1.6, 4.6) * 8
            pts = [(x0 + i * (x1 - x0) / 8, y0 - (v / 1000) * (y0 - y1 + 120)) for i, v in enumerate(HOM)]
            k = int(pr)
            vis = pts[:k + 1] + ([(pts[k][0] + (pts[k + 1][0] - pts[k][0]) * (pr - k), pts[k][1] + (pts[k + 1][1] - pts[k][1]) * (pr - k))] if k < 8 else [])
            if len(vis) > 1:
                dr.line(vis, fill=OXIDO, width=10, joint='curve')
            for i, p in enumerate(pts[:k + 1]):
                dr.ellipse([p[0] - 12, p[1] - 12, p[0] + 12, p[1] + 12], fill=(255, 255, 255))
                texto(dr, (p[0], p[1] - 44), str(HOM[i]), F('bold', 32), (255, 255, 255))
            if lt > 5.0:
                texto(dr, (W / 2, 600), 'ENTRE 740 Y 880, CADA AÑO', F('impact', 64), ORO, borde=3)
            fuente_pie(dr, 'Secretaría Distrital de Seguridad, Convivencia y Justicia, homicidios ene-sep 2018-2026')
            return viñeta(im)
        if t < 18.0:
            lt = t - 13.5
            texto(dr, (W / 2, 160), 'LA EXTORSIÓN CASI SE TRIPLICÓ', F('impact', 90), (255, 255, 255))
            v = 589 + (1639 - 589) * out_cubic(prog(lt, 0.8, 2.6))
            dr.rounded_rectangle([560, 820 - 589 * 0.33, 860, 820], 14, fill=(150, 145, 136))
            dr.rounded_rectangle([1060, 820 - v * 0.33, 1360, 820], 14, fill=OXIDO)
            texto(dr, (710, 820 - 589 * 0.33 - 50), '589', F('impact', 70), (255, 255, 255)); texto(dr, (1210, 820 - v * 0.33 - 50), f'{int(v):,}'.replace(',', '.'), F('impact', 70), (255, 255, 255))
            texto(dr, (710, 870), '2018', F('bold', 44), (220, 216, 208)); texto(dr, (1210, 870), '2026', F('bold', 44), (220, 216, 208))
            if lt > 2.7:
                x = prog(lt, 2.7, 2.95)
                texto(dr, (1600, 380), 'x2,8', F('impact', int(150 * (2 - out_cubic(x)))), ORO, borde=5)
            fuente_pie(dr, 'Secretaría de Seguridad, casos de extorsión ene-sep')
            dx, dy = sacudida(t, [13.5 + 2.7], 24)
            return camara(viñeta(im), dx=dx, dy=dy)
        lt = t - 18.0
        texto(dr, (120, 120), 'POBREZA EN LA ZONA URBANA', F('impact', 70), (255, 255, 255), anchor='lm')
        texto(dr, (120, 185), 'DANE-SDP, Multipropósito 2025', F('reg', 34), (200, 196, 190), anchor='lm')
        for i, n in enumerate(orden):
            a = prog(lt, 0.3 + i * 0.12, 0.6 + i * 0.12)
            pv = LOC[n]['pobreza']; c = mezcla((60, 58, 56), mezcla((250, 210, 160), (150, 40, 20), min(1, pv / 38)), a)
            for p in pol[n]['polys']:
                dr.polygon(p, fill=c, outline=(16, 18, 22), width=2)
        if lt > 3.2:
            for j, (n, txt) in enumerate([('Usme', 'USME 37,5 %'), ('Ciudad Bolívar', 'C. BOLÍVAR 36,4 %'), ('Bosa', 'BOSA 32,7 %')]):
                a = out_back(prog(lt, 3.2 + j * 0.5, 3.6 + j * 0.5))
                cx, cy = pol[n]['c']
                capa = Image.new('RGBA', (560, 110), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                d2.rounded_rectangle([4, 4, 556, 106], 20, fill=(255, 255, 255, 235)); texto(d2, (280, 55), txt, F('impact', 62), (150, 40, 20))
                pegar(im, capa, 760, {'Bosa': 600, 'Ciudad Bolívar': 760, 'Usme': 920}[n], a)
        if lt > 6.3:
            x = prog(lt, 6.3, 6.55)
            texto(dr, (1580, 900), '0 NOTAS\nLO PONEN AQUÍ', F('impact', int(84 * (1.8 - 0.8 * out_cubic(x)))), ROJO, borde=5, color_borde=(255, 255, 255), espacio=6)
        dx, dy = sacudida(t, [18.0 + 6.35], 26)
        return camara(viñeta(im), 1.0 + 0.12 * in_out(prog(lt, 2.8, 4.0)), cx=1060, cy=820, dx=dx, dy=dy)
    sfx = [(0.6 + i * 0.45, 'pop_suave', 0.5) for i in range(5)]
    sfx += [(6.5, 'whoosh_cine', 0.5), (6.9, 'latido', 0.8), (8.1, 'latido', 0.6), (9.6, 'latido', 0.6), (11.5, 'impacto', 0.5)]
    sfx += [(13.5, 'whoosh_cine', 0.5), (14.3, 'riser', 0.5), (16.2, 'impacto_trailer', 0.8)]
    sfx += [(18.0, 'whoosh_cine', 0.5)] + [(18.0 + 3.2 + j * 0.5, 'pop', 0.6) for j in range(3)] + [(24.3, 'impacto', 1.0)]
    return dur, f, sfx


def esc_calendario():
    dur = 8.0
    MES = ['NOV 2026', 'DIC', 'ENE 2027', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT 2027']
    HITOS = [(3.6, '31 AGO 2027', 'Cierra la inscripción de cédulas'), (4.6, '30 JUN - 31 JUL 2027', 'Inscripción de candidatos'), (5.6, '31 OCT 2027', '¡ELECCIONES!')]

    def f(t):
        im = lienzo((24, 22, 20)); dr = ImageDraw.Draw(im, 'RGBA')
        i = min(11, int(prog(t, 0.2, 3.0) * 11.99))
        dr.rounded_rectangle([160, 230, 760, 830], 30, fill=PAPEL)
        dr.rounded_rectangle([160, 230, 760, 380], 30, fill=OXIDO); dr.rectangle([160, 330, 760, 380], fill=OXIDO)
        texto(dr, (460, 305), MES[i], F('impact', 84), (255, 255, 255))
        if i == 11:
            texto(dr, (460, 600), '31', F('impact', 280), TINTA)
        else:
            texto(dr, (460, 560), str(11 - i), F('impact', 240), TINTA); texto(dr, (460, 730), 'MESES PARA VOTAR' if i < 10 else 'MES PARA VOTAR', F('bold', 40), TINTA)
        for k, (t0, a, b) in enumerate(HITOS):
            if t > t0:
                x = out_back(prog(t, t0, t0 + 0.35))
                capa = Image.new('RGBA', (900, 170), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                d2.rounded_rectangle([4, 4, 896, 166], 22, fill=(255, 255, 255, 240) if k < 2 else ORO + (255,))
                texto(d2, (40, 60), a, F('impact', 60), OXIDO if k < 2 else TINTA, anchor='lm'); texto(d2, (40, 125), b, F('bold', 40), TINTA, anchor='lm')
                pegar(im, capa, 1330, 330 + k * 220, x)
        fuente_pie(dr, 'Registraduría Nacional, calendario electoral 2027 (Resolución 12338 de 2026)')
        return viñeta(im)
    sfx = [(0.2 + k * 0.25, 'pagina', 0.35) for k in range(11)] + [(0.2, 'tictac', 0.4)] + [(h[0], 'pop', 0.7) for h in HITOS] + [(5.6, 'nivel_completado', 0.5)]
    return dur, f, sfx


def esc_tarjeta():
    dur = 15.0
    STATS = [('EXPERIENCIA', 7, 2.2), ('VISIBILIDAD', 10, 3.1), ('RELATO DE CIUDAD', 1, 4.0), ('TERRITORIO', 0, 4.9)]
    DEB = [(7.0, 'Jun. 2026: la Procuraduría lo suspendió provisionalmente por presunta participación en política. Renunció a la UNGRD.'), (8.4, 'Oct. 2026: el Tribunal Superior de Bogotá le ordenó rectificar lo que dijo del exsenador Carlos A. Trujillo.')]

    def frente():
        c = Image.new('RGBA', (620, 860), (14, 24, 30, 255)); d = ImageDraw.Draw(c)
        d.rounded_rectangle([4, 4, 616, 856], 30, outline=NEON, width=8)
        c.alpha_composite(foto('carrillo.jpg', 520, 560).convert('RGBA'), (50, 50))
        texto(d, (310, 680), 'CARLOS CARRILLO', F('impact', 64), (255, 255, 255))
        texto(d, (310, 745), 'CLASE: EXDIRECTOR UNGRD', F('mono', 32), NEON)
        texto(d, (310, 795), 'NIVEL: PRECANDIDATO', F('mono', 32), ORO)
        return c

    def dorso():
        c = Image.new('RGBA', (620, 860), (30, 14, 40, 255)); d = ImageDraw.Draw(c)
        d.rounded_rectangle([4, 4, 616, 856], 30, outline=ORO, width=8)
        for k in range(0, 900, 40):
            d.line([(0, k), (620, k - 300)], fill=(60, 30, 80), width=10)
        texto(d, (310, 430), 'BOGOTÁ\n2027', F('impact', 110), ORO, espacio=10)
        return c
    FR, DO = frente(), dorso()

    def f(t):
        im = lienzo((10, 14, 20)); dr = ImageDraw.Draw(im, 'RGBA')
        for k in range(0, W, 80):
            dr.line([(k, 0), (k, H)], fill=(18, 26, 36), width=2)
        for k in range(0, H, 80):
            dr.line([(0, k), (W, k)], fill=(18, 26, 36), width=2)
        ang = (1 - out_cubic(prog(t, 0, 1.8))) * 3 * math.pi
        cs = math.cos(ang); c = FR if cs >= 0 else DO
        w = max(2, int(620 * abs(cs)))
        carta = c.resize((w, 860), Image.BICUBIC)
        pegar(im, carta, 470, 540 + 10 * math.sin(t * 2), 1.0)
        texto(dr, (1400, 150), 'TARJETA DE JUGADOR', F('impact', 70), NEON)
        for i, (nom, v, t0) in enumerate(STATS):
            y = 290 + i * 135; x = out_cubic(prog(t, t0, t0 + 0.7))
            texto(dr, (980, y), nom, F('mono', 40), (255, 255, 255), anchor='lm')
            for k in range(10):
                col = (NEON if v >= 5 else OXIDO) if k < round(v * x) else (40, 50, 60)
                dr.rectangle([980 + k * 78, y + 32, 980 + k * 78 + 66, y + 70], fill=col)
            texto(dr, (1790, y + 51), f'{round(v * x)}/10', F('impact', 48), (255, 255, 255), anchor='lm')
        if t > 6.6:
            a = prog(t, 6.6, 6.9)
            dr.rounded_rectangle([900, 800, 1890, 1030], 18, fill=(70, 10, 10, int(230 * a)), outline=ROJO, width=4)
            texto(dr, (930, 832), 'DEBUFFS (hechos publicados, no condenas)', F('impact', 38), ROJO, anchor='lm')
            for k, (t0, txt) in enumerate(DEB):
                if t > t0:
                    for m, linea in enumerate(__import__('textwrap').wrap(txt, 64)):
                        texto(dr, (930, 880 + k * 74 + m * 32), ('▼ ' if m == 0 else '   ') + linea, F('bold', 26), (255, 225, 225), anchor='lm')
        texto(dr, (980, 770), 'Barras: valoración del consultor, no un dato. Hechos: Semana, Infobae, Blu Radio.', F('reg', 24), (150, 156, 160), anchor='lm')
        flash = [t0 for t0, _ in DEB if t0 <= t < t0 + 0.15]
        if flash:
            comp(im, Image.new('RGBA', (W, H), (255, 0, 0, 60)))
        dx, dy = sacudida(t, [d[0] for d in DEB], 18)
        return camara(viñeta(im), dx=dx, dy=dy)
    sfx = [(0.0, 'whoosh_cine', 0.6), (0.4, 'mision_desbloqueada', 0.5)] + [(t0, 'nivel_completado' if v >= 5 else 'perder_vida', 0.55) for _, v, t0 in STATS] + [(d[0], 'perder_vida', 0.7) for d in DEB] + [(6.6, 'alarma_retro', 0.35)]
    return dur, f, sfx


def esc_mapa():
    dur = 19.0
    pol = poligonos(700, 560, 960)
    MIS = ['Usme', 'Ciudad Bolívar', 'Bosa']; ROJAS = [('Santa Fe', 51), ('Los Mártires', 45)]

    def f(t):
        # capa del mapa (se mueve con la cámara)
        im = lienzo((8, 12, 26)); dr = ImageDraw.Draw(im, 'RGBA')
        for k in range(0, W, 60):
            dr.line([(k, 0), (k, H)], fill=(14, 22, 44), width=1)
        for k in range(0, H, 60):
            dr.line([(0, k), (W, k)], fill=(14, 22, 44), width=1)
        ap = prog(t, 0, 1.5); puls = 0.5 + 0.5 * math.sin(t * 6)
        for n, d in pol.items():
            mis = n in MIS and t > 2.0; roja = any(n == r[0] for r in ROJAS) and t > 11.0
            fill = (int(150 + 90 * puls), 20, 30) if roja else (30, 120, 80) if mis else (22, 34, 60)
            for q in d['polys']:
                dr.polygon(q, fill=fill + (int(255 * ap),), outline=(255, 140, 140) if roja else (70, 200, 255, int(255 * ap)), width=2)
        if t < 1.5:
            y = H * prog(t, 0, 1.5); dr.rectangle([0, y - 4, W, y + 4], fill=(120, 230, 255))
        if t > 2.0:
            for k, n in enumerate(MIS):
                a = out_back(prog(t, 2.0 + k * 0.6, 2.4 + k * 0.6)); cx, cy = pol[n]['c']
                capa = Image.new('RGBA', (90, 90), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                d2.ellipse([5, 5, 85, 85], fill=ORO, outline=TINTA, width=4); texto(d2, (45, 45), '!', F('impact', 64), TINTA)
                pegar(im, capa, cx, cy - 50 + 8 * math.sin(t * 5 + k), a)
        z = 1.0 + 0.45 * in_out(prog(t, 2.2, 3.4)) * (1 - in_out(prog(t, 7.6, 8.4))) + 0.5 * in_out(prog(t, 10.6, 11.6)) * (1 - in_out(prog(t, 14.4, 15.0)))
        cyz = 790 if t < 9 else 560
        im = camara(viñeta(im), z, cx=640, cy=cyz)
        # interfaz fija (no se mueve con la cámara)
        dr = ImageDraw.Draw(im, 'RGBA')
        texto(dr, (1520, 90), 'MAPA DE MISIONES', F('impact', 72), NEON)
        texto(dr, (1520, 150), 'BOGOTÁ 2027', F('mono', 38), ORO)
        if 4.2 < t < 10.6:
            a = prog(t, 4.2, 4.6) * (1 - prog(t, 10.2, 10.6))
            dr.rounded_rectangle([1180, 250, 1860, 560], 22, fill=(10, 30, 24, int(235 * a)), outline=NEON + (int(255 * a),), width=4)
            texto(dr, (1210, 292), 'MISIÓN 1: EL SUR', F('impact', 56), NEON + (int(255 * a),), anchor='lm')
            for k, txt in enumerate(['Usme, Ciudad Bolívar y Bosa', 'Pobreza urbana: 32 % a 37,5 %', 'Izquierda en 2026: más del 56 %']):
                texto(dr, (1210, 370 + k * 58), txt, F('bold', 38), (230, 240, 236, int(255 * a)), anchor='lm')
        if 8.0 < t < 10.6:
            a = out_back(prog(t, 8.0, 8.4)) * (1 - prog(t, 10.2, 10.6))
            capa = Image.new('RGBA', (680, 140), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
            d2.rounded_rectangle([4, 4, 676, 136], 20, fill=ORO + (255,)); texto(d2, (340, 50), 'OJO: EN 2023 GANÓ GALÁN', F('impact', 50), TINTA); texto(d2, (340, 104), 'en 19 de las 20 localidades', F('bold', 32), TINTA)
            pegar(im, capa, 1520, 660, max(a, 0.01))
        if t > 11.0:
            for k, (n, v) in enumerate(ROJAS):
                a = out_back(prog(t, 11.0 + k * 0.7, 11.4 + k * 0.7))
                capa = Image.new('RGBA', (660, 110), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                d2.rounded_rectangle([4, 4, 656, 106], 18, fill=(120, 10, 10, 240), outline=(255, 120, 120), width=3)
                texto(d2, (330, 55), f'ZONA ROJA · {n.upper()} · {v}', F('impact', 44), (255, 255, 255))
                pegar(im, capa, 1520, 330 + k * 140, a)
            texto(dr, (1520, 560), 'homicidios por cada 100.000 habitantes', F('reg', 30), (230, 200, 200))
            texto(dr, (1520, 600), '(enero a septiembre de 2026)', F('reg', 30), (230, 200, 200))
        if t > 15.0:
            a = prog(t, 15.0, 15.4)
            dr.rectangle([0, 900, W, 1030], fill=(0, 0, 0, int(210 * a)))
            texto(dr, (W / 2, 965), 'REGLA DEL JUEGO: SER DEL PUEBLO, NO USAR AL PUEBLO', F('impact', 62), (255, 255, 255, int(255 * a)))
        else:
            fuente_pie(dr, 'DANE-SDP 2025 · Registraduría 2023 y 2026 · Secretaría de Seguridad 2026')
        return im
    sfx = [(0.0, 'glitch_texto', 0.5)] + [(2.0 + k * 0.6, 'mision_desbloqueada', 0.3) for k in range(3)] + [(8.0, 'boing', 0.3), (11.0, 'alarma_retro', 0.25), (11.7, 'alarma_retro', 0.2), (15.0, 'camara', 0.5)]
    return dur, f, sfx


def esc_cierre():
    dur = 11.0
    MIS = ['Hablar de Bogotá desde el agua y el riesgo', 'Estar en el sur', 'Cuidar la frase']
    r = random.Random(9); nube = [(r.uniform(-1, 1), r.uniform(-0.4, 0.4), r.uniform(0.6, 1.4)) for _ in range(140)]

    def f(t):
        im = lienzo((22, 20, 18)); dr = ImageDraw.Draw(im, 'RGBA')
        if t < 4.6:
            texto(dr, (W / 2, 170), 'MISIONES', F('impact', 90), NEON)
            for i, m in enumerate(MIS):
                y = 380 + i * 170; a = prog(t, 0.4 + i * 0.9, 0.7 + i * 0.9)
                dr.rounded_rectangle([360, y - 60, 420, y], 10, outline=(255, 255, 255), width=5)
                if t > 0.8 + i * 0.9:
                    dr.line([(370, y - 30), (388, y - 10), (420, y - 64)], fill=NEON, width=12)
                texto(dr, (470, y - 30), m, F('bold', 58), (255, 255, 255, int(255 * a)), anchor='lm')
            return viñeta(im)
        lt = t - 4.6
        x = prog(lt, 0, 0.4)
        texto(dr, (W / 2, 420), 'YA ES VISIBLE.', F('impact', int(150 * (1.6 - 0.6 * out_cubic(x)))), (255, 255, 255))
        if lt > 0.8:
            x2 = prog(lt, 0.8, 1.2)
            texto(dr, (W / 2, 620), 'FALTA QUE SEA DE BOGOTÁ.', F('impact', int(130 * (1.6 - 0.6 * out_cubic(x2)))), ORO)
        if lt > 3.4:
            ex = out_back(prog(lt, 3.4, 3.8)); ox = W + 300 - ex * 620
            dr.rounded_rectangle([ox - 70, 640, ox + 70, 1000], 40, fill=(210, 30, 30)); dr.rectangle([ox - 30, 590, ox + 30, 645], fill=(40, 40, 40))
            dr.line([(ox - 30, 600), (ox - 150, 560), (ox - 210, 600)], fill=(30, 30, 30), width=22)
            texto(dr, (ox, 820), 'EXTINTOR', F('impact', 30), (255, 255, 255))
            if lt > 3.9:
                sp = prog(lt, 3.9, 5.5)
                capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dn = ImageDraw.Draw(capa)
                for a, b, s in nube:
                    px = ox - 230 - sp * 900 * (0.5 + abs(a)); py = 600 + b * 600 * sp
                    rad = 40 * s * (0.5 + sp)
                    dn.ellipse([px - rad, py - rad, px + rad, py + rad], fill=(245, 245, 245, int(170 * (1 - sp * 0.5))))
                comp(im, capa.filter(ImageFilter.GaussianBlur(18)))
        dx, dy = sacudida(t, [4.6 + 0.35, 4.6 + 1.15], 20)
        return camara(viñeta(im), dx=dx, dy=dy)
    sfx = [(0.8 + i * 0.9, 'pop_suave', 0.3) for i in range(3)] + [(4.6, 'impacto', 0.5), (5.4, 'impacto_trailer', 0.5), (8.0, 'whoosh_rapido', 0.5), (8.5, 'extintor_spray', 0.9), (9.6, 'risa', 0.7)]
    return dur, f, sfx


def esc_creditos():
    dur = 14.0
    L = ['FUENTES', '', 'Corpus propio: 1.093 notas de 85 medios (Google News y API de medios), 12 nov 2025 - 11 nov 2026',
         'SDIS, VIII Censo de Habitantes de Calle 2024 · TransMilenio S.A., datos abiertos',
         'McLuhan (1964) · Culkin (1967) · Lippmann (1922) · Wolf (1985) · Castells (2009) · Bourdieu (1979)',
         'Juego: We Become What We Behold, Nicky Case (CC0) · gameplay: Ludophiles (YouTube)',
         'Propiedad de medios: Media Ownership Monitor · CRC (2022) · García y Zambrano (2025)',
         'Bogotá Cómo Vamos, Encuesta de Percepción Ciudadana 2025', 'DANE-SDP, Encuesta Multipropósito 2025 (cuadros 216A y 216B)',
         'Registraduría Nacional: escrutinios Alcaldía 2023 y Presidencia 2026; calendario electoral 2027 (Res. 12338 de 2026)',
         'Secretaría Distrital de Seguridad, Convivencia y Justicia: delitos por localidad 2018-2026', 'Google Trends, consultado el 11 nov 2026',
         'La Silla Vacía · Vorágine · Semana · Infobae · Caracol Radio · El Tiempo · Me Vale (Eva Rey)', '',
         'Fotos: Wikimedia Commons (licencias libres) · Sonido y música: Mixkit (licencia gratuita)',
         '"Lightless Dawn", Kevin MacLeod (incompetech.com), licencia Creative Commons: By Attribution 4.0', 'Clips de base visual: Google Flow', '',
         'Diego Umbarila · Sociología de la Información y los Medios', 'Docente: Sebastián Peña Pérez · Noviembre de 2026']

    def f(t):
        im = lienzo((14, 13, 12)); dr = ImageDraw.Draw(im, 'RGBA')
        y0 = H + 40 - t * 150
        for i, s in enumerate(L):
            if not s:
                continue
            texto(dr, (W / 2, y0 + i * 70), s, F('impact', 64) if s == 'FUENTES' else F('reg', 34), ORO if s == 'FUENTES' else (230, 226, 218))
        return im
    return dur, f, []


FV = os.path.join(V, 'fotos')
AUTORES = {
    'bourdieu': ('bourdieu.jpg', 'PIERRE BOURDIEU', 'sociólogo francés',
                 ['Capital simbólico: el prestigio que hace que un apellido valga antes de que su dueño haga algo.', 'Capital social: la red de relaciones y apoyos que abre puertas.']),
    'wolf': ('periodicos.jpg', 'MAURO WOLF', 'sociólogo italiano de la comunicación',
             ['Las redacciones escogen qué es noticia con criterios de noticiabilidad: el conflicto y los nombres conocidos pesan más que una propuesta.']),
    'lippmann': ('lippmann.jpg', 'WALTER LIPPMANN', 'periodista y escritor estadounidense',
                 ['No actuamos sobre el mundo real, sino sobre la imagen del mundo que nos llega por los medios: el pseudo-entorno.']),
    'castells': ('castells.jpg', 'MANUEL CASTELLS', 'sociólogo español',
                 ['El poder se juega en la mente de la gente, y los medios deciden qué entra en ella: lo que no aparece, casi no existe.']),
}


def esc_autor(clave):
    dur = 6.0
    img_n, nombre, rol, ideas = AUTORES[clave]

    def f(t):
        im = lienzo((24, 22, 30)); dr = ImageDraw.Draw(im, 'RGBA')
        for k in range(0, W, 3):
            pass
        ent = out_back(prog(t, 0, 0.45))
        if img_n:
            ft = Image.open(os.path.join(FV, img_n)).convert('RGB'); ft = ImageOps.fit(ft, (520, 640), Image.LANCZOS, centering=(0.5, 0.3))
            ft = (ImageOps.grayscale(ft).convert('RGB') if img_n != 'periodicos.jpg' else ft); ft = ImageOps.expand(ft, 8, ORO)
        else:
            ft = Image.new('RGB', (536, 656), (50, 46, 60)); d2 = ImageDraw.Draw(ft); d2.rectangle([0, 0, 535, 655], outline=ORO, width=8)
            texto(d2, (268, 328), ''.join(w[0] for w in nombre.split()), F('impact', 220), ORO)
        pegar(im, ft, 430, 540, ent, angulo=-3 * (1 - ent))
        a = prog(t, 0.4, 0.8)
        texto(dr, (800, 250), 'COMO DECÍA EL ' + rol.upper().split(' ')[0] if rol.startswith('soci') else 'COMO DECÍA EL ' + rol.split(' ')[0].upper(), F('bold', 36), (200, 196, 210, int(255 * a)), anchor='lm')
        texto(dr, (800, 320), nombre, F('impact', 96), ORO + (int(255 * a),), anchor='lm')
        texto(dr, (800, 395), rol, F('reg', 40), (230, 226, 236, int(255 * a)), anchor='lm')
        y = 500
        for k, idea in enumerate(ideas):
            b = prog(t, 1.0 + k * 1.2, 1.4 + k * 1.2)
            for m, linea in enumerate(__import__('textwrap').wrap(idea, 42)):
                texto(dr, (800, y), ('“' if m == 0 else ' ') + linea + ('”' if m == len(__import__('textwrap').wrap(idea, 42)) - 1 else ''), F('serif', 46), (255, 255, 255, int(255 * b)), anchor='lm')
                y += 64
            y += 28
        texto(dr, (800, 1010), 'La idea del autor, explicada en palabras sencillas (no es una cita textual).', F('reg', 24), (160, 156, 170), anchor='lm')
        return viñeta(im)
    return dur, f, [(0.0, 'pagina', 0.5), (0.05, 'whoosh_cine', 0.4), (1.0, 'pop_suave', 0.4)]


def esc_movilidad():
    dur = 24.0
    TZ = json.load(open(os.path.join(V, 'consulta_trazados_troncales.json'), encoding='utf-8'))['features']
    EST = json.load(open(os.path.join(V, 'consulta_estaciones_troncales.json'), encoding='utf-8'))['features']
    COLT = {'A': (40, 80, 170), 'B': (120, 185, 60), 'C': (247, 175, 0), 'D': (140, 95, 180), 'E': (160, 115, 60), 'F': (225, 45, 45), 'G': (40, 165, 225),
            'H': (245, 125, 30), 'J': (205, 175, 95), 'K': (215, 185, 135), 'L': (95, 165, 120), 'M': (0, 175, 175)}
    NOMBRE = {'A': 'CARACAS', 'B': 'AUTOPISTA NORTE', 'C': 'SUBA', 'D': 'CALLE 80', 'E': 'NQS', 'F': 'AMÉRICAS', 'G': 'NQS SUR', 'H': 'CARACAS SUR',
              'K': 'CALLE 26', 'L': 'CARRERA 10', 'M': 'CARRERA 7'}
    pol = poligonos(640, 560, 940)
    lon0, lat1, k = -74.225, 4.84, 940 / (4.84 - 4.465)
    ox = 640 - (-73.99 - lon0) * k / 2; oy = 560 - 940 / 2

    def px(lo, la):
        return ox + (lo - lon0) * k, oy + (lat1 - la) * k
    lineas = []
    for f_ in TZ:
        letra = f_['attributes']['letra_trazado_troncal'].strip()[0]
        for path in f_['geometry']['paths']:
            lineas.append((letra, [px(a, b) for a, b in path]))
    puntos = {}
    for letra, ps in lineas:
        puntos.setdefault(letra, []).extend(ps)
    ETQ = {}
    for letra, ps in puntos.items():
        if letra in NOMBRE:
            ps2 = sorted(ps, key=lambda q: (q[1], q[0])); ETQ[letra] = ps2[len(ps2) // 2]
    AJ = {'A': (70, 0), 'B': (90, -40), 'C': (-70, -20), 'D': (-80, 10), 'E': (-50, 0), 'F': (-60, 25), 'G': (-70, 0), 'H': (75, 30), 'K': (-60, -25), 'L': (80, 0), 'M': (90, 0)}
    estaciones = [px(e['attributes']['longitud_estacion'], e['attributes']['latitud_estacion']) for e in EST if e['attributes'].get('longitud_estacion')]
    UNA_HORA = {a['Localidad']: a['Más de 1 hora al trabajo %'] for a in json.load(open(os.path.join(D, 'localidades.json'), encoding='utf-8'))}
    fotos = [Image.open(os.path.join(FV, n)).convert('RGB') for n in ('trancon_caracas.jpg', 'transmilenio_interior.jpg', 'trancon_autonorte.jpg')]
    hosp = Image.open(os.path.join(FV, 'hospital_san_jose.jpg')).convert('RGB')

    def parcial(ps, fr):
        n = max(2, int(len(ps) * fr)); return ps[:n]

    def f(t):
        if t < 13.0:
            im = lienzo((12, 14, 20)); dr = ImageDraw.Draw(im, 'RGBA')
            modo_hora = t > 7.0
            for n, d in pol.items():
                c = mezcla((34, 38, 52), (200, 70, 40), min(1, UNA_HORA.get(n, 10) / 38) * prog(t, 7.0, 8.0)) if modo_hora else (30, 34, 48)
                for q in d['polys']:
                    dr.polygon(q, fill=c, outline=(70, 80, 100), width=1)
            fr = in_out(prog(t, 0.6, 3.2)); colapso = prog(t, 3.6, 4.2) if not modo_hora else 0
            puls = 0.5 + 0.5 * math.sin(t * 9)
            for letra, ps in lineas:
                if len(ps) < 2:
                    continue
                c = COLT.get(letra, (200, 200, 200))
                if colapso:
                    c = mezcla(c, (255, int(40 + 60 * puls), 30), colapso)
                if modo_hora:
                    c = mezcla(c, (90, 90, 100), 0.6)
                dr.line(parcial(ps, fr), fill=c, width=9 if not modo_hora else 5, joint='curve')
            if fr > 0.95:
                for x, y in estaciones:
                    dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 255, 255, 220 if not modo_hora else 90), outline=(20, 20, 20))
            if 1.5 < t and not modo_hora:
                al = int(255 * prog(t, 1.5, 2.2))
                for letra, (x, y) in ETQ.items():
                    ax_, ay_ = AJ.get(letra, (0, 0))
                    texto(dr, (x + ax_, y + ay_), NOMBRE[letra], F('impact', 30), (255, 255, 255, al), borde=3, color_borde=mezcla(COLT[letra], (0, 0, 0), 0.4))
            texto(dr, (1450, 110), 'BOGOTÁ COLAPSADA', F('impact', 80), (255, 255, 255))
            if not modo_hora:
                texto(dr, (1450, 190), 'Troncales de TransMilenio', F('bold', 40), (220, 220, 230))
                if t > 3.8:
                    b = out_back(prog(t, 3.8, 4.2))
                    capa = Image.new('RGBA', (760, 260), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                    d2.rounded_rectangle([4, 4, 756, 256], 24, fill=(160, 30, 20, 240))
                    texto(d2, (380, 95), '7.ª CIUDAD', F('impact', 110), (255, 255, 255)); texto(d2, (380, 200), 'con peor tráfico del mundo (2025)', F('bold', 40), (255, 235, 225))
                    pegar(im, capa, 1450, 440, b)
                    texto(dr, (1450, 620), 'Ranking: TomTom Traffic Index 2025', F('reg', 30), (200, 200, 210))
                fuente_pie(dr, 'Trazados y estaciones: TransMilenio S.A., datos abiertos · TomTom Traffic Index 2025, citado por Vanguardia (25 ene 2026)')
            else:
                texto(dr, (1450, 300), 'MÁS DE 1 HORA', F('impact', 90), (255, 255, 255)); texto(dr, (1450, 380), 'para llegar al trabajo', F('bold', 44), (230, 226, 216))
                for m, (n, v) in enumerate([('Usme', 38.2), ('Bosa', 31.8), ('Ciudad Bolívar', 29.6), ('Teusaquillo', 4.0)]):
                    b = out_back(prog(t, 8.2 + m * 0.6, 8.6 + m * 0.6))
                    capa = Image.new('RGBA', (700, 100), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                    d2.rounded_rectangle([4, 4, 696, 96], 18, fill=(255, 255, 255, 235) if n != 'Teusaquillo' else (80, 160, 120, 235))
                    texto(d2, (30, 50), n.upper(), F('impact', 52), TINTA, anchor='lm'); texto(d2, (670, 50), f'{v:.1f} %'.replace('.', ','), F('impact', 60), (170, 40, 20) if n != 'Teusaquillo' else TINTA, anchor='rm')
                    pegar(im, capa, 1450, 500 + m * 120, b)
                fuente_pie(dr, 'DANE-SDP, Encuesta Multipropósito 2025: ocupados que tardan más de una hora en llegar al trabajo')
            dx, dy = sacudida(t, [4.1], 14)
            return camara(viñeta(im), dx=dx, dy=dy)
        if t < 17.5:
            lt = t - 13.0; i = min(2, int(lt / 1.5)); ll = lt - i * 1.5
            im = lienzo(); im.paste(ImageOps.fit(fotos[i], (W, H), Image.LANCZOS), (0, 0)); dr = ImageDraw.Draw(im, 'RGBA')
            dr.rectangle([0, 860, W, 1000], fill=(0, 0, 0, 170))
            texto(dr, (W / 2, 930), ['TRONCALES QUE COLAPSAN', 'TRANSMILENIO A REVENTAR', 'HORAS PERDIDAS CADA DÍA'][i], F('impact', 88), (255, 255, 255))
            fuente_pie(dr, 'Fotos: Wikimedia Commons (Mariordo, CC BY-SA 4.0; otras licencias libres)')
            return camara(viñeta(im), 1.0 + 0.08 * ll, dx=sacudida(t, [13.0 + i * 1.5], 10)[0])
        lt = t - 17.5
        im = lienzo(); im.paste(ImageEnhance.Brightness(ImageOps.fit(hosp, (W, H), Image.LANCZOS)).enhance(0.35), (0, 0)); dr = ImageDraw.Draw(im, 'RGBA')
        texto(dr, (W / 2, 150), 'Y LA SALUD, EN CUIDADOS INTENSIVOS', F('impact', 84), (255, 255, 255), borde=4)
        for m, (big, small) in enumerate([('26 BILLONES', 'de deuda de la Nueva EPS (abril de 2026)'), ('1.943', 'casos de personas sin atención en Bogotá (Personería, ene-sep 2025)')]):
            b = out_back(prog(lt, 0.6 + m * 1.6, 1.0 + m * 1.6))
            capa = Image.new('RGBA', (1500, 230), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
            d2.rounded_rectangle([4, 4, 1496, 226], 26, fill=(255, 255, 255, 235))
            texto(d2, (750, 90), big, F('impact', 110), (190, 30, 30)); texto(d2, (750, 185), small, F('bold', 42), TINTA)
            pegar(im, capa, W / 2, 400 + m * 290, b)
        fuente_pie(dr, 'Infobae (15 abr 2026), con datos de la Supersalud · Personería de Bogotá, citada por Semana (nov 2025) · Foto: Hospital San José, CC BY-SA 3.0')
        dx, dy = sacudida(t, [17.5 + 0.65, 17.5 + 2.25], 12)
        return camara(viñeta(im), 1.0 + 0.02 * lt, dx=dx, dy=dy)
    sfx = [(0.6, 'riser', 0.3), (3.6, 'alarma_retro', 0.3), (4.1, 'impacto', 0.6), (7.0, 'whoosh_cine', 0.4)] + [(8.2 + m * 0.6, 'pop', 0.45) for m in range(4)]
    sfx += [(13.0 + i * 1.5, 'whoosh_rapido', 0.45) for i in range(3)] + [(17.5, 'latido', 0.6), (18.1, 'impacto', 0.6), (19.7, 'impacto', 0.6)]
    return dur, f, sfx


def cifras_overlay(dur, tiempos=(3.0, 10.0, 17.0)):
    """Capa transparente con las cifras de la escena 1, para poner encima de los clips de noticieros."""
    CIF = [('26 %', 'aprueba la gestión del alcalde', 'Bogotá Cómo Vamos 2025', ORO),
           ('62 %', 'se siente inseguro: récord desde 2008', 'Bogotá Cómo Vamos 2025', ORO),
           ('589 → 1.639', 'casos de extorsión (ene-sep, 2018 vs. 2026)', 'Secretaría de Seguridad', OXIDO)]

    def f(t):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        texto(dr, (W / 2, 90), 'BOGOTÁ, 2026', F('impact', 64), (255, 255, 255), borde=4)
        for t0, (big, small, src, col) in zip(tiempos, CIF):
            if t <= t0 or t > t0 + 4.2:
                continue
            x = prog(t, t0, t0 + 0.35); sc = 2.4 - 1.4 * out_cubic(x); sale = prog(t, t0 + 3.6, t0 + 4.0)
            capa = Image.new('RGBA', (1600, 440), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
            d2.rounded_rectangle([60, 20, 1540, 420], 30, fill=(0, 0, 0, 150))
            texto(d2, (800, 170), big, F('impact', 200), col, borde=6)
            texto(d2, (800, 340), small.upper(), F('bold', 52), (255, 255, 255), borde=3)
            pegar(im, capa, W / 2 - sale * 1600, H / 2 + 60, sc, alfa=min(1, x * 3))
            texto(dr, (W - 40, H - 34), 'Fuente: ' + src, F('reg', 26), (235, 230, 220), anchor='rm', borde=2)
        return im
    sfx = [(t0, 'whoosh_cine', 0.7) for t0 in tiempos] + [(t0 + 0.3, 'impacto', 0.9) for t0 in tiempos]
    return f, sfx


def esc_apellido():
    """Escena 02 sin cámara: el apellido Galán, del padre al hijo, y el 26 % de hoy."""
    dur = 16.0
    padre = ImageOps.grayscale(Image.open(os.path.join(FV, 'lcgalan_busto.jpg')).convert('RGB')).convert('RGB')
    padre = ImageOps.fit(padre, (560, 760), Image.LANCZOS, centering=(0.5, 0.15))
    hijo = ImageOps.fit(Image.open(os.path.join(FV, 'cfgalan.jpg')).convert('RGB'), (560, 760), Image.LANCZOS, centering=(0.5, 0.25))

    def persona(d, cx, cy, col):
        d.ellipse([cx - 38, cy - 120, cx + 38, cy - 44], fill=col); d.rounded_rectangle([cx - 62, cy - 36, cx + 62, cy + 110], 40, fill=col)

    def f(t):
        im = lienzo((16, 14, 12)); dr = ImageDraw.Draw(im, 'RGBA')
        if t < 5.5:
            pegar(im, ImageOps.expand(padre, 8, (200, 190, 170)), 520, 540, out_back(prog(t, 0.2, 0.7)))
            a = prog(t, 0.8, 1.3)
            texto(dr, (900, 330), 'LUIS CARLOS GALÁN', F('impact', 90), (230, 222, 205, int(255 * a)), anchor='lm')
            texto(dr, (900, 410), 'Liberal. Asesinado en 1989 por enfrentar a la mafia.', F('reg', 38), (200, 194, 180, int(255 * a)), anchor='lm')
            if t > 2.4:
                x = prog(t, 2.4, 2.65)
                texto(dr, (900, 600), 'EL APELLIDO', F('impact', int(150 * (1.4 - 0.4 * out_cubic(x)))), ORO, borde=4, anchor='lm')
            fuente_pie(dr, 'Foto: busto de Luis Carlos Galán, Wikimedia Commons (CC BY 4.0)')
            dx, dy = sacudida(t, [2.45], 12)
            return camara(viñeta(im), dx=dx, dy=dy)
        if t < 10.5:
            lt = t - 5.5
            pegar(im, ImageOps.expand(hijo, 8, ORO), 520, 540, out_back(prog(lt, 0.0, 0.5)))
            a = prog(lt, 0.5, 1.0)
            texto(dr, (900, 300), 'CARLOS FERNANDO GALÁN', F('impact', 84), (255, 255, 255, int(255 * a)), anchor='lm')
            texto(dr, (900, 380), 'Alcalde de Bogotá desde 2024.', F('reg', 40), (220, 214, 204, int(255 * a)), anchor='lm')
            if lt > 1.6:
                x = prog(lt, 1.6, 1.9)
                texto(dr, (900, 570), '2023: 49 %', F('impact', int(170 * (1.4 - 0.4 * out_cubic(x)))), ORO, borde=4, anchor='lm')
                texto(dr, (900, 700), 'Ganó en 19 de las 20 localidades.', F('bold', 44), (240, 236, 228), anchor='lm')
            fuente_pie(dr, 'Registraduría, Alcaldía 2023 · Foto: Presidencia de Colombia, dominio público')
            dx, dy = sacudida(t, [5.5 + 1.65], 12)
            return camara(viñeta(im), dx=dx, dy=dy)
        lt = t - 10.5
        texto(dr, (W / 2, 190), 'HOY', F('impact', 110), (255, 255, 255))
        for k in range(4):
            on = k == 0 and lt > 1.2
            persona(dr, 600 + k * 240, 560, ORO if on else (70, 66, 60))
        if lt > 1.4:
            texto(dr, (W / 2, 820), 'SOLO 1 DE CADA 4 APRUEBA SU GESTIÓN (26 %)', F('impact', 76), ORO, borde=3)
        fuente_pie(dr, 'Bogotá Cómo Vamos, Encuesta de Percepción Ciudadana 2025')
        return viñeta(im)
    sfx = [(0.2, 'whoosh_cine', 0.5), (2.4, 'impacto', 0.8), (5.5, 'whoosh_cine', 0.5), (7.1, 'impacto_trailer', 0.7), (10.5, 'pagina', 0.4), (11.7, 'trombon_triste', 0.18)]
    return dur, f, sfx

def dibujar_tv(dr, cx, cy, s, pantalla=(40, 60, 80), a=255):
    w, h = 300 * s, 220 * s
    dr.line([(cx - 20 * s, cy - h / 2), (cx - 80 * s, cy - h / 2 - 90 * s)], fill=PAPEL + (a,), width=int(8 * s))
    dr.line([(cx + 20 * s, cy - h / 2), (cx + 80 * s, cy - h / 2 - 90 * s)], fill=PAPEL + (a,), width=int(8 * s))
    dr.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], int(28 * s), fill=(60, 56, 66, a), outline=PAPEL + (a,), width=int(8 * s))
    dr.rounded_rectangle([cx - w / 2 + 24 * s, cy - h / 2 + 24 * s, cx + w / 2 - 24 * s, cy + h / 2 - 24 * s], int(14 * s), fill=pantalla + (a,))
    return (cx - w / 2 + 24 * s, cy - h / 2 + 24 * s, cx + w / 2 - 24 * s, cy + h / 2 - 24 * s)


def dibujar_cel(dr, cx, cy, s, pantalla=(40, 60, 80), a=255):
    w, h = 150 * s, 290 * s
    dr.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], int(26 * s), fill=(60, 56, 66, a), outline=PAPEL + (a,), width=int(7 * s))
    dr.rounded_rectangle([cx - w / 2 + 14 * s, cy - h / 2 + 34 * s, cx + w / 2 - 14 * s, cy + h / 2 - 34 * s], int(8 * s), fill=pantalla + (a,))
    dr.ellipse([cx - 9 * s, cy + h / 2 - 26 * s, cx + 9 * s, cy + h / 2 - 8 * s], outline=PAPEL + (a,), width=int(3 * s))
    return (cx - w / 2 + 14 * s, cy - h / 2 + 34 * s, cx + w / 2 - 14 * s, cy + h / 2 - 34 * s)


def esc_mcluhan():
    """Audio 13: McLuhan, 'el medio es el mensaje' (Understanding Media, 1964)."""
    dur = 24.0
    T1, T2, T3 = 7.0, 14.0, 19.5

    def f(t):
        im = lienzo((24, 22, 30)); dr = ImageDraw.Draw(im, 'RGBA')
        if t < T1:  # tarjeta del autor
            a = prog(t, 0.4, 0.8); e = out_back(prog(t, 0, 0.5))
            ft = Image.open(os.path.join(FV, 'mcluhan.jpg')).convert('RGB'); ft = ImageOps.fit(ft, (520, 640), Image.LANCZOS, centering=(0.5, 0.3))
            ft = ImageOps.expand(ImageOps.grayscale(ft).convert('RGB'), 8, ORO)
            pegar(im, ft, 430, 540, e, angulo=-3 * (1 - e))
            texto(dr, (800, 250), 'COMO DECÍA EL TEÓRICO', F('bold', 36), (200, 196, 210, int(255 * a)), anchor='lm')
            texto(dr, (800, 320), 'MARSHALL McLUHAN', F('impact', 96), ORO + (int(255 * a),), anchor='lm')
            texto(dr, (800, 395), 'teórico canadiense de la comunicación', F('reg', 40), (230, 226, 236, int(255 * a)), anchor='lm')
            b = prog(t, 1.4, 1.9)
            texto(dr, (800, 520), 'Estudió cómo los medios (la imprenta,', F('serif', 44), (255, 255, 255, int(255 * b)), anchor='lm')
            texto(dr, (800, 584), 'la radio, la televisión) cambian', F('serif', 44), (255, 255, 255, int(255 * b)), anchor='lm')
            texto(dr, (800, 648), 'la forma en que pensamos.', F('serif', 44), (255, 255, 255, int(255 * b)), anchor='lm')
        elif t < T2:  # la frase
            u = t - T1
            frase = 'EL MEDIO ES EL MENSAJE'
            n = int(len(frase) * prog(u, 0.6, 2.4))
            z = 1 + 0.04 * u / (T2 - T1)
            capa = Image.new('RGBA', (W, 400), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
            texto(d2, (W / 2, 200), '“' + frase[:n] + ('”' if n == len(frase) else ''), F('impact', 150), ORO, borde=5)
            pegar(im, capa, W / 2, 470, z)
            a = prog(u, 2.6, 3.2)
            texto(dr, (W / 2, 690), 'Marshall McLuhan · Understanding Media (1964)', F('bold', 44), (230, 226, 236, int(255 * a)))
            texto(dr, (W / 2, 760), '(en inglés: “The medium is the message”)', F('reg', 34), (170, 166, 180, int(255 * a)))
        elif t < T3:  # qué vs por dónde
            u = t - T2
            a1 = out_back(prog(u, 0.2, 0.6)); a2 = out_back(prog(u, 1.6, 2.0)); brillo = prog(u, 2.6, 3.2)
            for k, (titulo, sub, cx, a) in enumerate([('QUÉ SE DICE', 'el contenido', 560, a1), ('POR DÓNDE NOS LLEGA', 'el medio', 1360, a2)]):
                capa = Image.new('RGBA', (700, 380), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa, 'RGBA')
                ok = k == 1
                d2.rounded_rectangle([6, 6, 694, 374], 30, fill=((60, 44, 10) if ok else (40, 38, 48)) + (240,), outline=(ORO if ok else (120, 116, 130)) + (255,), width=6 if ok else 3)
                texto(d2, (350, 150), titulo, F('impact', 66 if ok else 60), ORO if ok else (200, 196, 210))
                texto(d2, (350, 240), sub, F('reg', 42), (230, 226, 236))
                pegar(im, capa, cx, 470, a * (1 + 0.06 * brillo * ok))
            texto(dr, (960, 470), '+', F('impact', 110), (200, 196, 210, int(255 * a2)))
            texto(dr, (W / 2, 800), 'El medio cambia la forma en que vemos el mundo', F('bold', 50), (255, 255, 255, int(255 * brillo)))
        else:  # hoy: pantallas
            u = t - T3
            a1 = out_back(prog(u, 0.1, 0.5)); a2 = out_back(prog(u, 0.6, 1.0))
            capa = Image.new('RGBA', (640, 560), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa, 'RGBA')
            x0, y0, x1, y1 = dibujar_tv(d2, 320, 320, 1.7, (150, 20, 24))
            texto(d2, ((x0 + x1) / 2, (y0 + y1) / 2 - 20), 'ÚLTIMA', F('impact', 60), PAPEL); texto(d2, ((x0 + x1) / 2, (y0 + y1) / 2 + 40), 'HORA', F('impact', 60), PAPEL)
            pegar(im, capa, 620, 470, a1)
            capa = Image.new('RGBA', (360, 560), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa, 'RGBA')
            x0, y0, x1, y1 = dibujar_cel(d2, 180, 280, 1.7, (24, 30, 44))
            for k in range(4):
                yy = y0 + 20 + k * 92; d2.rounded_rectangle([x0 + 14, yy, x1 - 14, yy + 74], 10, fill=(60, 70, 96))
                d2.text((x0 + 26, yy + 37), ['#polémica', '#pelea', '#escándalo', '#viral'][k], font=F('bold', 26), fill=(255, 220, 120), anchor='lm')
            pegar(im, capa, 1300, 470, a2, angulo=6 * math.sin(u * 1.5))
            texto(dr, (620, 820), 'el noticiero', F('bold', 44), (230, 226, 236, int(255 * prog(u, 0.4, 0.8))))
            texto(dr, (1300, 820), 'el celular', F('bold', 44), (230, 226, 236, int(255 * prog(u, 0.9, 1.3))))
            texto(dr, (W / 2, 140), 'HOY, EL MEDIO ES UNA PANTALLA', F('impact', 84), ORO + (int(255 * prog(u, 1.2, 1.7)),), borde=3)
        return viñeta(im)
    sfx = [(0.0, 'pagina', 0.5), (0.05, 'whoosh_cine', 0.4), (T1, 'whoosh_cine', 0.4), (T1 + 2.4, 'impacto', 0.35), (T2 + 0.2, 'pop_suave', 0.35), (T2 + 1.6, 'pop_suave', 0.35), (T3, 'whoosh_rapido', 0.4)]
    return dur, f, sfx


def esc_propuesta():
    """Audio 15: el ciclo del conflicto y la propuesta del consultor en tres misiones."""
    dur = 64.0
    TC, TD, TP, TM, TF = 3.0, 9.6, 23.0, (23.6, 29.4, 44.8), 52.0
    MIS = [('MONTARSE EN LA OLA', 'Entrar al tema que ya está en la pantalla'),
           ('ROMPER EL GUION', 'La posición que nadie espera, aunque sea contra su lado'),
           ('PELEAR CONTRA PROBLEMAS, NO PERSONAS', 'Contra las EPS que no atienden, el trancón y el robo, con datos')]
    CIC = ['PELEA', 'CLICS', 'MÁS CÁMARA', 'MÁS PELEA']

    def f(t):
        im = lienzo((10, 14, 28)); dr = ImageDraw.Draw(im, 'RGBA')
        for k in range(0, W, 60):
            dr.line([(k, 0), (k, H)], fill=(16, 24, 46), width=1)
        for k in range(0, H, 60):
            dr.line([(0, k), (W, k)], fill=(16, 24, 46), width=1)
        if t < TC:  # pregunta
            a = out_back(prog(t, 0.1, 0.5))
            capa = Image.new('RGBA', (1600, 300), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
            texto(d2, (800, 110), '¿Y ESTO QUÉ TIENE QUE VER', F('impact', 96), PAPEL, borde=3)
            texto(d2, (800, 220), 'CON CARRILLO?', F('impact', 110), ORO, borde=3)
            pegar(im, capa, W / 2, H / 2, a)
        elif t >= TD and t < TP:  # cambiar el discurso
            u = t - TD; L = TP - TD
            if u < 3.0:
                a = out_back(prog(u, 0.1, 0.5))
                capa = Image.new('RGBA', (1500, 300), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                texto(d2, (750, 90), '¿CÓMO SE LE GANA A ESO?', F('impact', 96), PAPEL, borde=3)
                texto(d2, (750, 210), 'no portándose bonito: usando la regla de los medios', F('bold', 52), (200, 210, 230))
                pegar(im, capa, W / 2, H / 2, a)
            else:
                v = u - 3.0
                texto(dr, (W / 2, 110), 'ESCOGER LA PELEA', F('impact', 90), ORO + (int(255 * prog(v, 0, 0.5)),), borde=3)
                cajas = [(330, 'LOS MEDIOS', 'el conflicto es lo que vende', (150, 20, 26), (255, 130, 130), 0.6),
                         (960, 'PORTARSE BONITO', 'no funciona: nadie cubre al amable', (60, 60, 80), (170, 170, 200), 0.26 * L),
                         (1590, 'ESCOGER SUS PELEAS', 'usar la regla de los medios a su favor', (20, 90, 60), NEON, 0.50 * L)]
                for k, (cx, tit, sub, fondo, borde_, t0) in enumerate(cajas):
                    b = out_back(prog(v, t0, t0 + 0.5))
                    if b <= 0.01:
                        continue
                    capa = Image.new('RGBA', (520, 420), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                    d2.rounded_rectangle([4, 4, 516, 416], 28, fill=fondo + (235,), outline=borde_, width=5)
                    texto(d2, (260, 80), tit, F('impact', 54), PAPEL)
                    for m, ln in enumerate(__import__('textwrap').wrap(sub, 20)):
                        texto(d2, (260, 170 + m * 52), ln, F('bold', 40), PAPEL)
                    pegar(im, capa, cx, 520, b)
                    if k > 0:
                        x0 = cajas[k - 1][0] + 270; x1 = cx - 280
                        dr.line([(x0, 520), (x1, 520)], fill=PAPEL + (int(255 * b),), width=8)
                        dr.polygon([(x1 + 22, 520), (x1, 506), (x1, 534)], fill=PAPEL + (int(255 * b),))
                c = 0
                if c > 0:
                    dr.rectangle([0, 860, W, 1000], fill=(0, 0, 0, int(210 * c)))
                    texto(dr, (W / 2, 905), 'Si los medios escogen el conflicto,', F('bold', 46), (255, 255, 255, int(255 * c)))
                    texto(dr, (W / 2, 962), 'ÉL ESCOGE CUÁL CONFLICTO LE CONVIENE', F('impact', 56), ORO + (int(255 * c),))
        elif t < TD:  # el ciclo
            u = t - TC; cx, cy, R = 700, 560, 300
            texto(dr, (cx, 130), 'EL CICLO DEL CONFLICTO', F('impact', 72), (255, 110, 110, int(255 * prog(u, 0, 0.5))))
            giro = u * 0.6
            for k, nom in enumerate(CIC):
                ang = -math.pi / 2 + k * math.pi / 2
                a = out_back(prog(u, 0.4 + k * 0.7, 0.8 + k * 0.7))
                x, y = cx + R * math.cos(ang), cy + R * math.sin(ang)
                capa = Image.new('RGBA', (360, 130), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                act = int(giro) % 4 == k and u > 3.4
                d2.rounded_rectangle([4, 4, 356, 126], 24, fill=(150, 20, 26) if act else (60, 20, 30), outline=(255, 130, 130), width=4)
                texto(d2, (180, 65), nom, F('impact', 52), PAPEL)
                pegar(im, capa, x, y, a * (1.08 if act else 1))
            if u > 3.2:
                for k in range(4):  # flechas en arco
                    a0 = -math.pi / 2 + k * math.pi / 2 + 0.42; a1 = a0 + math.pi / 2 - 0.84
                    pts = [(cx + R * math.cos(a0 + (a1 - a0) * s / 12), cy + R * math.sin(a0 + (a1 - a0) * s / 12)) for s in range(13)]
                    dr.line(pts, fill=(255, 130, 130, 200), width=6)
                    ex, ey = pts[-1]; dx, dy = ex - pts[-2][0], ey - pts[-2][1]; m = math.hypot(dx, dy) or 1; dx, dy = dx / m, dy / m
                    dr.polygon([(ex + dx * 22, ey + dy * 22), (ex - dy * 14, ey + dx * 14), (ex + dy * 14, ey - dx * 14)], fill=(255, 130, 130, 220))
            a = prog(u, 1.8, 2.4)
            dr.rounded_rectangle([1180, 330, 1860, 790], 26, fill=(30, 12, 18, int(230 * a)), outline=(255, 130, 130, int(255 * a)), width=3)
            for k, s in enumerate(['Hoy los medios lo muestran', 'sobre todo por sus peleas', 'y sus polémicas.', '', 'Entre más pelea, más sale…', '…pero no por sus propuestas.']):
                b = prog(u, 2.2 + k * 0.45, 2.6 + k * 0.45) if s else 0
                texto(dr, (1215, 390 + k * 66), s, F('bold', 40), (255, 236, 236, int(255 * b)), anchor='lm')
        else:  # propuesta
            u = t - TP
            a = prog(u, 0, 0.5)
            texto(dr, (W / 2, 110), 'PROPUESTA DEL CONSULTOR', F('impact', 86), NEON + (int(255 * a),))
            texto(dr, (W / 2, 180), 'usar la teoría a su favor', F('mono', 40), ORO + (int(255 * a),))
            for k, (tit, sub) in enumerate(MIS):
                t0 = TM[k] - TP
                b = out_back(prog(u, t0, t0 + 0.45))
                hecho = u > t0 + 1.2
                capa = Image.new('RGBA', (1500, 170), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                d2.rounded_rectangle([4, 4, 1496, 166], 24, fill=(10, 34, 26) if hecho else (16, 26, 44), outline=NEON if hecho else (90, 120, 170), width=4)
                d2.rounded_rectangle([34, 40, 124, 130], 14, outline=NEON if hecho else (150, 170, 200), width=6)
                if hecho:
                    c = prog(u, t0 + 1.2, t0 + 1.5)
                    pts = [(50, 86), (74, 112), (112, 56)]
                    d2.line(pts[:2] if c < 0.5 else pts, fill=NEON, width=12)
                d2.text((160, 58), f'MISIÓN {k + 1}: {tit}', font=F('impact', 56), fill=PAPEL, anchor='lm')
                d2.text((160, 120), sub, font=F('bold', 36), fill=(200, 220, 214), anchor='lm')
                if b > 0.01:
                    pegar(im, capa, W / 2, 330 + k * 200, b)
            if TF < t < TF + 7.0:
                c = prog(t, TF, TF + 0.6) * (1 - prog(t, TF + 6.6, TF + 7.0))
                dr.rectangle([0, 900, W, 1040], fill=(0, 0, 0, int(225 * c)))
                texto(dr, (W / 2, 948), 'Si los medios escogen el conflicto y la sorpresa,', F('bold', 44), (255, 255, 255, int(255 * c)))
                texto(dr, (W / 2, 1006), 'ÉL ESCOGE CUÁL CONFLICTO LE CONVIENE', F('impact', 54), ORO + (int(255 * c),))
            elif t >= TF + 7.0:
                c = prog(t, TF + 7.0, TF + 7.6)
                dr.rectangle([0, 900, W, 1040], fill=(0, 0, 0, int(225 * c)))
                texto(dr, (W / 2, 948), 'LA IMAGEN QUE MUESTRAN LOS MEDIOS', F('impact', 56), (255, 255, 255, int(255 * c)))
                texto(dr, (W / 2, 1006), 'termina siendo la persona que la gente ve', F('bold', 42), ORO + (int(255 * c),))
        return viñeta(im)
    sfx = [(0.0, 'whoosh_cine', 0.45), (TC, 'glitch_texto', 0.35)] + [(TC + 0.4 + k * 0.7, 'pop_suave', 0.3) for k in range(4)] + \
          [(TD, 'whoosh_cine', 0.4), (TD + 3.0, 'pagina', 0.4), (TD + 3.6, 'pop_suave', 0.3), (TD + 3 + 0.26 * (TP - TD), 'pop_suave', 0.3), (TD + 3 + 0.50 * (TP - TD), 'pop_suave', 0.3)] + \
          [(TP, 'whoosh_cine', 0.45)] + [(m, 'pop_suave', 0.35) for m in TM] + [(m + 1.2, 'mision_desbloqueada', 0.22) for m in TM] + [(TF, 'camara', 0.4)]
    return dur, f, sfx


def esc_zonas():
    """Audio 16: Bogotá no es solo el sur. Habitantes de calle (Censo SDIS 2024) y hurto a personas (Secretaría de Seguridad 2025)."""
    dur = 60.0
    T1, T2, T3, T4 = 9.0, 29.0, 43.0, 49.5
    HC = {'Los Mártires': (1750, 1302), 'Santa Fe': (1313, 1236), 'Kennedy': (682, 1005), 'Puente Aranda': (472, 625), 'Rafael Uribe Uribe': (285, 599),
          'Engativá': (316, 589), 'Suba': (217, 528), 'Antonio Nariño': (333, 453), 'Ciudad Bolívar': (292, 431)}
    HURTO = ['Suba', 'Engativá', 'Kennedy']
    ZONAS = [('EL SUR', 'pobreza', ['Usme', 'Ciudad Bolívar', 'Bosa'], (30, 140, 80), (-230, 40)),
             ('EL CENTRO', 'habitantes de calle', ['Los Mártires', 'Santa Fe', 'La Candelaria'], (190, 30, 40), (330, 0)),
             ('NORTE Y OCCIDENTE', 'robo', ['Suba', 'Engativá', 'Kennedy'], (40, 110, 210), (-220, -110))]
    pol = poligonos(560, 560, 960)

    def color_hc(v):
        x = min(1.0, (v - 400) / 950)
        return mezcla((250, 210, 120), (120, 10, 20), max(0.0, x))

    def f(t):
        im = lienzo((14, 14, 22)); dr = ImageDraw.Draw(im, 'RGBA')
        if t < T1:
            a = out_back(prog(t, 0.1, 0.5))
            capa = Image.new('RGBA', (1600, 320), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
            texto(d2, (800, 100), 'OJO: BOGOTÁ NO ES SOLO EL SUR', F('impact', 100), ORO, borde=3)
            texto(d2, (800, 230), 'cada zona tiene su propio dolor', F('bold', 56), PAPEL)
            pegar(im, capa, W / 2, H / 2, a)
            return viñeta(im)
        ap = prog(t, T1, T1 + 1.2)
        for n, d in pol.items():
            if t >= T4:
                k_ = next((i for i, z in enumerate(ZONAS) if n in z[2]), None)
                on = k_ is not None and t > T4 + 0.6 + k_ * 0.9
                fill = mezcla(ZONAS[k_][3], (255, 255, 255), 0.12 * (0.5 + 0.5 * math.sin(t * 4))) if on else (40, 42, 56)
                out = (255, 255, 255) if on else (90, 92, 110)
            elif t < T3:
                v = HC.get(n, (0, 0))[1]
                fill = color_hc(v) if v and t > T1 + 1.0 else (40, 42, 56)
                out = (255, 230, 200)
            else:
                hot = n in HURTO
                fill = (40, 110, 200) if hot else (40, 42, 56)
                out = (150, 200, 255) if hot else (90, 92, 110)
            for q in d['polys']:
                dr.polygon(q, fill=fill + (int(255 * ap),), outline=out + (int(200 * ap),), width=2)
        # nombre de todas las localidades, para que ninguna quede "sin importancia"
        if t > T1 + 1.0:
            corto = {'Rafael Uribe Uribe': 'R. Uribe', 'La Candelaria': 'Cand.', 'Antonio Nariño': 'A. Nariño', 'Ciudad Bolívar': 'C. Bolívar', 'Barrios Unidos': 'B. Unidos',
                     'Puente Aranda': 'P. Aranda', 'San Cristóbal': 'S. Cristóbal', 'Los Mártires': 'Mártires'}
            callout = ['Los Mártires', 'Santa Fe', 'Kennedy'] if t < T3 else []
            an = int(230 * prog(t, T1 + 1.0, T1 + 1.6))
            for n, d in pol.items():
                if n in callout:
                    continue
                cx, cy = d['c']; tam = 15 if n in ('La Candelaria', 'Antonio Nariño', 'Los Mártires', 'Santa Fe') else 19
                texto(dr, (cx, cy), corto.get(n, n), F('bold', tam), (255, 255, 255, an), borde=3, color_borde=(10, 10, 14))
        if T1 + 1.0 < t < T3:
            for n in ['Los Mártires', 'Santa Fe', 'Kennedy']:
                cx, cy = pol[n]['c']; b = prog(t, T1 + 1.5, T1 + 2.0)
                v = HC[n][1]
                capa = Image.new('RGBA', (300, 70), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                d2.rounded_rectangle([2, 2, 298, 68], 14, fill=(20, 18, 26, 230)); texto(d2, (150, 35), f'{n.upper()} · {v:,}'.replace(',', '.'), F('bold', 26), PAPEL)
                dx, dy = {'Los Mártires': (260, -150), 'Santa Fe': (270, 40), 'Kennedy': (-200, -60)}[n]
                dr.line([(cx, cy), (cx + dx, cy + dy)], fill=(255, 255, 255, int(200 * b)), width=3)
                pegar(im, capa, cx + dx, cy + dy, b)
        # panel derecho
        x0 = 1080
        if T1 < t < T2:
            u = t - T1
            texto(dr, (x0, 150), 'HABITANTES DE CALLE', F('impact', 72), ORO + (int(255 * prog(u, 0, 0.5)),), anchor='lm')
            n_ = int(10478 * out_cubic(prog(u, 0.8, 2.6)))
            texto(dr, (x0, 290), f'{n_:,}'.replace(',', '.'), F('impact', 150), PAPEL + (int(255 * prog(u, 0.8, 1.0)),), anchor='lm')
            texto(dr, (x0, 390), 'personas viviendo en la calle en Bogotá (2024)', F('bold', 38), (220, 220, 230, int(255 * prog(u, 1.2, 1.6))), anchor='lm')
            b = prog(u, 3.6, 4.2)
            dr.rounded_rectangle([x0, 460, x0 + 760, 600], 20, fill=(120, 10, 20, int(220 * b)))
            texto(dr, (x0 + 380, 530), '+10 % frente a 2017 (9.538)', F('impact', 56), (255, 255, 255, int(255 * b)))
            c = prog(u, 6.0, 6.6)
            texto(dr, (x0, 680), 'Donde más hay: el centro', F('bold', 44), (255, 255, 255, int(255 * c)), anchor='lm')
            texto(dr, (x0, 740), 'Los Mártires, Santa Fe, La Candelaria', F('reg', 38), (220, 220, 230, int(255 * c)), anchor='lm')
            g = prog(u, 8.0, 8.6)
            dr.rounded_rectangle([x0, 820, x0 + 34, 854], 6, fill=(40, 42, 56, int(255 * g)), outline=(180, 180, 190, int(255 * g)), width=2)
            texto(dr, (x0 + 50, 837), 'En gris: también hay, pero menos casos', F('bold', 32), (230, 230, 236, int(255 * g)), anchor='lm')
            texto(dr, (x0 + 50, 882), '(no están entre las localidades con más en el censo)', F('reg', 28), (190, 190, 200, int(255 * g)), anchor='lm')
        elif T2 <= t < T3:
            u = t - T2
            texto(dr, (x0, 150), 'YA NO ESTÁN SOLO EN EL CENTRO', F('impact', 62), ORO + (int(255 * prog(u, 0, 0.5)),), anchor='lm')
            texto(dr, (x0, 215), 'personas encuestadas en el censo, por localidad', F('bold', 34), (220, 220, 230), anchor='lm')
            for k, n in enumerate(['Kennedy', 'Engativá', 'Suba']):
                a17, a24 = HC[n]; y = 330 + k * 190; b = out_cubic(prog(u, 0.8 + k * 0.9, 2.0 + k * 0.9))
                texto(dr, (x0, y), n.upper(), F('impact', 52), PAPEL, anchor='lm')
                esc = 700 / 1100
                dr.rounded_rectangle([x0, y + 40, x0 + a17 * esc, y + 80], 8, fill=(80, 90, 120))
                texto(dr, (x0 + a17 * esc + 14, y + 60), f'{a17}', F('bold', 30), (200, 200, 220), anchor='lm')
                w24 = a24 * esc * b
                dr.rounded_rectangle([x0, y + 92, x0 + max(8, w24), y + 140], 8, fill=(200, 40, 40))
                if b > 0.95:
                    texto(dr, (x0 + w24 + 14, y + 116), f'{a24:,}'.replace(',', '.'), F('impact', 40), PAPEL, anchor='lm')
            texto(dr, (x0, 920), 'gris: 2017 · rojo: 2024 · (encuestas del censo SDIS)', F('reg', 30), (190, 190, 200), anchor='lm')
        elif T3 <= t < T4:
            u = t - T3
            texto(dr, (x0, 150), 'NORTE Y OCCIDENTE: EL ROBO', F('impact', 66), (150, 200, 255, int(255 * prog(u, 0, 0.5))), anchor='lm')
            for k, n in enumerate(HURTO):
                b = out_back(prog(u, 1.0 + k * 0.6, 1.4 + k * 0.6))
                capa = Image.new('RGBA', (700, 110), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                d2.rounded_rectangle([4, 4, 696, 106], 20, fill=(20, 50, 100, 240), outline=(150, 200, 255), width=3)
                texto(d2, (350, 55), f'{k + 1}. {n.upper()}', F('impact', 56), PAPEL)
                pegar(im, capa, x0 + 360, 300 + k * 140, b)
            c = prog(u, 4.0, 4.6)
            texto(dr, (x0, 760), 'las localidades con más', F('bold', 44), (255, 255, 255, int(255 * c)), anchor='lm')
            texto(dr, (x0, 815), 'denuncias de hurto a personas', F('bold', 44), (255, 255, 255, int(255 * c)), anchor='lm')
            texto(dr, (x0, 885), 'En toda Bogotá: 86.376 (enero a septiembre de 2026)', F('reg', 36), (200, 220, 255, int(255 * c)), anchor='lm')
            texto(dr, (x0, 950), 'En gris: también hay robos, pero menos denuncias que en estas tres', F('reg', 28), (190, 190, 200, int(255 * c)), anchor='lm')
        if t >= T4:
            u = t - T4
            texto(dr, (x0, 140), 'UNA BOGOTÁ, VARIOS DOLORES', F('impact', 70), ORO + (int(255 * prog(u, 0, 0.5)),), anchor='lm')
            for k, (zona, dolor, locs, col, off) in enumerate(ZONAS):
                b = out_back(prog(u, 0.6 + k * 0.9, 1.0 + k * 0.9))
                if b <= 0.01:
                    continue
                # etiqueta sobre el mapa
                cs = [pol[n]['c'] for n in locs if n in pol]
                cx = sum(c[0] for c in cs) / len(cs); cy = sum(c[1] for c in cs) / len(cs)
                capa = Image.new('RGBA', (360, 90), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                d2.rounded_rectangle([3, 3, 357, 87], 16, fill=col + (245,), outline=PAPEL, width=3)
                texto(d2, (180, 45), dolor.upper(), F('impact', 36), PAPEL)
                lx, ly = max(200, min(880, cx + off[0])), cy + off[1]
                dr.line([(cx, cy), (lx, ly)], fill=(255, 255, 255, 220), width=3)
                dr.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(255, 255, 255))
                pegar(im, capa, lx, ly, b)
                # fila en el panel
                capa = Image.new('RGBA', (760, 190), (0, 0, 0, 0)); d2 = ImageDraw.Draw(capa)
                d2.rounded_rectangle([4, 4, 756, 186], 22, fill=col + (235,), outline=PAPEL, width=3)
                d2.text((30, 60), zona, font=F('impact', 52), fill=PAPEL, anchor='lm')
                d2.text((30, 125), dolor + ' · ' + ', '.join(locs), font=F('bold', 25), fill=PAPEL, anchor='lm')
                pegar(im, capa, x0 + 380, 330 + k * 220, b)
            c = prog(u, 3.4, 4.0)
            texto(dr, (x0, 925), 'Las demás localidades también tienen problemas:', F('bold', 30), (220, 220, 230, int(255 * c)), anchor='lm')
            texto(dr, (x0, 965), 'aquí se ve dónde pesa más cada uno.', F('bold', 30), (220, 220, 230, int(255 * c)), anchor='lm')
            c = prog(u, 4.0, 4.6)
            texto(dr, (x0, 1025), 'CADA LOCALIDAD, SU PROPIA MISIÓN', F('impact', 50), (255, 255, 255, int(255 * c)), anchor='lm')
        if t < T3:
            fuente_pie(dr, 'Fuente: SDIS, Censo de Habitantes de Calle 2024 (presentación de la Secretaría; bogota.gov.co, 14-feb-2025)')
        elif t < T4:
            fuente_pie(dr, 'Fuente: Secretaría Distrital de Seguridad, hurto a personas por localidad, enero a septiembre de 2026 (corte 30-sep-2026)')
        return viñeta(im)
    sfx = [(0.0, 'whoosh_cine', 0.45), (0.2, 'impacto', 0.3), (T1, 'glitch_texto', 0.35), (T1 + 0.8, 'pop_suave', 0.3), (T1 + 3.6, 'impacto', 0.3), (T2, 'whoosh_rapido', 0.4)] + \
          [(T2 + 0.8 + k * 0.9, 'pop_suave', 0.3) for k in range(3)] + [(T3, 'whoosh_cine', 0.4)] + [(T3 + 1.0 + k * 0.6, 'pop_suave', 0.3) for k in range(3)] + \
          [(T4, 'whoosh_cine', 0.4)] + [(T4 + 1.0 + k * 0.7, 'pop_suave', 0.3) for k in range(3)]
    return dur, f, sfx


def esc_metodo():
    """Audio 17: cómo se hizo el análisis y para qué le sirve a una campaña. Los cambios de parte salen
    de la grabación (alinear_voz) si ya existe; si no, de las sílabas del guion."""
    import textwrap
    par = open(os.path.join(D, 'guion_17.txt'), encoding='utf-8').read().strip().splitlines()
    vz = os.path.join(V, 'voz', '17.wav')
    if os.path.exists(vz):
        import alinear_voz
        from moviepy import AudioFileClip
        dv = AudioFileClip(vz).duration
        cj = os.path.join(V, 'voz', '17_cortes.json')  # cortes sacados de la transcripción con tiempos + pausas reales
        cortes = json.load(open(cj, encoding='utf-8')) if os.path.exists(cj) else alinear_voz.alinear(vz, par)
        T = [0.0] + [0.3 + c for c in cortes]; dur = dv + 1.1
    else:
        import alinear_voz
        s = [alinear_voz.silabas(p) for p in par]; dv = sum(s) * 0.24
        T = [0.0]
        for x in s[:-1]:
            T.append(T[-1] + x * 0.24)
        T = [0.0] + [0.3 + t for t in T[1:]]; dur = dv + 1.1
    T.append(dur)
    PASOS = ['RECOLECTAR', 'CRUZAR', 'ANALIZAR', 'MOSTRAR']
    COL = [(47, 111, 143), (30, 140, 80), (190, 120, 20), (170, 40, 60)]
    mini = {n: Image.open(os.path.join(FV, n)).convert('RGB') for n in
            ['mini_dossier.png', 'mini_fichas.png', 'mini_presentacion.png', 'mini_mapa_zonas.png', 'mini_dolencias.png', 'mini_juego.png', 'mini_gaza.png', 'mini_lula.png']}

    def barra(dr, activo, a):
        for k, p in enumerate(PASOS):
            x = 300 + k * 440; on = k == activo
            dr.rounded_rectangle([x - 190, 40, x + 190, 120], 18, fill=(COL[k] if on else (44, 42, 52)) + (int(240 * a),), outline=(PAPEL if on else (90, 88, 100)) + (int(255 * a),), width=3 if on else 2)
            texto(dr, (x, 80), f'{k + 1}. {p}', F('impact', 40), (PAPEL if on else (150, 146, 160)) + (int(255 * a),))
            if k < 3:
                texto(dr, (x + 220, 80), '›', F('impact', 50), (120, 116, 130, int(255 * a)))

    def tarjeta(w, h, col, titulo, lineas, tam=34):
        c = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
        d2.rounded_rectangle([3, 3, w - 3, h - 3], 22, fill=col + (240,), outline=PAPEL, width=3)
        d2.text((28, 48), titulo, font=F('impact', 46), fill=PAPEL, anchor='lm')
        for m, l in enumerate(lineas):
            d2.text((28, 104 + m * (tam + 10)), l, font=F('bold', tam), fill=PAPEL, anchor='lm')
        return c

    def f(t):
        im = lienzo((18, 17, 24)); dr = ImageDraw.Draw(im, 'RGBA')
        k = next((i for i in range(7) if t < T[i + 1]), 6); u = t - T[k]; L = T[k + 1] - T[k]
        if k == 0:
            a = prog(u, 0.2, 0.8)
            texto(dr, (W / 2, 330), 'DETRÁS DE ESTE VIDEO', F('impact', 120), ORO + (int(255 * a),), borde=4)
            texto(dr, (W / 2, 450), 'cómo se hizo, y por qué sirve para cualquier campaña', F('bold', 50), (235, 231, 240, int(255 * prog(u, 0.8, 1.4))))
            for j, p in enumerate(PASOS):
                b = out_back(prog(u, 1.6 + j * 0.5, 2.0 + j * 0.5))
                c = Image.new('RGBA', (380, 120), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
                d2.rounded_rectangle([3, 3, 377, 117], 22, fill=COL[j] + (240,), outline=PAPEL, width=3)
                d2.text((190, 60), f'{j + 1}. {p}', font=F('impact', 48), fill=PAPEL, anchor='mm')
                pegar(im, c, 300 + j * 440, 700, b)
        elif k == 1:  # recolectar
            barra(dr, 0, 1)
            n = int(1093 * out_cubic(prog(u, 0.4, 3.5)))
            texto(dr, (560, 360), f'{n:,}'.replace(',', '.'), F('impact', 230), PAPEL, borde=4)
            texto(dr, (560, 510), 'notas sobre Carrillo', F('bold', 54), ORO)
            texto(dr, (560, 580), '85 medios · 12 nov 2025 a 11 nov 2026', F('reg', 38), (220, 216, 228))
            # terminal
            c = Image.new('RGBA', (760, 420), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
            d2.rounded_rectangle([0, 0, 759, 419], 18, fill=(8, 10, 12, 245), outline=(70, 80, 90), width=2)
            for j in range(3):
                d2.ellipse([20 + j * 30, 18, 38 + j * 30, 36], fill=[(235, 90, 80), (240, 190, 60), (90, 200, 100)][j])
            m = max(1, n)
            for j in range(8):
                q = m - 7 + j
                if q >= 1:
                    d2.text((24, 70 + j * 42), f'> nota {q:>4} de 1093 ... guardada', font=F('mono', 28), fill=NEON if j == 7 else (120, 200, 150))
            pegar(im, c, 1420, 430, out_back(prog(u, 0.0, 0.5)))
            t0 = 0.55 * L
            if u > t0 - 0.6:
                texto(dr, (W / 2, 690), 'Y NO ES LA PRIMERA VEZ:', F('impact', 50), (200, 196, 210, int(255 * prog(u, t0 - 0.6, t0))))
            b = out_back(prog(u, t0, t0 + 0.4))
            pegar(im, tarjeta(1100, 230, (40, 60, 90), 'LULA · ELECCIONES EN BRASIL', ['1.367 notas de 7 fuentes de Brasil, Reino Unido y Colombia',
                                                                                   'CNN Brasil · Poder360 · Brasil de Fato · The Guardian · BBC · El Colombiano'], 30), W / 2, 880, b)
        elif k == 2:  # cruzar
            barra(dr, 1, 1)
            c = Image.new('RGBA', (520, 200), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
            d2.rounded_rectangle([3, 3, 517, 197], 26, fill=(60, 44, 10, 245), outline=ORO, width=5)
            d2.text((260, 70), 'LO QUE DICEN', font=F('impact', 56), fill=ORO, anchor='mm'); d2.text((260, 140), 'LOS MEDIOS', font=F('impact', 56), fill=ORO, anchor='mm')
            pegar(im, c, W / 2, 560, out_back(prog(u, 0, 0.5)))
            FU = [('REGISTRADURÍA', 'votos 2023 y 2026', (380, 300)), ('DANE', 'Multipropósito 2025', (1540, 300)),
                  ('SECRETARÍA DE SEGURIDAD', 'delitos 2018-2026', (330, 820)), ('SDIS', 'censo habitantes de calle', (1590, 820)),
                  ('BOGOTÁ CÓMO VAMOS', 'percepción 2025', (W / 2, 900)), ('GOOGLE TRENDS', 'qué busca la gente', (W / 2, 220))]
            for j, (n_, s_, (x, y)) in enumerate(FU):
                b = prog(u, 0.35 * L + j * 0.11 * L, 0.35 * L + j * 0.11 * L + 0.4)
                if b <= 0:
                    continue
                dr.line([(W / 2, 560), (x, y)], fill=(57, 255, 136, int(150 * b)), width=4)
                c = Image.new('RGBA', (520, 130), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
                d2.rounded_rectangle([3, 3, 517, 127], 20, fill=(20, 70, 46, 245), outline=PAPEL, width=3)
                d2.text((260, 48), n_, font=F('impact', 40), fill=PAPEL, anchor='mm'); d2.text((260, 95), s_, font=F('bold', 28), fill=(210, 240, 220), anchor='mm')
                pegar(im, c, x, y, out_back(b))
            c = Image.new('RGBA', (520, 200), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
            d2.rounded_rectangle([3, 3, 517, 197], 26, fill=(60, 44, 10, 255), outline=ORO, width=5)
            d2.text((260, 70), 'LO QUE DICEN', font=F('impact', 56), fill=ORO, anchor='mm'); d2.text((260, 140), 'LOS MEDIOS', font=F('impact', 56), fill=ORO, anchor='mm')
            pegar(im, c, W / 2, 560, out_back(prog(u, 0, 0.5)))
            texto(dr, (W / 2, 1030), 'Fuentes oficiales y abiertas, citadas en los créditos', F('reg', 28), (170, 166, 180, int(255 * prog(u, 2, 2.5))))
        elif k == 3:  # analizar
            barra(dr, 2, 1)
            c = Image.new('RGBA', (760, 520), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
            d2.rounded_rectangle([0, 0, 759, 519], 20, fill=(244, 240, 232, 255))
            d2.text((40, 50), 'NOTA DEL CORPUS', font=F('bold', 28), fill=(140, 130, 120), anchor='lm')
            d2.rectangle([40, 90, 700, 130], fill=(60, 56, 52)); d2.rectangle([40, 145, 560, 185], fill=(60, 56, 52))
            for j in range(6):
                d2.rectangle([40, 230 + j * 44, 720 - (j % 3) * 70, 250 + j * 44], fill=(190, 184, 176))
            pegar(im, c, 560, 600, out_back(prog(u, 0, 0.5)), angulo=-2)
            ET = [('TEMA', 'seguridad, salud, movilidad…'), ('TONO', 'a favor · neutro · en contra'), ('¿VOZ PROPIA?', 'habla él o solo lo nombran'), ('¿LOCALIDAD?', 'si la nota toca un barrio')]
            for j, (a_, b_) in enumerate(ET):
                b = out_back(prog(u, 0.15 * L + j * 0.09 * L, 0.15 * L + j * 0.09 * L + 0.4))
                pegar(im, tarjeta(720, 150, COL[2] if j % 2 == 0 else (150, 90, 20), a_, [b_], 32), 1400, 300 + j * 175, b)
            if u > 0.6 * L:
                b = out_back(prog(u, 0.6 * L, 0.6 * L + 0.5))
                c = Image.new('RGBA', (820, 130), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
                d2.rounded_rectangle([3, 3, 817, 127], 24, fill=(20, 20, 26, 245), outline=NEON, width=4)
                d2.text((410, 46), 'LA MÁQUINA VA RÁPIDO…', font=F('impact', 42), fill=NEON, anchor='mm')
                d2.text((410, 96), '…y 216 notas leídas a mano para comprobar', font=F('bold', 32), fill=PAPEL, anchor='mm')
                pegar(im, c, 560, 960, b)
        elif k == 4:  # de quién son los medios
            barra(dr, 2, 1)
            texto(dr, (W / 2, 190), '¿DE QUIÉN SON LOS MEDIOS QUE HABLAN DE CARRILLO?', F('impact', 62), ORO + (int(255 * prog(u, 0, 0.5)),), borde=3)
            RED = [('PRISA (ESPAÑA)', (61, 138, 90), [('Caracol Radio', 102)]), ('GILINSKI', (91, 74, 122), [('Semana', 94)]),
                   ('SARMIENTO ANGULO (GRUPO AVAL)', (140, 109, 31), [('El Tiempo', 20), ('Citytv (Bogotá)', 0)]),
                   ('SANTO DOMINGO (VALOREM)', (47, 111, 143), [('Blu Radio', 39), ('El Espectador', 34), ('Noticias Caracol', 6)]),
                   ('ARDILA LÜLLE (OAL)', (181, 71, 47), [('La FM', 24)])]
            fase2 = 0.42 * L
            if u < fase2:
                y = 270; j = 0
                for g, (dueno, col, medios) in enumerate(RED):
                    b = out_cubic(prog(u, 0.135 * L + g * 0.052 * L, 0.135 * L + g * 0.052 * L + 0.5))
                    if b <= 0.01:
                        y += 70 * len(medios) + 26; continue
                    yc = y + 35 * (len(medios) - 1)
                    dr.rounded_rectangle([140, yc - 30, 640, yc + 30], 14, fill=col + (int(240 * b),))
                    texto(dr, (390, yc), dueno, F('impact', 30), PAPEL + (int(255 * b),))
                    for m, (med, n) in enumerate(medios):
                        yy = y + m * 70
                        dr.line([(640, yc), (760, yy)], fill=col + (int(220 * b),), width=3)
                        dr.rounded_rectangle([760, yy - 28, 1100, yy + 28], 12, fill=(30, 30, 40, int(240 * b)), outline=col + (int(255 * b),), width=3)
                        texto(dr, (780, yy), med, F('bold', 30), PAPEL + (int(255 * b),), anchor='lm')
                        w = n * 5.5 * b
                        if n:
                            dr.rounded_rectangle([1130, yy - 20, 1130 + w, yy + 20], 8, fill=col + (int(255 * b),))
                        texto(dr, (1145 + w, yy), f'{n} notas' if n else 'ninguna nota', F('bold', 28), ((240, 236, 230) if n else (160, 156, 170)) + (int(255 * b),), anchor='lm')
                    y += 70 * len(medios) + 26
                fuente_pie(dr, 'Propiedad: Media Ownership Monitor, CRC (2022), García y Zambrano (2025) · notas: corpus propio, 12 nov 2025 - 11 nov 2026')
            else:
                v = u - fase2
                texto(dr, (W / 2, 290), '¿Y SE NOTA EN CÓMO LO CUENTAN?', F('impact', 56), PAPEL + (int(255 * prog(v, 0, 0.4)),))
                for j, (med, dueno, cifra, que, col) in enumerate([('SEMANA', 'Gilinski', '29 de 58', 'notas eran PELEAS', (91, 74, 122)),
                                                                   ('CARACOL RADIO', 'Prisa', '36 de 70', 'notas eran sobre su trabajo en la UNGRD', (61, 138, 90))]):
                    b = out_back(prog(v, 0.5 + j * 0.8, 0.9 + j * 0.8))
                    c = Image.new('RGBA', (760, 360), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
                    d2.rounded_rectangle([3, 3, 757, 357], 26, fill=col + (245,), outline=PAPEL, width=4)
                    d2.text((380, 60), med, font=F('impact', 60), fill=PAPEL, anchor='mm'); d2.text((380, 115), 'dueño: ' + dueno, font=F('bold', 30), fill=(235, 235, 240), anchor='mm')
                    d2.text((380, 200), cifra, font=F('impact', 80), fill=ORO, anchor='mm')
                    for m, ln in enumerate(textwrap.wrap(que, 30)):
                        d2.text((380, 270 + m * 36), ln, font=F('bold', 30), fill=PAPEL, anchor='mm')
                    pegar(im, c, 540 + j * 840, 560, b)
                c_ = prog(v, 2.2, 2.7)
                texto(dr, (W / 2, 790), 'No prueba que el dueño dé órdenes, pero explica por qué cada medio cuenta a su manera.', F('reg', 32), (210, 206, 220, int(255 * c_)))
                c_ = prog(v, 0.70 * (L - fase2), 0.70 * (L - fase2) + 0.6)
                dr.rectangle([0, 860, W, 1010], fill=(0, 0, 0, int(220 * c_)))
                texto(dr, (W / 2, 905), 'ENFOQUE SOCIOLÓGICO', F('impact', 64), ORO + (int(255 * c_),))
                texto(dr, (W / 2, 970), 'no basta con contar noticias: ¿quién las cuenta y desde dónde?', F('bold', 40), PAPEL + (int(255 * c_),))
                fuente_pie(dr, 'Notas leídas a mano del corpus (216 notas de Semana, Caracol Radio y El Tiempo), dossier de precampaña')
        elif k == 5:  # mostrar
            barra(dr, 3, 1)
            orden = [('mini_mapa_zonas.png', 'Mapas por localidad'), ('mini_dolencias.png', 'Gráficas con datos'), ('mini_fichas.png', 'Fichas de precandidatos'), ('mini_dossier.png', 'Dossier de Carrillo'),
                     ('mini_presentacion.png', 'Presentación'), ('mini_lula.png', 'Avance Lula'), ('mini_juego.png', 'Este video')]
            for j, (n_, et) in enumerate(orden):
                fila, colu = divmod(j, 4)
                x, y = 270 + colu * 460, 360 + fila * 400
                b = out_back(prog(u, 0.3 + j * 0.09 * L, 0.7 + j * 0.09 * L))
                if b <= 0.01:
                    continue
                ft = ImageOps.fit(mini[n_], (400, 260), Image.LANCZOS, centering=(0.5, 0.0))
                c = Image.new('RGBA', (420, 330), (0, 0, 0, 0)); c.paste(ImageOps.expand(ft, 10, PAPEL), (0, 0))
                d2 = ImageDraw.Draw(c); d2.text((210, 305), et, font=F('bold', 30), fill=PAPEL, anchor='mm')
                pegar(im, c, x, y, b, angulo=(-2 if j % 2 else 2) * (1 - b))
            if u > 0.82 * L:
                texto(dr, (W / 2, 1030), 'Video: Google Flow + animación y edición propias', F('reg', 28), (190, 186, 200, int(255 * prog(u, 0.82 * L, 0.82 * L + 0.4))))
        else:  # para una campaña
            a = prog(u, 0, 0.5)
            texto(dr, (W / 2, 130), '¿PARA QUÉ LE SIRVE A UNA CAMPAÑA?', F('impact', 84), ORO + (int(255 * a),), borde=3)
            US = [('UN SONDEO PERMANENTE', 'qué temas mueven a la gente'), ('CUIDAR LAS PALABRAS', 'cuáles prenden la pelea y cuáles conectan'),
                  ('QUÉ LE DUELE A CADA LOCALIDAD', 'y dónde está el voto'), ('HABLAR DE LAS PERSONAS', 'no caer en lo tradicional: salir peleando no basta')]
            for j, (a_, b_) in enumerate(US):
                b = out_back(prog(u, 2.0 + j * 0.18 * L, 2.4 + j * 0.18 * L))
                c = Image.new('RGBA', (1400, 130), (0, 0, 0, 0)); d2 = ImageDraw.Draw(c)
                d2.rounded_rectangle([3, 3, 1397, 127], 24, fill=COL[j] + (240,), outline=PAPEL, width=3)
                d2.text((40, 48), a_, font=F('impact', 50), fill=PAPEL, anchor='lm'); d2.text((40, 100), b_, font=F('bold', 30), fill=(235, 235, 240), anchor='lm')
                pegar(im, c, W / 2, 290 + j * 160, b)
            if u > 0.78 * L:
                c_ = prog(u, 0.78 * L, 0.78 * L + 0.6)
                dr.rectangle([0, 920, W, 1050], fill=(0, 0, 0, int(220 * c_)))
                texto(dr, (W / 2, 960), 'EL PLUS DEL ENFOQUE SOCIOLÓGICO', F('bold', 38), (230, 226, 236, int(255 * c_)))
                texto(dr, (W / 2, 1012), 'DE LA INTUICIÓN A LA ESTRATEGIA', F('impact', 64), ORO + (int(255 * c_),))
        return viñeta(im)
    sfx = [(0.0, 'whoosh_cine', 0.4)] + [(T[i], 'whoosh_rapido', 0.35) for i in range(1, 7)] + \
          [(T[0] + 1.6 + j * 0.5, 'pop_suave', 0.3) for j in range(4)] + [(T[5] + 0.3 + j * 0.09 * (T[6] - T[5]), 'pop_suave', 0.25) for j in range(8)] + \
          [(T[6] + 0.78 * (T[7] - T[6]), 'mision_desbloqueada', 0.25)]
    return dur, f, sfx


ESCENAS = {'17_metodo': esc_metodo, '01_cifras': esc_cifras, '16_zonas': esc_zonas, '13_mcluhan': esc_mcluhan, '15_propuesta': esc_propuesta, '02_apellido': esc_apellido, '03_wanted': esc_wanted, '04_carrillo': esc_carrillo, '05_problema': esc_problema, '06_dolencias': esc_dolencias, '06b_movilidad': esc_movilidad, 'autor_bourdieu': lambda: esc_autor('bourdieu'), 'autor_wolf': lambda: esc_autor('wolf'), 'autor_lippmann': lambda: esc_autor('lippmann'), 'autor_castells': lambda: esc_autor('castells'),
           '07_calendario': esc_calendario, '08_tarjeta': esc_tarjeta, '09_mapa': esc_mapa, '10_cierre': esc_cierre, '11_creditos': esc_creditos}


def render(nombre, prueba=False, objetivo=None):
    from moviepy import VideoClip, AudioFileClip, CompositeAudioClip
    dur, fn0, sfx = ESCENAS[nombre]()
    k = dur / objetivo if objetivo else 1.0
    fn = (lambda t: fn0(min(t * k, dur - 0.01))) if k != 1 else fn0
    sfx = [(t0 / k, s_, v_) for t0, s_, v_ in sfx]; dur = dur / k

    def cuadro(t):
        return np.asarray(fn(t).convert('RGB'))
    if prueba:
        for k, t in enumerate(np.linspace(0, dur - 0.05, 6)):
            fn(t).convert('RGB').resize((640, 360)).save(os.path.join(ESC, f'{nombre}_prueba_{k}.png'))
        return
    clip = VideoClip(cuadro, duration=dur)
    aud = []
    for t0, s, vol in sfx:
        a = AudioFileClip(os.path.join(SON, s + '.mp3'))
        a = a.subclipped(0, min(a.duration, dur - t0)).with_start(t0).with_volume_scaled(vol * 0.7)
        aud.append(a)
    if aud:
        clip = clip.with_audio(CompositeAudioClip(aud).with_duration(dur))
    clip.write_videofile(os.path.join(ESC, nombre + '.mp4'), fps=FPS, codec='libx264', audio_codec='aac', preset='medium', bitrate='8000k', threads=8, logger=None)
    print('listo', nombre, dur)


if __name__ == '__main__':
    args = sys.argv[1:]
    prueba = '--prueba' in args
    for n in [a for a in args if not a.startswith('--')] or ESCENAS:
        nom, _, obj = n.partition('=')
        render(nom, prueba, float(obj) if obj else None)

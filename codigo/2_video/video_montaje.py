"""Montaje del video v3: apertura con el clip de Luis Carlos Galán, crisis con clips de noticieros y cifras, escenas animadas,
tarjetas de autores, voz de Diego y música con 'ducking'. Carpetas dentro de ENTREGA_VIDEO/:
  voz/01 ... voz/12   una grabación por escena (m4a, mp3 o wav)   ·   camara/02.mp4 y camara/08.mp4   ·   flow/NN.mp4 (va antes de la animación de la escena NN)
Si algo falta, el montaje pone una tarjeta que lo dice. Salida: ENTREGA_VIDEO/Video_Carrillo_borrador.mp4"""
import glob, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from moviepy import (VideoFileClip, AudioFileClip, CompositeAudioClip, ImageClip, CompositeVideoClip, VideoClip, concatenate_videoclips, vfx, afx)
import video_anim as VA

D = os.path.dirname(os.path.abspath(__file__)); V = os.path.join(D, 'ENTREGA_VIDEO'); ESC = os.path.join(V, 'escenas'); SON = os.path.join(V, 'sonidos'); CL = os.path.join(V, 'clips')
W, H = 1920, 1080
FUENTE = ImageFont.truetype(r'C:\Windows\Fonts\segoeuib.ttf', 30)


def etiqueta(txt, dur, y=H - 40):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((40, y), txt, font=FUENTE, fill=(255, 255, 255, 230), anchor='lm', stroke_width=3, stroke_fill=(0, 0, 0))
    a = np.asarray(im)
    return ImageClip(a[:, :, :3]).with_mask(ImageClip(a[:, :, 3] / 255.0, is_mask=True)).with_duration(dur)


def a_169(c):
    """Clip vertical o 4:3 -> 16:9 con fondo desenfocado (estilo TikTok)."""
    fg = c.resized(height=H)
    if abs(fg.w - W) < 4:
        return fg
    bg = c.resized(width=W).cropped(y_center=c.resized(width=W).h / 2, height=H)
    bg = bg.image_transform(lambda f: np.asarray(ImageEnhance.Brightness(Image.fromarray(f).resize((W // 6, H // 6)).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)).enhance(0.45)))
    return CompositeVideoClip([bg, fg.with_position('center')], size=(W, H)).with_duration(c.duration)


def tramo(nombre, a, b, credito, vol=0.3):
    c = VideoFileClip(os.path.join(CL, nombre)).subclipped(a, b)
    v = CompositeVideoClip([a_169(c), etiqueta('Video: ' + credito, c.duration)], size=(W, H)).with_duration(c.duration)
    return v.with_audio(c.audio.with_volume_scaled(vol)) if c.audio else v


def buscar(carpeta, n):
    for ext in ('m4a', 'mp3', 'wav', 'aac', 'ogg', 'opus', 'mp4', 'mov'):
        f = glob.glob(os.path.join(V, carpeta, f'{n}.{ext}'))
        if f:
            return f[0]
    return None


def tarjeta(txt, dur):
    im = Image.new('RGB', (W, H), (30, 28, 26)); d = ImageDraw.Draw(im)
    d.text((W / 2, H / 2), txt, font=ImageFont.truetype(r'C:\Windows\Fonts\segoeuib.ttf', 64), fill=(242, 182, 50), anchor='mm', align='center')
    return ImageClip(np.asarray(im)).with_duration(dur)


def anim(n):
    return VideoFileClip(os.path.join(ESC, n + '.mp4'))


def musica(nombre, dur, vol):
    m = AudioFileClip(os.path.join(SON, nombre + '.mp3'))
    m = m.with_effects([afx.AudioLoop(duration=dur)]) if m.duration < dur else m.subclipped(0, dur)
    return m.with_volume_scaled(vol).with_effects([afx.AudioFadeIn(0.5), afx.AudioFadeOut(0.8)])


def escena_crisis():
    partes = [tramo('01_juan_pablo_camacho.mp4', 0, 6.8, 'TikTok @Juan Pablo Camacho Báez'), tramo('02_kienyke.mp4', 5, 13, 'KienyKe'),
              tramo('03_pulzo.mp4', 2, 9, 'Pulzo'), tramo('04_el_espectador.mp4', 0, 7, 'El Espectador')]
    base = concatenate_videoclips(partes, method='compose'); dur = base.duration
    f, sfx = VA.cifras_overlay(dur, (3.0, 11.0, 19.0)); cache = {}

    def capa(t):
        if t not in cache:
            cache.clear(); cache[t] = np.asarray(f(t))
        return cache[t]
    ov = VideoClip(lambda t: capa(t)[:, :, :3], duration=dur).with_mask(VideoClip(lambda t: capa(t)[:, :, 3] / 255.0, duration=dur, is_mask=True))
    v = CompositeVideoClip([base, ov], size=(W, H)).with_duration(dur)
    aud = [base.audio] + [AudioFileClip(os.path.join(SON, s + '.mp3')).with_start(t0).with_volume_scaled(vol * 0.6) for t0, s, vol in sfx]
    return v.with_audio(CompositeAudioClip(aud).with_duration(dur))


def _coefs(dst, src):
    """Coeficientes de PIL PERSPECTIVE que llevan el cuadrilátero dst (pantalla) al rectángulo src (imagen)."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def escena_gta(dur=26.3):
    """Pantallas de carga estilo GTA V: cada ilustración animada con Flow va en un panel inclinado en 3D sobre negro,
    que se aleja despacio; entre una y otra, fundido a negro. Orden igual al audio 03."""
    nombres = ['oviedo', 'valencia', 'lopez', 'penalosa']
    clips = [VideoFileClip(os.path.join(V, 'gta', n + '.mp4')).without_audio() for n in nombres]
    T = dur / len(clips)
    giro = [1, -1, 1, -1]          # hacia qué lado se inclina el panel
    fspin = ImageFont.truetype(r'C:\Windows\Fonts\segoeui.ttf', 22)

    def frame(t):
        i = min(int(t // T), len(clips) - 1); lt = t - i * T; p = lt / T
        c = clips[i]; src = Image.fromarray(c.get_frame(min(lt * c.duration / T, c.duration - 0.05)))
        sw, sh = src.size
        e = 1 - p * 0.10                                   # el panel se aleja (se encoge) despacio
        w, h = 1560 * e, 878 * e
        k = (0.07 + 0.03 * p) * giro[i]                    # inclinación 3D que aumenta un poco
        cx, cy = W / 2 + giro[i] * (-30 + 60 * p), H / 2 - 10
        hl, hr = h * (1 + k), h * (1 - k)
        dst = [(cx - w / 2, cy - hl / 2), (cx + w / 2, cy - hr / 2), (cx + w / 2, cy + hr / 2), (cx - w / 2, cy + hl / 2)]
        panel = src.transform((W, H), Image.PERSPECTIVE, _coefs(dst, [(0, 0), (sw, 0), (sw, sh), (0, sh)]), Image.BICUBIC)
        mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(dst, fill=255)
        im = Image.new('RGB', (W, H), (0, 0, 0)); im.paste(panel, (0, 0), mask)
        # sombra suave del borde inferior, como en el juego
        dr = ImageDraw.Draw(im, 'RGBA')
        # indicador de carga abajo a la derecha
        a = (t * 4) % (2 * math.pi)
        for s in range(8):
            ang = a + s * math.pi / 4; al = int(255 * (s + 1) / 8)
            dr.ellipse([W - 70 + 16 * math.cos(ang) - 3, H - 60 + 16 * math.sin(ang) - 3, W - 70 + 16 * math.cos(ang) + 3, H - 60 + 16 * math.sin(ang) + 3], fill=(255, 255, 255, al))
        dr.text((W - 100, H - 60), 'Cargando', font=fspin, fill=(255, 255, 255, 200), anchor='rm')
        luz = min(1, lt / 0.6, (T - lt) / 0.6)            # fundido desde y hacia negro
        if luz < 1:
            im = Image.blend(Image.new('RGB', (W, H)), im, max(0, luz))
        return np.asarray(im)
    return VideoClip(frame, duration=dur)


def con_fondo(nombre_anim, n_flow, alpha=0.38):
    """La animación encima y el clip de Google Flow de fondo, semitransparente: el video solo se ve donde la animación
    es oscura (el fondo), así los textos, mapas y viñetas quedan intactos. El clip va de ida y vuelta para no cortar."""
    a = anim(nombre_anim)
    f = VideoFileClip(buscar('flow', n_flow)).without_audio()
    cuadros = [np.asarray(Image.fromarray(fr).resize((960, 540), Image.BILINEAR)) for fr in f.iter_frames(fps=24)]
    n = len(cuadros)

    def frame(t):
        A = a.get_frame(min(t, a.duration - 0.04)).astype(np.float32)
        k = int(t * 24) % (2 * n - 2); k = k if k < n else 2 * n - 2 - k
        B = np.asarray(Image.fromarray(cuadros[k]).resize((W, H), Image.BILINEAR)).astype(np.float32)
        brillo = A.max(axis=2)
        m = (np.clip((80 - brillo) / 50, 0, 1) * alpha)[..., None]
        return (A * (1 - m) + B * m).astype(np.uint8)
    v = VideoClip(frame, duration=a.duration)
    v = CompositeVideoClip([v, etiqueta('Fondo generado con IA: Google Flow', a.duration, y=40)], size=(W, H)).with_duration(a.duration)
    return v.with_audio(a.audio) if a.audio else v


JUEGO = os.path.join(os.path.expanduser('~'), 'Downloads', 'We Become What We Behold Full Playthrough _ Longplay _ Walkthrough (no commentary) - Ludophiles (1080p, h264).mp4')
# Escena 14: una parte por párrafo del guion (la voz se parte por los silencios entre párrafos).
# tipo 'video': (a, b) del gameplay a velocidad real · 'pepe' y 'medio': cuadro congelado (77 s) con zoom y señales
# (tipo, a, b, palabras, subtítulo, tarjeta de autor)
PARTES_JUEGO = [
    ('video', 0.5, 8.5, 14, None, None),
    ('pepe', 77.0, 77.0, 40, None, None),
    ('medio', 77.0, 77.0, 42, None, None),
    ('video', 23.0, 38.0, 48, '“¡Qué lindo sombrero!” … “Ya los sombreros no están de moda”', None),
    ('video', 48.0, 70.0, 34, 'Si algo no parece importante, la gente no le para bolas', None),
    ('video', 76.5, 92.0, 46, '“Cuadrado loco ataca”', ('MAURO WOLF', 'Para los medios, el conflicto vale más como noticia.')),
    ('video', 136.0, 158.0, 44, '“Los círculos le temen a los cuadrados”', ('WALTER LIPPMANN', 'Reaccionamos a la imagen que tenemos en la cabeza, no a lo que pasó.')),
    ('video', 158.0, 202.0, 50, '“La paz aburre, la violencia se vuelve viral”', None),
    ('video', 208.0, 240.0, 28, '“Casi todos odian a todos”', None),
    ('video', 17.5, 22.0, 26, None, ('MANUEL CASTELLS', 'Lo que no sale en la pantalla, para la gente casi no existe.')),
]
PEPE, VECINOS, TELE, CAMARA = (805, 268), [(393, 715), (520, 690), (1135, 940), (1555, 230)], (960, 470), (1370, 545)


def partir_voz(ruta, n):
    """Inicio de cada párrafo: los n-1 silencios más largos de la grabación."""
    import subprocess, re, imageio_ffmpeg
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-i', ruta, '-af', 'silencedetect=n=-35dB:d=0.7', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r)]; fin = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]
    sil = sorted([(f - i, (i + f) / 2) for i, f in zip(ini, fin) if i > 0.5 and f - i > 1.5], reverse=True)[:n - 1]
    if len(sil) == n - 1:
        return sorted(m for _, m in sil)
    # sin pausas largas: alineo frase por frase (sílabas del guion contra las pausas de la grabación)
    import alinear_voz
    par = open(os.path.join(D, 'guion_14.txt'), encoding='utf-8').read().strip().splitlines()
    return alinear_voz.alinear(ruta, par)


# momentos del gameplay (segundos del video original), medidos cuadro a cuadro
FOTOS = [23.6, 34.1, 43.5, 52.3, 60.9, 69.7, 82.7, 100.2, 116.4, 128.2, 138.6, 149.2, 162.0, 174.3, 189.5, 199.0, 209.5, 220.7]
NOTICIAS = [25.8, 36.2, 45.6, 54.4, 63.0, 71.8, 84.8, 102.3, 118.5, 130.4, 140.7, 151.3, 164.1, 176.4, 191.6, 201.1, 211.6, 222.8]
SOUNDTRACK = os.path.join(os.path.expanduser('~'), 'Downloads', 'Kevin MacLeod Lightless Dawn - Kevin MacLeod Archive.mp3')


def escena_juego(dur=None, inicio_voz=0.3, voz=None):
    src = VideoFileClip(JUEGO)
    n = len(PARTES_JUEGO)
    cortes = partir_voz(voz, n) if voz else None
    if cortes:
        lim = [0.0] + [inicio_voz + c for c in cortes] + [dur]
    else:  # sin voz: 0,42 s por palabra
        lim = [0.0]
        for p in PARTES_JUEGO:
            lim.append(lim[-1] + p[3] * 0.42)
        dur = lim[-1] + 0.8; lim[-1] = dur
    F_ = VA.F; congelado = Image.fromarray(src.get_frame(77.0)).convert('RGB').resize((W, H))

    def zoom(im, z, cx, cy):
        return VA.camara(im, z, cx, cy)

    def foco(im, cx, cy, r, a):
        m = Image.new('L', (W, H), int(150 * a)); ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
        m = m.filter(ImageFilter.GaussianBlur(18)); negro = Image.new('RGB', (W, H), (10, 10, 14))
        return Image.composite(negro, im, m)

    def flecha(d, x0, y0, x1, y1, color=(200, 30, 36)):
        d.line([(x0, y0), (x1, y1)], fill=color, width=8)
        dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy) or 1; dx, dy = dx / L, dy / L
        d.polygon([(x1 + dx * 26, y1 + dy * 26), (x1 - dy * 16, y1 + dx * 16), (x1 + dy * 16, y1 - dx * 16)], fill=color)

    def etiq(d, x, y, txt, tam=46, fondo=(200, 30, 36)):
        f = F_('impact', tam); w = d.textlength(txt, font=f)
        d.rounded_rectangle([x - w / 2 - 22, y - tam * 0.75, x + w / 2 + 22, y + tam * 0.75], 14, fill=fondo)
        d.text((x, y), txt, font=f, fill=(255, 255, 255), anchor='mm')

    def frame(t):
        k = next((i for i in range(n) if t < lim[i + 1]), n - 1)
        tipo, a, b, _, sub, autor = PARTES_JUEGO[k]; u = t - lim[k]; L = lim[k + 1] - lim[k]
        if tipo == 'video':
            vel = max(0.6, min(1.0, (b - a) / L)) if L > 0 else 1
            im = Image.fromarray(src.get_frame(min(a + u * vel, b, src.duration - 0.05))).convert('RGB').resize((W, H))
            d = ImageDraw.Draw(im, 'RGBA')
        elif tipo == 'pepe':
            p = u / L; z = 1 + 1.4 * VA.in_out(min(1, u / 1.5)) * (1 - VA.in_out(VA.prog(p, 0.45, 0.6)))
            im = foco(congelado.copy(), *PEPE, 90, 1 - VA.prog(p, 0.45, 0.6))
            d = ImageDraw.Draw(im, 'RGBA')
            if p < 0.5:
                etiq(d, PEPE[0], PEPE[1] - 120, 'ÉL ES PEPE', 56)
            else:
                etiq(d, PEPE[0], PEPE[1] - 110, 'PEPE', 46)
                for j, (x, y) in enumerate(VECINOS):
                    if VA.prog(p, 0.6 + j * 0.06, 0.66 + j * 0.06) > 0:
                        etiq(d, x, y - 100, 'VECINO', 34, (47, 111, 143))
            im = zoom(im, z, *PEPE); d = ImageDraw.Draw(im, 'RGBA')
        else:  # medio
            p = u / L; im = congelado.copy()
            foc = TELE if p < 0.55 else CAMARA
            im = foco(im, foc[0], foc[1], 230 if p < 0.55 else 270, 1.0)
            d = ImageDraw.Draw(im, 'RGBA')
            if p < 0.55:
                etiq(d, TELE[0], 160, 'LA PANTALLA = EL MEDIO', 58)
                d.text((TELE[0], 790), 'como el noticiero o el celular', font=F_('bold', 44), fill=(255, 255, 255), anchor='mm', stroke_width=4, stroke_fill=(0, 0, 0))
            else:
                etiq(d, CAMARA[0], 220, 'TÚ = LA CÁMARA', 58)
                d.text((CAMARA[0], 880), 'lo que grabas, lo ve todo el pueblo', font=F_('bold', 44), fill=(255, 255, 255), anchor='mm', stroke_width=4, stroke_fill=(0, 0, 0))
                flecha(d, CAMARA[0] - 200, CAMARA[1], TELE[0] + 170, TELE[1])
        ent = min(1.0, u / 0.4)
        if k == 0:
            d.rounded_rectangle([380, 820, 1540, 990], 24, fill=(20, 18, 16, int(225 * ent)))
            d.text((960, 870), 'WE BECOME WHAT WE BEHOLD', font=F_('impact', 64), fill=(242, 182, 50, int(255 * ent)), anchor='mm')
            d.text((960, 945), 'Nicky Case (2016) · “Nos convertimos en lo que contemplamos”', font=F_('bold', 30), fill=(244, 240, 232, int(255 * ent)), anchor='mm')
        if sub:  # traducción pequeña abajo, sin tapar
            f = F_('bold', 36); w = d.textlength(sub, font=f)
            d.rounded_rectangle([960 - w / 2 - 24, 1000, 960 + w / 2 + 24, 1056], 16, fill=(15, 15, 18, int(190 * ent)))
            d.text((960, 1028), sub, font=f, fill=(255, 255, 255, int(255 * ent)), anchor='mm')
        if autor and u > 1.0:  # tarjeta pequeña arriba a la derecha
            e = VA.out_cubic(min(1.0, (u - 1.0) / 0.4)); x = W - 700 * e - 20
            d.rounded_rectangle([x, 30, x + 680, 190], 20, fill=(20, 18, 26, 225), outline=(242, 182, 50), width=3)
            d.text((x + 28, 72), 'COMO DECÍA ' + autor[0], font=F_('impact', 40), fill=(242, 182, 50), anchor='lm')
            import textwrap
            for m, ln in enumerate(textwrap.wrap(autor[1], 36)):
                d.text((x + 28, 122 + m * 40), ln, font=F_('serif', 30), fill=(255, 255, 255), anchor='lm')
        d.text((24, 22), 'Gameplay: We Become What We Behold, Nicky Case (dominio público, CC0) · video: Ludophiles', font=F_('bold', 22), fill=(255, 255, 255, 200), anchor='lt', stroke_width=3, stroke_fill=(0, 0, 0))
        return np.asarray(im)
    v = VideoClip(frame, duration=dur)
    # sin el audio del juego: solo clic de cámara en cada foto, un toque suave cuando sale la noticia, y soundtrack de fondo
    capas = [AudioFileClip(SOUNDTRACK).subclipped(0, dur).with_volume_scaled(0.45).with_effects([afx.AudioFadeIn(1.5), afx.AudioFadeOut(2.0)])]
    for k, p in enumerate(PARTES_JUEGO):
        tipo, a, b = p[0], p[1], p[2]; L = lim[k + 1] - lim[k]
        if tipo != 'video' or L <= 0:
            continue
        vel = max(0.6, min(1.0, (b - a) / L))
        for lista, nombre, vol in ((FOTOS, 'camara', 0.55), (NOTICIAS, 'pop_suave', 0.35)):
            for s in lista:
                t0 = lim[k] + (s - a) / vel
                if a <= s < b and t0 < lim[k + 1] - 0.3:
                    capas.append(AudioFileClip(os.path.join(SON, nombre + '.mp3')).with_start(t0).with_volume_scaled(vol))
    return v.with_audio(CompositeAudioClip(capas).with_duration(dur))


# (número de voz, lista de piezas, música, volumen, voz al final)
PLAN = [
    ('00', [('clip', '00_sebastian_quintero.mp4', 'TikTok @Sebastián Quintero')], None, 0, False),
    ('01', [('crisis',)], 'musica_dramatica', 0.45, True),
    ('02', [('anim', '02_apellido'), ('anim', 'autor_bourdieu')], 'musica_dramatica', 0.25, False),
    ('03', [('gta',)], 'gta4', 0.60, False),
    ('04', [('anim', '04_carrillo')], None, 0, False),
    ('05', [('anim', '05_problema'), ('anim', 'autor_wolf')], 'musica_juego', 0.22, False),
    ('06', [('anim', '06_dolencias'), ('anim', 'autor_lippmann'), ('anim', 'autor_castells')], 'musica_seria', 0.32, False),
    ('13', [('anim', '13_mcluhan')], 'musica_seria', 0.30, False),
    ('14', [('juego',)], None, 0, False),
    ('15', [('anim', '15_propuesta')], 'musica_seria', 0.28, False),
    ('07', [('fondo', '06b_movilidad', '06')], 'musica_seria', 0.32, False),
    ('08', [('anim', '07_calendario')], 'musica_seria', 0.28, False),
    ('09', [('anim', '08_tarjeta')], 'musica_juego', 0.28, False),
    ('10', [('fondo', '09_mapa', '10')], 'musica_juego', 0.28, False),
    ('16', [('anim', '16_zonas')], 'musica_seria', 0.28, False),
    ('11', [('fondo', '10_cierre', '11')], 'musica_cierre', 0.40, False),
    ('17', [('anim', '17_metodo')], 'musica_seria', 0.25, False),
    ('12', [('anim', '11_creditos')], 'musica_cierre', 0.50, False),
]

partes = []
for n, piezas, mus, vol, voz_al_final in PLAN:
    vf = buscar('voz', n); va = AudioFileClip(vf) if vf and not vf.endswith(('.mp4', '.mov')) else None
    vis = []; retraso = 0.0
    for p in piezas:
        if p[0] == 'clip':
            c = VideoFileClip(os.path.join(CL, p[1]))
            vis.append(CompositeVideoClip([a_169(c), etiqueta('Video: ' + p[2], c.duration)], size=(W, H)).with_duration(c.duration).with_audio(c.audio))
        elif p[0] == 'crisis':
            vis.append(escena_crisis())
        elif p[0] == 'fondo':
            vis.append(con_fondo(p[1], p[2]))
        elif p[0] == 'gta':
            vis.append(escena_gta())
        elif p[0] == 'juego':
            vis.append(escena_juego(va.duration + 1.1, voz=vf) if va else escena_juego())
        elif p[0] == 'anim':
            vis.append(anim(p[1]))
        elif p[0] == 'camara':
            cam = buscar('camara', n)
            vis.append(VideoFileClip(cam).resized(height=H) if cam else tarjeta(f'ESCENA {n}\nAQUÍ VA TU TOMA A CÁMARA', 6))
        elif p[0] == 'flow':
            fl = buscar('flow', n)
            if fl:
                c = VideoFileClip(fl).without_audio().resized(height=H)
                vis.append(CompositeVideoClip([c, etiqueta('Generado con IA: Google Flow', c.duration)], size=(W, H)).with_duration(c.duration))
                retraso += c.duration
    clip = concatenate_videoclips(vis, method='compose') if len(vis) > 1 else vis[0]
    if va and retraso + va.duration + 0.8 > clip.duration:
        clip = concatenate_videoclips([clip, clip.to_ImageClip(clip.duration - 0.05).with_duration(retraso + va.duration + 0.8 - clip.duration)])
    capas = [clip.audio] if clip.audio else []
    if va:
        capas.append(va.with_start(max(0.3, clip.duration - va.duration - 0.5) if voz_al_final else 0.3 + retraso).with_volume_scaled(1.6))
    if mus:
        capas.append(musica(mus, clip.duration, vol * (0.55 if va else 1.0)))
    if capas:
        clip = clip.with_audio(CompositeAudioClip(capas).with_duration(clip.duration))
    partes.append(clip.with_effects([vfx.FadeIn(0.15), vfx.FadeOut(0.15)]))
    print(n, round(clip.duration, 1), 'voz' if va else 'sin voz', flush=True)
final = concatenate_videoclips(partes, method='compose')
print('duración total', round(final.duration, 1), 's')
salida = os.path.join(V, 'Video_Carrillo_borrador.mp4')
final.write_videofile(salida, fps=30, codec='libx264', audio_codec='aac', preset='medium', bitrate='8000k', threads=8, logger=None)
print(salida)

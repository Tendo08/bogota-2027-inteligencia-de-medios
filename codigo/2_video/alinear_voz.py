"""Alinea el guion con la grabación sin reconocimiento de voz:
divide el guion en frases (por la puntuación), detecta las pausas de la grabación
y empareja fronteras de frase con pausas por programación dinámica, usando el
número de sílabas como medida del tiempo que toma decir cada frase."""
import re, subprocess, imageio_ffmpeg


def silabas(txt):
    return max(1, len(re.findall(r'[aeiouáéíóúü]+', txt.lower())))


def pausas(ruta, umbral='-32dB', minimo=0.2):
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-i', ruta, '-af', f'silencedetect=n={umbral}:d={minimo}', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', r)]
    fin = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]
    dur = float(re.findall(r'time=(\d+):(\d+):([\d.]+)', r)[-1][2]) + 60 * int(re.findall(r'time=(\d+):(\d+):([\d.]+)', r)[-1][1])
    return [(max(0, i), f) for i, f in zip(ini, fin) if i > 0.3 and f < dur - 0.3], dur


def alinear(ruta, parrafos):
    """Devuelve el instante (s) en que empieza cada párrafo, excepto el primero."""
    frases = []  # (sílabas, tipo de frontera al final: 2 párrafo, 1 punto, 0 coma)
    for k, p in enumerate(parrafos):
        trozos = [t for t in re.split(r'(?<=[.,:;?!])\s+', p.strip()) if t]
        for m, t in enumerate(trozos):
            fin = 2 if m == len(trozos) - 1 else (1 if t[-1] in '.?!:' else 0)
            frases.append((silabas(t), fin))
    frases[-1] = (frases[-1][0], 3)
    P, dur = pausas(ruta)
    # nodos de tiempo: inicio, pausas, final
    nodos = [(0.0, 0.0, 0.0)] + [(i, f, f - i) for i, f in P] + [(dur, dur, 0.0)]
    habla = [0.0]
    for a in range(1, len(nodos)):
        habla.append(habla[-1] + max(0.0, nodos[a][0] - nodos[a - 1][1]))
    sil = [0] + [s for s, _ in frases]
    acum = [0]
    for s in sil[1:]:
        acum.append(acum[-1] + s)
    ritmo = habla[-1] / acum[-1]
    B, N = len(frases), len(nodos)
    INF = 1e18
    # costo[b][n]: frontera b (0 = inicio) puesta en el nodo n
    costo = [[INF] * N for _ in range(B + 1)]; atras = [[None] * N for _ in range(B + 1)]
    costo[0][0] = 0.0
    salto = {0: 0.6, 1: 3.0, 2: 6.0, 3: 50.0}
    for b in range(1, B + 1):
        tipo = frases[b - 1][1]
        for n in range(1, N):
            if b == B and n != N - 1:
                continue
            mejor, de = INF, None
            for b0 in range(max(0, b - 4), b):
                pen_b = sum(salto[frases[x - 1][1]] for x in range(b0 + 1, b))
                for n0 in range(max(0, n - 6), n):
                    if costo[b0][n0] >= INF:
                        continue
                    d = habla[n] - habla[n0]; e = ritmo * (acum[b] - acum[b0])
                    sig = 0.22 * e + 0.5
                    pen_n = sum(1.5 * min(1.0, nodos[x][2] / 0.6) for x in range(n0 + 1, n))
                    c = costo[b0][n0] + ((d - e) / sig) ** 2 + pen_b + pen_n
                    if c < mejor:
                        mejor, de = c, (b0, n0)
            if de is None:
                continue
            largo = nodos[n][2]
            bono = {0: 0.3, 1: 1.2, 2: 2.5, 3: 0}[tipo] * min(1.0, largo / 0.6)
            costo[b][n] = mejor - bono; atras[b][n] = de
    # reconstruir
    asign = {}; b, n = B, N - 1
    while b > 0:
        asign[b] = n; b, n = atras[b][n]
    # instante de cada frontera (las saltadas se interpolan por sílabas)
    t_front = {0: 0.0}
    for b in range(1, B + 1):
        if b in asign:
            i, f, _ = nodos[asign[b]]; t_front[b] = (i + f) / 2 if b < B else dur
    claves = sorted(t_front)
    def t_de(b):
        if b in t_front:
            return t_front[b]
        a = max(k for k in claves if k < b); z = min(k for k in claves if k > b)
        return t_front[a] + (t_front[z] - t_front[a]) * (acum[b] - acum[a]) / (acum[z] - acum[a])
    cortes, b = [], 0
    for k, p in enumerate(parrafos[:-1]):
        b += len([t for t in re.split(r'(?<=[.,:;?!])\s+', p.strip()) if t])
        cortes.append(round(t_de(b), 2))
    return cortes


if __name__ == '__main__':
    import sys, os
    D = os.path.dirname(os.path.abspath(__file__))
    par = open(os.path.join(D, sys.argv[2]), encoding='utf-8').read().strip().splitlines()
    print(alinear(sys.argv[1], par))

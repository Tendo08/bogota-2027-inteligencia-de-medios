BASE = "."  # carpeta del proyecto
"""Mapas legibles: cada localidad con su nombre y su porcentaje; las pequeñas del centro con línea guía; Sumapaz en recuadro.
Un mapa por figura (pobreza y voto), a lo ancho de la página. Más la cuadrícula de Google Trends con leyenda de colores."""
import json, os, sys, unicodedata
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mc
from matplotlib.patches import Polygon as MPoly, Rectangle
from shapely.geometry import shape
import matplotlib.patheffects as pe
D = BASE
O = os.path.join(D, 'dossier_datos')
G = os.path.join(D, 'ENTREGA_DOSSIER', 'graficas')
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 10})
TINTA, GRIS = '#1d1b18', '#6f685e'


def norm(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()


URB = json.load(open(os.path.join(O, 'localidades_urbanas.json'), encoding='utf-8'))
LOC = {o['nombre']: o for o in json.load(open(os.path.join(D, 'mapa_localidades.json'), encoding='utf-8'))}
V26 = {}
for a in json.load(open(os.path.join(D, 'fuentes_primarias', 'registraduria', 'presidente_2026_localidad.json'), encoding='utf-8')):
    V26[{'CANDELARIA': 'LA CANDELARIA', 'MARTIRES': 'LOS MARTIRES', 'RAFAEL URIBE URIB': 'RAFAEL URIBE URIBE', '': 'SIN'}.get(a['L'], a['L'])] = a
NOMS = [n for n in URB]
POB = {n: LOC[n]['pobreza'] for n in NOMS}
CEP = {n: V26[norm(n)]['Cepeda'] for n in NOMS}
CORTO = {'Rafael Uribe Uribe': 'Rafael\nUribe U.', 'Barrios Unidos': 'Barrios\nUnidos', 'Puente Aranda': 'Puente\nAranda', 'Ciudad Bolívar': 'Ciudad\nBolívar', 'San Cristóbal': 'San\nCristóbal'}
# Localidades pequeñas: etiqueta afuera, a la derecha, con línea guía (como en los mapas de la Alcaldía)
AFUERA = {'Chapinero': (-73.975, 4.685), 'Los Mártires': (-73.975, 4.645), 'Santa Fe': (-73.975, 4.623), 'La Candelaria': (-73.975, 4.603),
          'Antonio Nariño': (-73.975, 4.583), 'San Cristóbal': (-73.975, 4.553), 'Tunjuelito': (-74.195, 4.578)}
MOVER = {'Usaquén': (0.012, 0.0), 'Suba': (-0.01, 0.0), 'Ciudad Bolívar': (-0.02, 0.012), 'Rafael Uribe Uribe': (0.0, -0.004), 'Usme': (0.0, 0.004)}


def mapa(dic, cmap, lim, titulo, nota, sumapaz, archivo, unidad='%'):
    fig, ax = plt.subplots(figsize=(7.6, 8.6))
    nm = mc.Normalize(*lim); cm = plt.get_cmap(cmap)
    for n in NOMS:
        g = shape(URB[n]); v = dic[n]
        for p in ([g] if g.geom_type == 'Polygon' else list(g.geoms)):
            ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=cm(nm(v)), ec='white', lw=1.1))
    for n in NOMS:
        g = shape(URB[n]); v = dic[n]; c = g.representative_point()
        txt = f'{v:.1f} %'.replace('.', ',')
        if n in AFUERA:
            x, y = AFUERA[n]; izq = x < -74.1
            ax.annotate(f'{n}  {txt}', xy=(c.x, c.y), xytext=(x, y), fontsize=8.6, color=TINTA, ha='right' if izq else 'left', va='center',
                        arrowprops=dict(arrowstyle='-', color=TINTA, lw=.7, shrinkA=0, shrinkB=0))
            ax.plot(c.x, c.y, 'o', ms=2.5, color=TINTA)
        else:
            dx, dy = MOVER.get(n, (0, 0)); osc = nm(v) > .6
            ax.text(c.x + dx, c.y + dy, f'{CORTO.get(n, n)}\n{txt}', ha='center', va='center', fontsize=8.2, color='white' if osc else TINTA, linespacing=.95,
                    fontweight='bold', path_effects=[pe.withStroke(linewidth=2.2, foreground=cm(nm(v)))])
    # Sumapaz: rural, fuera de escala; recuadro como en los mapas oficiales
    v = sumapaz
    ax.add_patch(Rectangle((-74.01, 4.475), 0.032, 0.03, fc=cm(nm(min(v, lim[1]))), ec=TINTA, lw=.6))
    ax.text(-74.012, 4.49, f'Sumapaz (rural)\n{v:.1f} %'.replace('.', ','), ha='right', va='center', fontsize=8.4, color=TINTA)
    ax.set_xlim(-74.29, -73.90); ax.set_ylim(4.465, 4.84); ax.set_aspect('equal'); ax.axis('off')
    sm = plt.cm.ScalarMappable(norm=nm, cmap=cm)
    cb = fig.colorbar(sm, ax=ax, orientation='horizontal', fraction=.03, pad=.01, shrink=.6); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=8)
    cb.set_label('Más claro = menos   ·   más oscuro = más (%)', fontsize=8, color=GRIS)
    ax.set_title(titulo, loc='left', fontsize=11, color=TINTA)
    fig.text(0.06, 0.02, nota, fontsize=7.2, color=GRIS)
    fig.savefig(os.path.join(G, archivo), dpi=220, bbox_inches='tight', facecolor='white'); plt.close(fig)


mapa(POB, 'Oranges', (0, 40), 'Pobreza monetaria por localidad (zona urbana): el sur dobla o triplica al norte',
     'Fuente: DANE-SDP, Encuesta Multipropósito 2025, cuadro 216A (pobreza en la zona urbana de cada localidad) y 216B (Sumapaz, rural).\n'
     'El mapa dibuja solo el área urbana (UPZ de la Secretaría de Seguridad), porque esa es el área que mide la cifra del DANE.', 11.39, '5a_mapa_pobreza.png')
mapa(CEP, 'Blues', (20, 62), 'Voto por Iván Cepeda (izquierda), 1.ª vuelta presidencial 2026: la misma geografía',
     'Fuente: Registraduría Nacional, resultados por mesa de la primera vuelta 2026, sumados por localidad (cálculo propio).\n'
     'Sumapaz: 76,4 % de 2.179 votos, por encima de la escala. Es el voto de Cepeda, no de Carrillo: sirve para ver dónde está el electorado de su sector.', 76.4,
     '5b_mapa_voto.png')


# ---------- Galán 2023 ----------
A23 = {norm(a['L']): a for a in json.load(open(os.path.join(D, 'fuentes_primarias', 'registraduria', 'alcaldia_2023_localidad.json'), encoding='utf-8'))}
GAL = {n: A23[norm(n)]['CARLOS FERNANDO GALAN PACHON'] for n in NOMS}
mapa(GAL, 'YlOrBr', (30, 62), 'Voto por Carlos Fernando Galán, Alcaldía 2023: ganó en todas las localidades urbanas',
     'Fuente: Registraduría Nacional, escrutinio por mesa de la elección de alcalde 2023, sumado por localidad (cálculo propio). Total en Bogotá: 49 %.\n'
     'Sumapaz es la única localidad donde no ganó: allí Gustavo Bolívar sacó 47,1 %. Mismo dibujo urbano de las figuras 5a y 5b.', A23['SUMAPAZ']['CARLOS FERNANDO GALAN PACHON'], '5c_mapa_galan.png')
# ---------- Google Trends: cuadrícula con leyenda de colores ----------
T = json.load(open(os.path.join(O, 'google_trends.json'), encoding='utf-8'))
NN = ['Carrillo', 'Oviedo', 'López', 'Valencia', 'Peñalosa']
CC = {'Carrillo': '#b5472f', 'Oviedo': '#d9a441', 'López': '#3d8a5a', 'Valencia': '#2f6f8f', 'Peñalosa': '#8a8378'}
A = T['comparacion_anual_colombia']['bogota_participacion_pct']; B = T['comparacion_ventana_mapa_colombia']['bogota_participacion_pct']
fig, axs = plt.subplots(1, 2, figsize=(8.6, 5.0))
for ax, v, tit in [(axs[0], A, 'Todo 2026 (1 ene - 11 nov)'), (axs[1], B, 'Segundo semestre (1 jun - 11 nov 2026)')]:
    orden = sorted(range(5), key=lambda i: -v[i])
    seq = []
    for i in orden:
        seq += [NN[i]] * v[i]
    seq = (seq + [NN[orden[-1]]] * 100)[:100]
    for k, n in enumerate(seq):
        ax.add_patch(plt.Circle((k % 10 + .5, 9 - k // 10 + .5), .4, color=CC[n]))
    for j, i in enumerate(orden):
        yy = -0.9 - j * 0.75
        ax.add_patch(plt.Circle((1.2, yy), .28, color=CC[NN[i]], clip_on=False))
        ax.text(1.7, yy, f'{NN[i]}: {v[i]} de cada 100', va='center', fontsize=9, color=TINTA, fontweight='bold' if NN[i] == 'Carrillo' else 'normal')
    ax.set_xlim(0, 10); ax.set_ylim(-4.6, 10); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(tit, fontsize=10, color=TINTA)
fig.suptitle('Búsquedas en Google hechas desde Bogotá: de cada 100 sobre los cinco precandidatos, cuántas son de cada uno', x=0.02, ha='left', fontsize=10.5, color=TINTA)
fig.text(0.02, 0.0, 'Google Trends, participación en la subregión Bogotá entre los cinco nombres comparados, consultado el 11 nov 2026. Cada punto = 1 búsqueda de cada 100.\n'
         'Medir búsquedas es medir curiosidad, no apoyo: los picos de Carrillo coinciden con sus polémicas (ver figura 1).', fontsize=7.2, color=GRIS)
fig.savefig(os.path.join(G, '3_trends_bogota.png'), dpi=220, bbox_inches='tight', facecolor='white'); plt.close(fig)
print('ok')

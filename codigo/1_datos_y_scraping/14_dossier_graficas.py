BASE = "."  # carpeta del proyecto
"""Gráficas del dossier de Carlos Carrillo (12 nov 2026)."""
import json, os, sys, unicodedata, collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
D = BASE
O = os.path.join(D, 'dossier_datos')
G = os.path.join(D, 'ENTREGA_DOSSIER', 'graficas'); os.makedirs(G, exist_ok=True)
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#555', 'axes.labelcolor': '#222', 'xtick.color': '#444', 'ytick.color': '#444'})
TINTA, GRIS, CLARO = '#1d1b18', '#8a8378', '#e9e4da'
COL = {'Pelea con un político': '#b5472f', 'Política nacional e izquierda': '#2f6f8f', 'Salida o gestión de la UNGRD': '#d9a441', 'Judicial o disciplinario': '#5b4a7a',
       'Aspiración 2027': '#3d8a5a', 'Bogotá y sus problemas': '#111111', 'Aparece de pasada': '#d8d2c6'}


def norm(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()


def guardar(fig, nombre):
    fig.savefig(os.path.join(G, nombre), dpi=220, bbox_inches='tight', facecolor='white')
    plt.close(fig)


# 1. Línea de vida del relato: búsquedas semanales de "Carlos Carrillo" y lo que publicó la prensa esa semana
T = json.load(open(os.path.join(O, 'google_trends.json'), encoding='utf-8'))
sem = [x.strip().rsplit(' ', 1) for x in T['carrillo_solo_colombia_semanal']['semanas'].split(';')]
etq = [a for a, _ in sem]; val = [int(b) for _, b in sem]
fig, ax = plt.subplots(figsize=(9.2, 3.9))
x = list(range(len(val)))
ax.fill_between(x, val, color='#cfd9e0', step='mid')
ax.step(x, val, where='mid', color='#2f6f8f', lw=1.4)
NOTAS = {'19 abr': 'Angie Rodríguez lo acusa\n(23 abr)', '7 jun': 'Suspensión (2 jun)\ny renuncia (9 jun)', '26 jul': 'Choques con Quintero\ny caso Guerrero', '23 ago': 'Rechaza la "gerente\npara Bogotá" (26 ago)',
         '13 sept': 'Pico sin hecho claro\nen la prensa', '4 oct': 'Camioneta de la UNP\n(5 oct)', '11 oct': 'Tribunal le ordena\nrectificar (13 oct)'}
alto = {'19 abr': 70, '7 jun': 80, '26 jul': 48, '23 ago': 86, '13 sept': 112, '4 oct': 74, '11 oct': 60}
for k, t in NOTAS.items():
    i = etq.index(k)
    col = '#111' if 'Bogotá' in t else TINTA
    ax.annotate(t, (i, val[i]), xytext=(i + {'11 oct': 2.2, '4 oct': 0.4, '23 ago': -1.8}.get(k, 0), alto[k]), ha='center', va='bottom', fontsize=7.6, color=col,
                fontweight='bold' if 'Bogotá' in t else 'normal', arrowprops=dict(arrowstyle='-', color=GRIS, lw=.7))
ax.axvspan(etq.index('31 may'), len(val) - 1, color='#f4efe6', zorder=0)
ax.text(etq.index('31 may') + .3, 126, 'Ventana del mapa de menciones (1 jun - 11 nov)', fontsize=7.5, color=GRIS)
ticks = [i for i, e in enumerate(etq) if e.split()[0] in ('4', '1', '5', '3', '7', '2', '6') and i % 4 == 1] or x[::4]
ax.set_xticks(x[1::4]); ax.set_xticklabels([etq[i] for i in x[1::4]], fontsize=8)
ax.set_ylim(0, 132); ax.set_ylabel('Interés relativo (máx. = 100)')
ax.set_title('Cuándo buscan a Carrillo: los picos coinciden con peleas, sanciones y una sola discusión sobre Bogotá', loc='left', fontsize=10.5, color=TINTA)
fig.text(0.01, -0.04, 'Google Trends, término "Carlos Carrillo", Colombia, semanas del 28 dic 2025 al 8 nov 2026, consultado el 11 nov 2026. Hechos: notas del corpus propio (487 notas).\n'
         'Google atribuye el tema principal a Carlos Carrillo Arenas (político); los homónimos casi no pesan. La escala es relativa (máximo de la serie = 100).', fontsize=7, color=GRIS)
guardar(fig, '1_linea_de_vida.png')

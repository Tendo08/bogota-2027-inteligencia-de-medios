BASE = "."  # carpeta del proyecto
"""Gráficas nuevas del dossier: red de propiedad, mapa de menciones por grupo dueño, mapas urbanos y escalera de localidades, relato frente a realidad."""
import json, os, sys, unicodedata, collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mc
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon as MPoly
from shapely.geometry import shape
D = BASE
O = os.path.join(D, 'dossier_datos')
G = os.path.join(D, 'ENTREGA_DOSSIER', 'graficas'); os.makedirs(G, exist_ok=True)
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
TINTA, GRIS, CLARO = '#1d1b18', '#8a8378', '#e9e4da'
COL = {'Pelea con un político': '#b5472f', 'Política nacional e izquierda': '#2f6f8f', 'Gestión o salida de la UNGRD': '#d9a441', 'Judicial o disciplinario': '#5b4a7a',
       'Aspiración 2027': '#3d8a5a', 'Bogotá y sus problemas': '#111111', 'Aparece de pasada': '#d8d2c6'}
L = json.load(open(os.path.join(O, 'carrillo_codificado.json'), encoding='utf-8'))
M = json.load(open(os.path.join(O, 'mapa_menciones_manual.json'), encoding='utf-8'))
N = collections.Counter(n['medio'] for n in L); NT = collections.Counter(n['medio'] for n in L if n['en_titular'])


def norm(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()


def guardar(fig, nombre):
    fig.savefig(os.path.join(G, nombre), dpi=220, bbox_inches='tight', facecolor='white'); plt.close(fig)


# ---------- 2. Red de propiedad ----------
GRUPOS = [
    ('Sarmiento Angulo\n(Grupo Aval)', '#8c6d1f', [('El Tiempo', 'El Tiempo'), ('Portafolio', 'Portafolio.co'), ('Citytv (Bogotá)', 'Citytv')]),
    ('Santo Domingo\n(Valorem)', '#2f6f8f', [('El Espectador', 'El Espectador'), ('Blu Radio', 'Blu Radio'), ('Noticias Caracol (TV)', 'Noticias Caracol')]),
    ('Ardila Lülle\n(OAL)', '#b5472f', [('La FM', 'La FM'), ('Noticias RCN', 'Noticias RCN')]),
    ('Gilinski', '#5b4a7a', [('Semana', 'Revista Semana')]),
    ('Prisa (España)', '#3d8a5a', [('Caracol Radio', 'Caracol Radio')]),
    ('Públicos', '#6b7a8f', [('RTVC Noticias', 'RTVC Noticias'), ('Radio Nacional', 'Radio Nacional de Colombia'), ('Canal Capital (Bogotá)', 'Canal Capital')]),
    ('Digitales e\nindependientes', '#9a948a', [('Infobae', 'Infobae'), ('La Silla Vacía', 'La Silla Vacía'), ('Cambio', 'CAMBIO Colombia'), ('Pulzo', 'Pulzo'), ('Al Punto', 'Al Punto'),
                                                ('Las2orillas', 'Las2orillas'), ('360 Radio', '360 Radio')]),
]
filas = sum(len(g[2]) for g in GRUPOS)
fig, ax = plt.subplots(figsize=(9.4, 9.0))
y = filas + len(GRUPOS) * 0.6
for dueno, col, medios in GRUPOS:
    y0 = y
    ys = []
    for nom, clave in medios:
        y -= 1; ys.append(y)
        n = N.get(clave, 0); t = NT.get(clave, 0)
        ax.add_patch(FancyBboxPatch((3.3, y - .36), 2.9, .72, boxstyle='round,pad=0.02,rounding_size=0.12', fc='white', ec=col, lw=1.2))
        ax.text(3.45, y, nom, va='center', fontsize=9, color=TINTA)
        ax.scatter([7.2], [y], s=max(n, .6) * 13, color=col, alpha=.85, zorder=3, edgecolors='white', lw=.6)
        ax.text(7.2 + (0.25 + (n ** .5) * .05), y, f'{n} notas' + (f' · {t} en titular' if n else ' · ninguna'), va='center', fontsize=8.6, color=TINTA if n else GRIS)
    yc = sum(ys) / len(ys)
    ax.add_patch(FancyBboxPatch((0, yc - .45), 2.5, .9, boxstyle='round,pad=0.02,rounding_size=0.15', fc=col, ec='none'))
    ax.text(1.25, yc, dueno, ha='center', va='center', fontsize=8.8, color='white', fontweight='bold')
    for yy in ys:
        ax.plot([2.5, 3.3], [yc, yy], color=col, lw=1, alpha=.7)
    y -= 0.6
ax.text(1.25, filas + len(GRUPOS) * .6 + .5, 'Dueño o grupo', ha='center', fontsize=9.5, color=GRIS, fontweight='bold')
ax.text(4.75, filas + len(GRUPOS) * .6 + .5, 'Medio', ha='center', fontsize=9.5, color=GRIS, fontweight='bold')
ax.text(7.2, filas + len(GRUPOS) * .6 + .5, 'Notas sobre Carrillo (12 nov 2025 - 11 nov 2026)', ha='left', fontsize=9.5, color=GRIS, fontweight='bold')
ax.set_xlim(-0.1, 11.5); ax.set_ylim(y, filas + len(GRUPOS) * .6 + 1); ax.axis('off')
ax.set_title('¿De quién son los medios que hablan de Carrillo? Los grandes grupos lo cubren; los canales de Bogotá, no', loc='left', fontsize=10.5, color=TINTA)
fig.text(0.01, 0.02, 'Propiedad: "Medios de comunicación y redes de poder en Colombia" (documento de síntesis, 11 nov 2026), que cita Media Ownership Monitor, CRC (2022) y García y Zambrano (2025).\n'
         'La propiedad no prueba que el dueño dicte cada nota. Conteo: corpus propio de 1.093 notas (Google News por sitio y API de medios). "Digitales" no implica un mismo dueño.', fontsize=7, color=GRIS)
guardar(fig, '2_red_propiedad.png')

# ---------- 3. Mapa de menciones: Semana (Gilinski), Caracol Radio (Prisa), El Tiempo (Aval, Bogotá) ----------
ORD = ['Revista Semana', 'Caracol Radio', 'El Tiempo']
NOMB = {'Revista Semana': 'Semana\nnacional · Gilinski', 'Caracol Radio': 'Caracol Radio\nnacional · Prisa', 'El Tiempo': 'El Tiempo\nde Bogotá · Grupo Aval'}
MESES = ['2025-11', '2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09', '2026-10', '2026-11']
MN = dict(zip(MESES, ['nov.*', 'dic.', 'ene.', 'feb.', 'mar.', 'abr.', 'may.', 'jun.', 'jul.', 'ago.', 'sep.', 'oct.', 'nov.*']))
SUB = [o for o in M if o['medio'] in ORD]
import math
ANCHO = {m: max(2, math.ceil(max(sum(1 for o in SUB if o['medio'] == md and o['fecha'].startswith(m)) for md in ORD) / 3)) for m in MESES}
fig, ax = plt.subplots(figsize=(10.5, 4.4))
x0 = 0; cortes = {}
for m in MESES:
    cortes[m] = x0; x0 += ANCHO[m] + 1
for r, med in enumerate(ORD):
    y0 = (len(ORD) - 1 - r) * 4.0
    for m in MESES:
        ns = sorted([o for o in SUB if o['medio'] == med and o['fecha'].startswith(m)], key=lambda o: (o['codigo'] == 'X', o['fecha']))
        for j, o in enumerate(ns):
            ax.add_patch(Rectangle((cortes[m] + j % ANCHO[m], y0 + 2.6 - (j // ANCHO[m])), .86, .86, color=COL[o['encuadre']], lw=0))
    tot = [o for o in SUB if o['medio'] == med]
    ax.text(-0.6, y0 + 2.6, NOMB[med] + f"\n{sum(o['codigo'] != 'X' for o in tot)} sobre él, {sum(o['codigo'] == 'X' for o in tot)} de pasada", ha='right', va='center', fontsize=8.4, color=TINTA)
for m in MESES:
    ax.text(cortes[m], 12.0, MN[m], fontsize=7.6, color=GRIS)
    if m != MESES[0]:
        ax.plot([cortes[m] - .55] * 2, [-0.4, 11.8], color=CLARO, lw=.8)
ax.set_xlim(-0.5, x0); ax.set_ylim(-0.6, 12.6); ax.axis('off')
cn = collections.Counter(o['encuadre'] for o in SUB)
ax.legend([Rectangle((0, 0), 1, 1, color=c) for c in COL.values()], [f'{k} ({cn[k]})' for k in COL], loc='upper center', bbox_to_anchor=(.5, -0.02), ncol=4, fontsize=7.8, frameon=False, handlelength=1, handleheight=1)
ax.set_title(f'Mapa de menciones en 12 meses, tres dueños distintos: ninguna de las {len(SUB)} notas trata un problema de Bogotá', loc='left', fontsize=10.5, color=TINTA)
fig.text(0.01, -0.1, 'Cada cuadro es una nota que nombra a Carrillo (12 nov 2025 - 11 nov 2026; * = medio mes). Encuadre asignado a mano leyendo titular y entrada. Hasta el 2 de junio era director de la UNGRD.\n'
         'El Tiempo no dejó leer el cuerpo de sus notas: se codificó por titular. En Citytv y Canal Capital la búsqueda no encontró notas sobre él. Ningún cuadro es negro (Bogotá).', fontsize=7, color=GRIS)
guardar(fig, '3_mapa_menciones.png')

# ---------- 5. Mapas urbanos con las 19 localidades numeradas ----------
URB = json.load(open(os.path.join(O, 'localidades_urbanas.json'), encoding='utf-8'))
LOC = {o['nombre']: o for o in json.load(open(os.path.join(D, 'mapa_localidades.json'), encoding='utf-8'))}
V26 = {}
for a in json.load(open(os.path.join(D, 'fuentes_primarias', 'registraduria', 'presidente_2026_localidad.json'), encoding='utf-8')):
    V26[{'CANDELARIA': 'LA CANDELARIA', 'MARTIRES': 'LOS MARTIRES', 'RAFAEL URIBE URIB': 'RAFAEL URIBE URIBE', '': 'SIN'}.get(a['L'], a['L'])] = a
NUM = ['Usaquén', 'Chapinero', 'Santa Fe', 'San Cristóbal', 'Usme', 'Tunjuelito', 'Bosa', 'Kennedy', 'Fontibón', 'Engativá', 'Suba', 'Barrios Unidos', 'Teusaquillo', 'Los Mártires',
       'Antonio Nariño', 'Puente Aranda', 'La Candelaria', 'Rafael Uribe Uribe', 'Ciudad Bolívar', 'Sumapaz']
POB = {n: LOC[n]['pobreza'] for n in NUM if LOC[n]['pobreza'] is not None}; POB['Sumapaz'] = 11.39
CEP = {n: V26[norm(n)]['Cepeda'] for n in NUM}
AJUSTE = {'La Candelaria': (0.004, 0.0), 'Los Mártires': (-0.002, 0.0), 'Antonio Nariño': (0.0, -0.002), 'Santa Fe': (-0.004, 0.012), 'Ciudad Bolívar': (0.004, 0.022), 'Tunjuelito': (0.0, 0.004), 'Chapinero': (-0.012, 0.0), 'Usaquén': (-0.01, 0.0), 'San Cristóbal': (-0.006, 0.0)}
fig, axs = plt.subplots(1, 2, figsize=(8.8, 6.9))
fig.subplots_adjust(top=0.93, wspace=0.02)
for ax, dic, cmap, tit, lim in [(axs[0], POB, 'Oranges', 'Pobreza monetaria, zona urbana (%)', (0, 40)), (axs[1], CEP, 'Blues', 'Voto por Cepeda, 1.ª vuelta 2026 (%)', (20, 62))]:
    nm = mc.Normalize(*lim); cm = plt.get_cmap(cmap)
    for n in NUM[:-1]:
        g = shape(URB[n]); v = dic[n]
        polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
        for p in polys:
            ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=cm(nm(v)), ec='white', lw=.8))
        c = g.representative_point(); dx, dy = AJUSTE.get(n, (0, 0))
        ax.text(c.x + dx, c.y + dy, f'{NUM.index(n) + 1}\n{v:.0f}'.replace('.', ','), ha='center', va='center', fontsize=6.6, color='#111' if nm(v) < .62 else 'white', fontweight='bold', linespacing=.9)
    ax.set_xlim(-74.225, -73.99); ax.set_ylim(4.465, 4.84); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(tit, fontsize=10, color=TINTA)
    sm = plt.cm.ScalarMappable(norm=nm, cmap=cm); cb = fig.colorbar(sm, ax=ax, orientation='horizontal', fraction=.035, pad=.01); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7)
leyenda = '   '.join(f'{i + 1} {n}' for i, n in enumerate(NUM[:-1]))
fig.suptitle('Las 19 localidades urbanas: donde hay más pobreza, más votó la izquierda (número de localidad y valor)', x=0.02, ha='left', fontsize=10.5, color=TINTA)
import textwrap
fig.text(0.02, 0.035, '\n'.join(textwrap.wrap(leyenda, 175)), fontsize=7, color=TINTA)
fig.text(0.02, -0.01, 'Pobreza: DANE-SDP, Encuesta Multipropósito 2025, cuadro 216A (localidad urbana). Voto: Registraduría, escrutinio por mesa, suma propia. Geometría: UPZ de la Secretaría de Seguridad (SCJ),\n'
         'unidas por localidad; se excluyen las zonas rurales (UPR), por eso Usme y Ciudad Bolívar se ven de su tamaño urbano. 20 Sumapaz es rural: pobreza 11,4 % (cuadro 216B), Cepeda 76,4 % (2.179 votos).', fontsize=6.8, color=GRIS)
guardar(fig, '5_mapas_localidades.png')

# ---------- 6. Escalera: las 20 localidades ordenadas por pobreza ----------
orden = sorted(NUM, key=lambda n: POB[n])
fig, ax = plt.subplots(figsize=(8.8, 6.4))
for i, n in enumerate(orden):
    ax.plot([POB[n], CEP[n]], [i, i], color=CLARO, lw=2.2, zorder=1)
    ax.scatter(POB[n], i, s=46, color='#d9772b', zorder=3); ax.scatter(CEP[n], i, s=46, color='#2f6f8f', zorder=3)
    et = f'{NUM.index(n) + 1}. {n}' + (' (rural)' if n == 'Sumapaz' else '')
    ax.text(-2, i, et, ha='right', va='center', fontsize=8.6, color=TINTA)
    ax.text(101, i, '0', ha='center', va='center', fontsize=8.6, color='#b5472f', fontweight='bold')
ax.text(101, len(orden) - 0.1, 'Notas que lo\nubican aquí', ha='center', va='bottom', fontsize=7.8, color='#b5472f')
ax.set_xlim(0, 106); ax.set_ylim(-0.8, len(orden) + 1.2); ax.set_yticks([])
ax.set_xticks([0, 20, 40, 60, 80]); ax.set_xlabel('%', fontsize=8); ax.spines['left'].set_visible(False)
ax.scatter([], [], color='#d9772b', label='Pobreza monetaria (%)'); ax.scatter([], [], color='#2f6f8f', label='Voto por Cepeda 2026 (%)')
ax.legend(loc='lower right', bbox_to_anchor=(.93, 0.0), fontsize=8, frameon=False)
ax.set_title('Las 20 localidades, de menor a mayor pobreza: el voto de izquierda sube con la pobreza y la prensa no pone a Carrillo en ninguna', loc='left', fontsize=10, color=TINTA)
fig.text(0.01, -0.03, 'Mismas fuentes de la figura anterior. La columna roja cuenta las notas del corpus (1.093) en las que una localidad aparece en la misma oración que Carrillo o en la siguiente.\n'
         'La relación entre pobreza y voto es un patrón territorial, no una causa, y el voto es de Cepeda, no de Carrillo.', fontsize=7, color=GRIS)
guardar(fig, '6_escalera_localidades.png')

# ---------- 7. Relato frente a realidad (96 notas codificadas a mano en cinco medios) ----------
REAL = [('Salud', 57.7), ('Educación', 44.7), ('Empleo', 38.2), ('Seguridad', 37.5), ('Pobreza', 33.6), ('Movilidad', 18.2)]
c = collections.Counter(o['encuadre'] for o in M if o['codigo'] != 'X'); tot = sum(c.values())
RELATO = [(k, c[k]) for k in ['Gestión o salida de la UNGRD', 'Pelea con un político', 'Judicial o disciplinario', 'Política nacional e izquierda', 'Aspiración 2027', 'Bogotá y sus problemas']]
fig, ax = plt.subplots(figsize=(9.2, 4.1))
for i, (k, v) in enumerate(REAL):
    ax.barh(5 - i, -v, color='#a89f91', height=.62)
    ax.text(-v - 1.5, 5 - i, f'{k}  {v:.1f} %'.replace('.', ','), ha='right', va='center', fontsize=8.6, color=TINTA)
for i, (k, v) in enumerate(RELATO):
    p = 100 * v / tot
    ax.barh(5 - i, p, color=COL[k], height=.62)
    ax.text(p + 1.5, 5 - i, f'{k}  {v} de {tot}', ha='left', va='center', fontsize=8.6, color=TINTA)
ax.axvline(0, color=TINTA, lw=.8); ax.set_xlim(-95, 95); ax.set_yticks([]); ax.set_xticks([]); ax.spines['left'].set_visible(False); ax.spines['bottom'].set_visible(False)
ax.text(-48, 6.05, 'Lo que los bogotanos piden priorizar\n(% que lo menciona, hasta 3 respuestas)', ha='center', fontsize=9, color=TINTA, fontweight='bold')
ax.text(48, 6.05, 'De qué tratan las notas sobre Carrillo', ha='center', fontsize=9, color=TINTA, fontweight='bold')
ax.set_ylim(-0.6, 7)
fig.text(0.01, -0.05, 'Izquierda: Bogotá Cómo Vamos, Encuesta de Percepción Ciudadana 2025. Derecha: Semana, Caracol Radio y El Tiempo (12 nov 2025 - 11 nov 2026), sin las notas que lo nombran de pasada.\n'
         'Las dos columnas no son la misma medida: una es lo que pide la gente y la otra de qué hablan las notas. Lo que importa es que no se tocan.', fontsize=7, color=GRIS)
guardar(fig, '7_relato_realidad.png')
print('ok', tot, dict(c))

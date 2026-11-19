BASE = "."  # carpeta del proyecto
"""Figura 9: Galán 2023 frente a la izquierda (Bolívar 2023, Cepeda 2026) por localidad.
Figura 10: de quién se habla en las notas sobre Carrillo (agenda nacional frente a Bogotá)."""
import json, os, re, sys, unicodedata
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D = BASE; O = os.path.join(D, 'dossier_datos'); G = os.path.join(D, 'ENTREGA_DOSSIER', 'graficas')
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
TINTA, GRIS, CLARO = '#1d1b18', '#6f685e', '#e9e4da'


def norm(s):
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()


R = os.path.join(D, 'fuentes_primarias', 'registraduria')
A23 = {norm(a['L']): a for a in json.load(open(os.path.join(R, 'alcaldia_2023_localidad.json'), encoding='utf-8')) if a['L'] != 'Nacional'}
V26 = {}
for a in json.load(open(os.path.join(R, 'presidente_2026_localidad.json'), encoding='utf-8')):
    V26[{'CANDELARIA': 'LA CANDELARIA', 'MARTIRES': 'LOS MARTIRES', 'RAFAEL URIBE URIB': 'RAFAEL URIBE URIBE'}.get(a['L'], a['L'])] = a
LOC = {o['nombre']: o for o in json.load(open(os.path.join(D, 'mapa_localidades.json'), encoding='utf-8'))}
POB = {n: (LOC[n]['pobreza'] if LOC[n]['pobreza'] is not None else 11.39) for n in LOC}
filas = sorted(LOC, key=lambda n: POB[n])
gan = sum(1 for n in filas if A23[norm(n)]['CARLOS FERNANDO GALAN PACHON'] > max(v for k, v in A23[norm(n)].items() if k not in ('L', 'pobreza', 'votos validos', 'CARLOS FERNANDO GALAN PACHON')))
fig, ax = plt.subplots(figsize=(9.2, 6.6))
for i, n in enumerate(filas):
    g = A23[norm(n)]['CARLOS FERNANDO GALAN PACHON']; b = A23[norm(n)]['GUSTAVO BOLIVAR MORENO']; c = V26[norm(n)]['Cepeda']
    ax.plot([min(g, b, c), max(g, b, c)], [i, i], color=CLARO, lw=2.2, zorder=1)
    ax.scatter(g, i, s=52, color='#d9a441', zorder=3, edgecolors='white', lw=.6)
    ax.scatter(b, i, s=52, color='#b5472f', zorder=3, edgecolors='white', lw=.6)
    ax.scatter(c, i, s=52, color='#2f6f8f', zorder=3, edgecolors='white', lw=.6, marker='D')
    ax.text(-1.5, i, f'{n}' + (' (rural)' if n == 'Sumapaz' else '') + f'  ·  {POB[n]:.0f} %'.replace('.', ','), ha='right', va='center', fontsize=8.4, color=TINTA)
ax.text(-1.5, len(filas) + .1, 'Localidad  ·  pobreza', ha='right', va='bottom', fontsize=8, color=GRIS)
ax.set_xlim(0, 82); ax.set_ylim(-0.8, len(filas) + 1); ax.set_yticks([]); ax.spines['left'].set_visible(False)
ax.set_xticks([0, 20, 40, 60, 80]); ax.set_xlabel('% de los votos válidos', fontsize=8.5)
ax.scatter([], [], s=52, color='#d9a441', label='Galán, Alcaldía 2023'); ax.scatter([], [], s=52, color='#b5472f', label='Bolívar (izquierda), Alcaldía 2023')
ax.scatter([], [], s=52, color='#2f6f8f', marker='D', label='Cepeda (izquierda), Presidencia 2026')
ax.legend(loc='lower right', fontsize=8, frameon=False)
ax.set_title(f'En 2023 Galán ganó {gan} de las 20 localidades, también el sur; en 2026 el sur votó por la izquierda nacional', loc='left', fontsize=10.2, color=TINTA)
fig.text(0.01, -0.03, 'Registraduría, escrutinio por mesa, Alcaldía de Bogotá 2023 y 1.ª vuelta presidencial 2026, sumas propias por localidad. Localidades ordenadas de menor a mayor pobreza urbana\n'
         '(DANE-SDP, Multipropósito 2025). Bolívar solo ganó en Sumapaz. El voto de la izquierda en el sur es nacional, no se trasladó a la elección de alcalde en 2023.', fontsize=7, color=GRIS)
fig.savefig(os.path.join(G, '9_galan_2023.png'), dpi=220, bbox_inches='tight', facecolor='white'); plt.close(fig)

L = json.load(open(os.path.join(O, 'carrillo_codificado.json'), encoding='utf-8'))
n = len(L)
TEMAS = [('Gustavo Petro', r'\bPetro\b', '#2f6f8f'), ('Abelardo de la Espriella', r'Espriella|Abelardo', '#2f6f8f'), ('Angie Rodríguez', r'Angie Rodr', '#2f6f8f'),
         ('Iván Cepeda', r'Cepeda', '#2f6f8f'), ('Carlos Fernando Galán (alcalde)', r'Gal[aá]n\b', '#b5472f'), ('Inseguridad', r'inseguridad', '#b5472f')]
vals = [(k, 100 * sum(1 for x in L if re.search(rx, x['titulo'] + ' ' + (x.get('texto') or ''), re.I)) / n, c) for k, rx, c in TEMAS]
fig, ax = plt.subplots(figsize=(9.2, 3.8))
for i, (k, v, c) in enumerate(vals):
    ax.barh(len(vals) - 1 - i, v, color=c, height=.62)
    ax.text(v + 1, len(vals) - 1 - i, f'{v:.0f} %', va='center', fontsize=9.5, color=TINTA)
ax.set_yticks(range(len(vals))); ax.set_yticklabels([k for k, _, _ in vals][::-1], fontsize=9.5)
ax.set_xticks([]); ax.spines['bottom'].set_visible(False); ax.set_xlim(0, 80)
ax.set_title('En las notas que nombran a Carrillo, la agenda es nacional: Petro aparece en 2 de cada 3; Galán, en 2 de cada 100', loc='left', fontsize=10.2, color=TINTA)
fig.text(0.01, -0.06, f'Porcentaje de las {n:,} notas del corpus (12 nov 2025 - 11 nov 2026) que nombran a cada persona o tema en el titular o el texto. Azul: agenda nacional; rojo: Bogotá.'.replace(',', '.'), fontsize=7, color=GRIS)
fig.savefig(os.path.join(G, '10_agenda_nacional.png'), dpi=220, bbox_inches='tight', facecolor='white'); plt.close(fig)
print(gan, [(k, round(v)) for k, v, _ in vals])

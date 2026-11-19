BASE = "."  # carpeta del proyecto
"""Figura: una entrevista, dos noticias. La entrevista de Me Vale (Eva Rey, 14-15 jun 2026) tuvo dos frases:
'se va a incendiar el país' y su aspiración a la Alcaldía ('soy un hombre libre'). ¿Cuántas notas sacó cada una y en qué medios?"""
import json, os, re, sys, collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D = BASE; O = os.path.join(D, 'dossier_datos'); G = os.path.join(D, 'ENTREGA_DOSSIER', 'graficas')
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
TINTA, GRIS = '#1d1b18', '#6f685e'
L = json.load(open(os.path.join(O, 'carrillo_codificado.json'), encoding='utf-8'))
inc, alc = [], []
for n in L:
    if not ('2026-06-14' <= n['fecha'] <= '2026-07-05'):
        continue
    t = (n['titulo'] + ' ' + (n.get('texto') or '')).lower()
    if re.search(r'incendiar|se va a incendiar|incendia el pa', t) and 'carrillo' in t:
        inc.append(n)
    if re.search(r'hombre libre|alcald[ií]a de bogot', t) and re.search(r'eva rey|me vale|desn[uú]date', t):
        alc.append(n)
DUENO = {'Revista Semana': 'Semana (Gilinski)', 'Infobae': 'Infobae', 'La Silla Vacía': 'La Silla Vacía', 'Pulzo': 'Pulzo', 'ELHERALDO.CO': 'El Heraldo', 'El Colombiano': 'El Colombiano',
         'Blu Radio': 'Blu Radio (Santo Domingo)', 'Noticias Caracol': 'Noticias Caracol (Santo Domingo)', 'Caracol Radio': 'Caracol Radio (Prisa)', 'El Tiempo': 'El Tiempo (Grupo Aval)',
         'El Espectador': 'El Espectador (Santo Domingo)', 'La FM': 'La FM (Ardila Lülle)'}
ci = collections.Counter(n['medio'] for n in inc)
filas = ['Revista Semana', 'Infobae', 'La Silla Vacía', 'Pulzo', 'ELHERALDO.CO', 'El Colombiano', 'Blu Radio', 'Noticias Caracol', 'El Espectador', 'La FM', 'Caracol Radio', 'El Tiempo']
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 4.4), gridspec_kw={'width_ratios': [1, 1.6]})
fig.subplots_adjust(wspace=0.75)
a1.bar([0, 1], [len(inc), len(alc)], color=['#b5472f', '#3d8a5a'], width=.6)
for x, v in [(0, len(inc)), (1, len(alc))]:
    a1.text(x, v + 1, str(v), ha='center', fontsize=12, color=TINTA, fontweight='bold')
a1.set_xticks([0, 1]); a1.set_xticklabels(['"Se va a incendiar\nel país"', '"Soy un hombre libre"\n(Alcaldía 2027)'], fontsize=9)
a1.set_yticks([]); a1.spines['left'].set_visible(False); a1.set_ylim(0, len(inc) * 1.15)
a1.set_title('Notas que reprodujeron cada frase', fontsize=10, color=TINTA)
for i, m in enumerate(filas):
    v = ci.get(m, 0)
    a2.barh(len(filas) - 1 - i, v, color='#b5472f' if v else '#d8d2c6', height=.62)
    a2.text(v + .3, len(filas) - 1 - i, str(v) if v else '0 (la búsqueda no halló notas)', va='center', fontsize=8.4, color=TINTA if v else GRIS)
a2.set_yticks(range(len(filas))); a2.set_yticklabels([DUENO.get(m, m) for m in filas][::-1], fontsize=8.6)
a2.set_xticks([]); a2.spines['bottom'].set_visible(False)
a2.set_title('"Incendiar el país": notas por medio', fontsize=10, color=TINTA)
fig.suptitle('Una entrevista, dos noticias: la frase de choque se volvió noticia nacional; su aspiración a Bogotá, casi nada', x=0.01, ha='left', fontsize=10.5, color=TINTA)
fig.text(0.01, -0.06, f'Entrevista en el programa digital Me Vale, de Eva Rey (clip publicado el 15 jun 2026). Notas del corpus entre el 14 de junio y el 5 de julio: {len(inc)} notas en {len(ci)} medios citan la frase de incendiar\n'
         f'el país; {len(alc)} notas (Semana, 16 jun; Infobae, 17 jun) recogen su aspiración a la Alcaldía. El Tiempo solo se pudo leer por titular. Conteo propio; un cero quiere decir que la búsqueda no encontró notas.', fontsize=7, color=GRIS)
fig.savefig(os.path.join(G, '8_una_entrevista.png'), dpi=220, bbox_inches='tight', facecolor='white'); plt.close(fig)
print(len(inc), len(alc), ci.most_common())

BASE = "."  # carpeta del proyecto
"""Láminas de fotos para el dossier (recortes a la misma proporción, con nombre y crédito)."""
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
D = BASE
F = os.path.join(D, 'ENTREGA_DOSSIER', 'fotos'); G = os.path.join(D, 'ENTREGA_DOSSIER', 'graficas')
C = json.load(open(os.path.join(F, 'creditos.json'), encoding='utf-8'))
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif']})
GRIS = '#6f685e'


def recorte(img, prop, arriba=0.0):
    h, w = img.shape[:2]
    if w / h > prop:
        nw = int(h * prop); x = (w - nw) // 2; return img[:, x:x + nw]
    nh = int(w / prop); y = int((h - nh) * arriba); return img[y:y + nh, :]


def lamina(items, nombre, prop, ancho, alto, credito_y=-0.02, titulo=None):
    fig, axs = plt.subplots(1, len(items), figsize=(ancho, alto))
    for ax, (k, etiqueta, arriba) in zip(axs, items):
        im = mpimg.imread(os.path.join(F, C[k]['archivo']))
        ax.imshow(recorte(im, prop, arriba)); ax.axis('off')
        ax.set_title(etiqueta, fontsize=9.5, pad=4, loc='left')
    cred = ' · '.join(f"{e.split(chr(10))[0]}: {C[k]['autor'][:45]} ({C[k]['licencia']})" for k, e, _ in items)
    if titulo:
        fig.suptitle(titulo, x=0.01, ha='left', fontsize=10.5, y=1.02)
    fig.text(0.01, credito_y, 'Fotos: Wikimedia Commons. ' + cred, fontsize=6.3, color=GRIS, wrap=True)
    fig.savefig(os.path.join(G, nombre), dpi=200, bbox_inches='tight', facecolor='white'); plt.close(fig)


lamina([('carrillo', 'Carlos Carrillo', 0.1), ('oviedo', 'Juan Daniel Oviedo', 0.05), ('lopez', 'Claudia López', 0.1), ('valencia', 'Paloma Valencia', 0.1), ('penalosa', 'Enrique Peñalosa', 0.1)],
       'A_cinco_precandidatos.png', 0.8, 9.2, 2.35)
lamina([('carrillo_concejal', 'Concejal de Bogotá (2023)', 0.15), ('carrillo_ungrd', 'Posesión en la UNGRD (mar. 2024)', 0.2), ('carrillo', 'Director de la UNGRD (2024-2026)', 0.1)],
       'B_trayectoria_carrillo.png', 1.0, 9.0, 3.0)
lamina([('usme', 'Usme: 37,5 % de pobreza urbana', 0.3), ('tunjuelo', 'Río Tunjuelo hacia Ciudad Bolívar', 0.3), ('transmicable', 'TransMiCable, Ciudad Bolívar', 0.3)],
       'C_el_sur.png', 1.35, 9.2, 2.35)
lamina([('transmilenio', 'TransMilenio, Av. Caracas', 0.4), ('bosa', 'Bosa: 32,7 % de pobreza urbana', 0.4)], 'D_ciudad.png', 1.5, 7.5, 2.4)
print(os.listdir(G))

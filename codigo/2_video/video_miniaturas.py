"""Miniaturas de los productos del proyecto para la escena 17 (portadas de PDF y cuadros del video)."""
import os, shutil, subprocess, sys
import fitz, imageio_ffmpeg
D = os.path.dirname(os.path.abspath(__file__)); FV = os.path.join(D, 'ENTREGA_VIDEO', 'fotos'); B = os.path.dirname(D)
pdfs = {'mini_dossier.png': (os.path.join(D, 'ENTREGA_DOSSIER', 'Dossier_Carlos_Carrillo_Diego_Umbarila_v3.pdf'), 0),
        'mini_fichas.png': (os.path.join(D, 'ENTREGA_JUEVES', 'Fichas_Precandidatos_Bogota_2027_Diego_Umbarila.pdf'), 0),
        'mini_presentacion.png': (os.path.join(D, 'ENTREGA_JUEVES', 'Presentacion_Bogota_2027_Diego_Umbarila.pdf'), 0),
        'mini_gaza.png': (os.path.join(B, 'Gaza', 'informe', 'Informe_Gaza_Diego_Umbarila_FINAL.pdf'), 0),
        'mini_lula.png': (os.path.join(B, 'Brasil_Lula', 'Avance_Lula_Diego_Umbarila.pdf'), 0)}
for n, (p, pg) in pdfs.items():
    doc = fitz.open(p); doc[pg].get_pixmap(dpi=110).save(os.path.join(FV, n)); print(n, doc.page_count, 'págs')
VID = os.path.join(D, 'ENTREGA_VIDEO', 'Video_Carrillo_Bogota2027_Diego_Umbarila.mp4')
for n, t in {'mini_mapa_zonas.png': 704, 'mini_dolencias.png': 170, 'mini_juego.png': 330}.items():
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-ss', str(t), '-i', VID, '-frames:v', '1', os.path.join(FV, n)])
    print(n)

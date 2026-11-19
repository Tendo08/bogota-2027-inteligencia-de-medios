"""Vuelve a renderizar todas las animaciones con la misma duración que ya tenían (para aplicar arreglos generales)."""
import os, sys, re, subprocess
sys.argv = [sys.argv[0]]
import video_anim as VA, imageio_ffmpeg
saltar = {'17_metodo'}
for n in VA.ESCENAS:
    if n in saltar:
        continue
    p = os.path.join(VA.ESC, n + '.mp4')
    if not os.path.exists(p):
        print('sin archivo previo, salto', n); continue
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-i', p], capture_output=True, text=True).stderr
    h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r).groups()
    VA.render(n, objetivo=int(h) * 3600 + int(m) * 60 + float(s))

BASE = "."  # carpeta del proyecto
"""Anexo en Excel del dossier: corpus, mapa de menciones codificado a mano, Google Trends y rastro de búsqueda."""
import json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
D = BASE
O = os.path.join(D, 'dossier_datos')
L = json.load(open(os.path.join(O, 'carrillo_codificado.json'), encoding='utf-8'))
M = json.load(open(os.path.join(O, 'mapa_menciones_manual.json'), encoding='utf-8'))
T = json.load(open(os.path.join(O, 'google_trends.json'), encoding='utf-8'))
B0 = json.load(open(os.path.join(O, 'carrillo_bruto.json'), encoding='utf-8'))
B = json.load(open(os.path.join(O, 'carrillo_bruto_12m.json'), encoding='utf-8'))
wb = Workbook()
CAB = PatternFill('solid', fgColor='E9E4DA')


def hoja(ws, cab, filas, anchos):
    ws.append(cab)
    for c in ws[1]:
        c.font = Font(bold=True); c.fill = CAB; c.alignment = Alignment(wrap_text=True, vertical='top')
    for f in filas:
        ws.append(f)
    for i, a in enumerate(anchos):
        ws.column_dimensions[chr(65 + i)].width = a
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = ws.dimensions


ws = wb.active; ws.title = 'Leídas a mano (' + str(len(M)) + ')'
hoja(ws, ['Medio', 'Fecha', 'Titular', 'Encuadre (codificado a mano)', 'Lo nombra en el titular', 'Lectura', 'URL'],
     [[o['medio'], o['fecha'], o['titulo'], o['encuadre'], 'Sí' if o['en_titular'] else 'No', o['lectura'], o['url']] for o in sorted(M, key=lambda x: (x['medio'], x['fecha']))], [16, 11, 80, 28, 12, 12, 60])
ws = wb.create_sheet('Corpus (' + str(len(L)) + ')')
hoja(ws, ['Fecha', 'Medio', 'Titular', 'Lo nombra en el titular', 'Veces que lo nombra en el texto', 'Encuadre (automático)', 'Localidades en la nota', 'URL'],
     [[n['fecha'], n['medio'], n['titulo'], 'Sí' if n['en_titular'] else 'No', n['menciones'], n['principal'], ', '.join(n['localidades_nota']), n['url_real']] for n in sorted(L, key=lambda x: x['fecha'])],
     [11, 18, 80, 12, 12, 26, 20, 60])
ws = wb.create_sheet('Google Trends')
ws.append([T['fuente']]); ws.append([])
ws.append(['Participación en búsquedas desde Bogotá (%)', 'Carrillo', 'Oviedo', 'López', 'Valencia', 'Peñalosa'])
ws.append(['1 ene - 11 nov 2026'] + T['comparacion_anual_colombia']['bogota_participacion_pct'])
ws.append(['1 jun - 11 nov 2026'] + T['comparacion_ventana_mapa_colombia']['bogota_participacion_pct'])
ws.append([]); ws.append(['Semana', 'Interés por "Carlos Carrillo" en Colombia (máx. = 100)'])
for x in T['carrillo_solo_colombia_semanal']['semanas'].split(';'):
    a, b = x.strip().rsplit(' ', 1); ws.append([a, int(b)])
R = T['carrillo_12_meses_colombia']
ws.append([]); ws.append(['Últimos 12 meses (Colombia): ' + R['enlace']])
for k2 in ['temas_principales', 'consultas_principales', 'consultas_en_ascenso', 'subregiones']:
    ws.append([k2.replace('_', ' ').capitalize()])
    for a2, b2 in R[k2].items():
        ws.append([a2, b2])
for c in ws[3]:
    c.font = Font(bold=True)
ws.column_dimensions['A'].width = 42
ws = wb.create_sheet('Rastro de búsqueda')
ws.append(['Primer barrido (1 jun - 11 nov 2026): ' + str(len(B0['consultas'])) + ' consultas a Google News']); ws['A1'].font = Font(bold=True)
for q in B0['consultas']:
    ws.append([q])
ws.append([]); ws.append(['Segundo barrido, ampliación a 12 meses (12 nov 2025 - 11 nov 2026): ' + str(len(B['consultas'])) + ' consultas'])
for q in B['consultas']:
    ws.append([q])
ws.append([]); ws.append(['También: API de La Silla Vacía, 360 Radio, Las2orillas, Razón Pública y Al Punto (búsqueda "Carlos Carrillo").'])
ws.append(['Medios locales revisados sin notas sobre él en la ventana: Q\'hubo Bogotá y Región Capital (API del medio); Citytv y Canal Capital (búsqueda sin resultados).'])
ws.append(['Depuración (12 meses): 1.691 resultados; se quitaron 519 que no lo nombran en el texto, 60 de homónimos, 16 de medios ajenos y 3 repetidos; quedan 1.093 notas de 85 medios.'])
ws.column_dimensions['A'].width = 110
ruta = os.path.join(D, 'ENTREGA_DOSSIER', 'Anexo_Corpus_Carrillo_Diego_Umbarila.xlsx')
wb.save(ruta); print(ruta)

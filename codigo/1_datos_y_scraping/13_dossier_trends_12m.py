BASE = "."  # carpeta del proyecto
import json, os
D = BASE; f = os.path.join(D, 'dossier_datos', 'google_trends.json')
T = json.load(open(f, encoding='utf-8'))
T['carrillo_12_meses_colombia'] = {
 'enlace': 'https://trends.google.com/trends/explore?date=today%2012-m&geo=CO&q=Carlos%20Carrillo (consultado el 11-nov-2026)',
 'nota': 'La serie semanal coincide con la de enero-noviembre; antes de 2026 solo hay un pico menor en diciembre de 2025 (13).',
 'temas_principales': {'Carlos Carrillo Arenas (Político colombiano)': 100, 'Abelardo de la Espriella': 3, 'Gustavo Petro': 3, 'UNGRD (tema)': 1, 'Entrevista periodística (tema)': 1, 'Juan Carlos Carrillo (boxeador)': 0, 'Centro Democrático': 0, 'Fernando Carrillo (actor)': 0},
 'consultas_principales': {'carlos carrillo arenas': 100, 'abelardo de la espriella': 4, 'ungrd': 3, 'carlos carrillo ungrd': 3, 'juan carlos carrillo': 3, 'quien es carlos carrillo': 2, 'gustavo petro': 2, 'fernando carrillo': 1, 'juliana guerrero': 1, 'luz adriana camargo': 1},
 'consultas_en_ascenso': {'abelardo de la espriella': 'aumento puntual', 'juliana guerrero': 'aumento puntual', 'reforma': 'aumento puntual', 'carlos carrillo arenas': '+1.150 %', 'quien es carlos carrillo': '+130 %'},
 'subregiones': {'Bogotá': 100, 'Cundinamarca': 92, 'Caldas': 91, 'Tolima': 90, 'Santander': 89, 'Boyacá': 87, 'Antioquia': 83}}
json.dump(T, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')

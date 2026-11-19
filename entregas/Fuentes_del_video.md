# Fuentes del video ensayo: Carlos Carrillo, Bogotá 2027

Diego Umbarila · Sociología de la Información y los Medios · Docente: Sebastián Peña Pérez
Lista viva: se actualiza cada vez que entra algo nuevo al video. Última actualización: 17-nov-2026.

## 1. Datos (fuentes primarias, recogidas por scraping, API o descarga)

| Dato en el video | Fuente | Cómo se obtuvo | Enlace / referencia |
|---|---|---|---|
| Corpus de 1.093 notas de 85 medios (12-nov-2025 a 11-nov-2026) | Google News y API de medios | Scraping propio (corpus del proyecto) | Archivos del proyecto |
| Aprobación del alcalde 26 %; percepción de inseguridad 62 % (récord desde 2008) | Bogotá Cómo Vamos, Encuesta de Percepción Ciudadana 2025 (n=1.520, campo 7-29 oct 2025, error ±3 %) | PDF descargado | bogotacomovamos.org |
| Extorsión 589 → 1.639 casos (ene-sep, 2018 vs. 2026); homicidios ene-sep 2018-2026; homicidios por localidad | Secretaría Distrital de Seguridad, Convivencia y Justicia, capa "Delitos Alto Impacto Localidad", corte 30-sep-2026 | Consulta a la capa de datos (API ArcGIS) | https://oaiee.scj.gov.co/agc/rest/services/Tematicos_Pub/CifrasSCJ/MapServer/0 |
| Hurto a personas: Suba, Engativá y Kennedy, las de más casos; 86.376 en Bogotá (ene-sep 2026) | Misma capa de la Secretaría de Seguridad, corte 30-sep-2026 (contrastada con MinDefensa) | Consulta a la capa de datos y API | Igual que arriba · datos.gov.co: m8fd-ahd9, 4rxi-8m8d, q2ib-t9am |
| Pobreza por localidad; más de 1 hora al trabajo | DANE-SDP, Encuesta Multipropósito 2025 (cuadros 216A, 216B y otros) | Anexos descargados | dane.gov.co |
| Votos 2023 (Alcaldía) y 2026 (Presidencia) por localidad; calendario electoral 2027 | Registraduría Nacional (Observatorio Electoral; Resolución 12338 de 2026) | Archivo descargado y visor | registraduria.gov.co |
| Trazados y estaciones troncales de TransMilenio | TransMilenio S.A., datos abiertos | Descarga (JSON) | datosabiertos-transmilenio |
| Habitantes de calle: 10.478 en 2024, +10 % frente a 2017 (9.538); el centro baja de 33,3 % a 25,6 % | SDIS, VIII Censo de Habitantes de Calle 2024 (con SDP e IDIPRON) | Lectura de la publicación oficial | https://bogota.gov.co/en/node/242862 (14-feb-2025) |
| Habitantes de calle por localidad (encuestados 2017 y 2024): Mártires 1.750→1.302, Santa Fe 1.313→1.236, Kennedy 682→1.005, Engativá 316→589, Suba 217→528, etc. | Presentación de la SDIS sobre el censo 2024 | Foto propia de la presentación (no encontré la tabla publicada en línea) | Foto en el proyecto |
| Búsquedas sobre candidatos | Google Trends, consultado el 11-nov-2026 | Consulta | trends.google.com |
| Congestión de Bogotá | TomTom Traffic Index 2025, citado por Vanguardia (25-ene-2026) | Prensa | vanguardia.com |
| Salud: quejas y crisis de EPS | Infobae (15-abr-2026) con datos de la Supersalud · Personería de Bogotá citada por Semana (nov-2025) | Prensa | infobae.com · semana.com |

## 2. Contexto de prensa (no se usan como dato principal)

- Prensa Mercosur (17-feb-2025): confirma la baja del centro y el aumento en Kennedy, Suba y Engativá. https://prensamercosur.org/2025/02/17/colombia-bogota-y-el-reto-de-la-poblacion-en-calle-censo-2024-revela-alarmante-incremento/
- El Tiempo (14-feb-2025), resultados del censo. Dice que Los Mártires, Santa Fe y Kennedy suman "casi el 40 %"; con los números de la presentación da cerca de 34 %, por eso no se usa. https://www.eltiempo.com/bogota/estos-son-los-resultados-del-ultimo-censo-de-habitantes-de-la-calle-en-bogota-3426866
- Concejo de Bogotá (16-abr-2026 y 9-abr-2025) sobre hurtos. Su cifra de 88.042 denuncias en 2025 no cuadra con la Secretaría (99.665 solo de enero a septiembre de 2025), por eso no se usa. https://concejodebogota.gov.co/en-bogota-roban-a-9-personas-cada-hora/cbogota/2026-04-16/102915.php
- La Silla Vacía · Vorágine · Semana · Infobae · Caracol Radio · El Tiempo · Me Vale (entrevista de Eva Rey).
- Parte 17 ("Detrás de este video"), dueños de los medios: mapa de propiedad del documento "Medios de comunicación y redes de poder en Colombia" (síntesis, 11-nov-2026), que cita Media Ownership Monitor, CRC (2022) y García y Zambrano (2025). Notas por medio: corpus propio (Caracol Radio 102, Semana 94, Blu Radio 39, El Espectador 34, La FM 24, El Tiempo 20, Noticias Caracol 6, Citytv 0). Encuadre: lectura a mano de 216 notas (Semana: 29 de 58 son peleas; Caracol Radio: 36 de 70 son de gestión en la UNGRD). Mismos datos del dossier v3.
- Parte 17, otros corpus propios: Lula (1.367 notas de CNN Brasil, Poder360, Brasil de Fato, The Guardian, NewsAPI, El Colombiano y BBC), archivo `Brasil_Lula/corpus_limpio_lula.csv`.

## 3. Teoría (autores citados)

- Pierre Bourdieu: capital simbólico y capital social (*La distinción*, 1979; "Las formas del capital", 1986).
- Mauro Wolf: noticiabilidad y criterios de selección de noticias (*La investigación de la comunicación de masas*, 1985).
- Walter Lippmann: el pseudo-entorno, "las imágenes en nuestra cabeza" (*La opinión pública*, 1922).
- Manuel Castells: el poder se juega en la mente de la gente; lo que no aparece en los medios casi no existe (*Comunicación y poder*, 2009; Castells et al., 2007). En el video va parafraseado, no como cita textual.
- Marshall McLuhan: "el medio es el mensaje" (*Understanding Media*, 1964). Cita traducida.
- John Culkin: "nos convertimos en lo que contemplamos" ("A Schoolman's Guide to Marshall McLuhan", *Saturday Review*, 18-mar-1967). Se suele atribuir a McLuhan por error; el propio juego lo marca como "misattributed".

## 4. Material audiovisual

- Clips de prensa: TikTok @Sebastián Quintero · TikTok @Juan Pablo Camacho Báez · KienyKe · Pulzo · El Espectador.
- Juego: *We Become What We Behold*, Nicky Case (2016), dominio público (CC0). https://ncase.me/wbwwb/ · código: https://github.com/ncase/wbwwb
- Gameplay: "We Become What We Behold Full Playthrough | Longplay | Walkthrough (no commentary)", canal Ludophiles, YouTube.
- Música de la escena estilo pantalla de carga: tema de *Grand Theft Auto IV* (Rockstar Games), extraído de YouTube. Uso académico; puede tener restricción de derechos si se sube a redes.
- Fotos: Wikimedia Commons (Mariordo, CC BY-SA 4.0; Hospital San José, CC BY-SA 3.0; busto de Luis Carlos Galán, CC BY 4.0; Presidencia de Colombia, dominio público; otras con licencias libres). Foto de estación de TransMilenio de referencia: Wikimedia Commons.
- Fotos propias: estación de TransMilenio (animada con Google Flow) y presentación de la SDIS.
- Ilustraciones propias de Oviedo, Paloma Valencia, Claudia López y Peñalosa (animadas con Google Flow, solo movimiento de cámara).
- Sonido y música de fondo: Mixkit (licencia gratuita).
- Música de fondo de la parte del juego: "Lightless Dawn", Kevin MacLeod (incompetech.com), licencia Creative Commons Attribution 4.0 (exige dar crédito; ya va en los créditos). En esa parte se quitó el audio original del gameplay y solo quedan un clic de cámara en cada foto y un sonido suave cuando sale la noticia.

## 5. Herramientas de IA

- Google Flow: clips de fondo (estación, barrios del sur, gente caminando) y animación de las ilustraciones.
- Claude (Anthropic): apoyo en guion, búsqueda y verificación de datos, animaciones (Python) y montaje.
- Voz: grabación propia de Diego Umbarila. Sin rostro.

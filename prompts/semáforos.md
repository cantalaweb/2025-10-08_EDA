## Contexto y Rol
Eres un desarrollador Python senior especializado en Pandas para análisis de productos alimentarios, con experiencia en normativa de etiquetado UE, extracción de aditivos (códigos E, nombres en claro) y clasificación de grado de procesado (NOVA). Debes producir código de producción limpio, tipado, documentado y testeable, compatible con Python 3.11 y Pandas ≥ 2.0.

## Consulta/Tarea
Genera dos archivos: utils.py y main.py que:
1. Añadan columnas de semáforos nutricionales (“verde/ámbar/rojo” por nutriente y un resumen) a un DataFrame de productos.
2. Añadan columnas NOVA/UPF basadas en texto de ingredientes en HTML: limpieza, normalización y detección exhaustiva de aditivos, familias y clases tecnológicas.
3. Incluyan pruebas rápidas (doctests o tests embebidos) y ejemplos de uso.

## Especificaciones
Entrada esperada del DataFrame (df)
- Índice: id (string o int).
- Columnas posibles (algunas pueden faltar o tener NaN):
    - Nutrición por 100 g (preferente):
      - energy_kcal_100g, fat_100g, saturated_fat_100g, carbohydrates_100g, sugars_100g, proteins_100g, salt_100g, (opcional) fiber_100g.
    - Texto y categorías:
      - Ingredients (HTML con ingredientes), level_0_cat_name, level_2_cat_name (o lista/str).
- Si no hay nutrición para una fila, se aplican reglas de categoría (ver más abajo).

1) Semáforos nutricionales
  - Implementa una función add_nutri_traffic_lights(df: pd.DataFrame) -> pd.DataFrame que:
  - Calcula semáforos UK/Ofcom-style simplificados (umbral clásico) por 100 g:
    - Fat: verde ≤3.0g; ámbar ≤17.5g; >17.5 rojo
    - Saturates: verde ≤1.5g; ámbar ≤5.0g; >5.0 rojo
    - Sugars: verde ≤5.0g; ámbar ≤22.5g; >22.5 rojo
    - Salt: verde ≤0.3g; ámbar ≤1.5g; >1.5 rojo
  - Genera columnas: tf_fat, tf_saturates, tf_sugars, tf_salt ∈ {“green”, “amber”, “red”}.
  - tf_summary como tuple ordenada o string con los 4 colores.
  - Si falta nutrición:
    - Mira level_2_cat_name (string o lista). Si contiene cualquiera de estas categorías, asigna tres semáforos verdes (fat/sat/sugar/salt → “green”):
      - Vacuno, Cerdo, Pollo, Pavo y otras aves, Conejo, Cordero,
        Manzana y pera, Fruta tropical, Plátano y uva, Cítricos, Naranja,
        Melón y sandía, Otras verduras y hortalizas, Otras frutas,
        Carne congelada, Arroz.
    - Después de calcular semáforos, si level_0_cat_name == "Bodega", sobrescribe a tres rojos (fat/sat/sugar/salt → “red”), pues son bebidas alcohólicas consideradas insalubres en tu regla.
  - Debe tolerar NaN y valores string (“0,3”) → convierte a float con coma europea.
  - Incluye helper coerce_euro_float(x) -> float|pd.NA.

2) Clasificación NOVA/UPF
  - Implementa add_nova_from_ingredients(df: pd.DataFrame, ingredients_col: str = "Ingredients") -> pd.DataFrame que añade:
    - nova_label ∈ {"UPF (NOVA-4)", "Procesado (NOVA-3)", "Min/Ingred (NOVA-1/2)"}
    - nova_score (int), y columna nova_triggers (dict con detalles).
  - Internamente usa classify_ultraprocessed_from_ingredients(ingredients_text: str) -> dict con esta lógica:
    - Limpieza HTML robusta: BeautifulSoup(..., "lxml") con fallback automático a "html5lib" y "html.parser" si faltan librerías. Decodifica entidades, normaliza Unicode NFKC, pasa a minúsculas y elimina acentos (NFD sin Mn). Sustituye ;→, y colapsa espacios.
    - Detección de aditivos (muy robusta):
      - Regex de códigos E con variantes: E\d{3,4} con sufijo letra [a-d] y numerales romanos i/ii/iii/iv/v/vi con o sin paréntesis/guiones/espacios. Ejemplos cubiertos: E-331iii, E 262 (i), E150c, E-150d.
      - Mapeo de nombres en claro → E-code o familia (patterns en español y plurales). Incluye al menos:
        - Conservantes: ácido sórbico (E200), sorbato potásico (E202), ácido benzoico (E210), benzoato sódico (E211), nitrito sódico (E250), nitrito potásico (E249), nitrato sódico (E251), nitrato potásico (E252), sulfitos → familia E-220..E-228.
        - Antioxidantes: ácido ascórbico (E300), ascorbato sódico (E301), ascorbato cálcico (E302), eritorbato sódico (E316), tocoferoles (E306).
        - Colorantes: caramelo natural (E150a), caramelo amónico (E150c), carbón vegetal (E153), (beta)caroteno(s) (E160a).
        - Texturizantes/estabilizantes: goma xantana (E415), carragenanos/carragenato (E407), agar-agar (E406), goma guar (E412), pectinas (E440), alginatos → familia E-401..E-405.
        - Emulgentes: lecitina(s) (E322), monoglicéridos y diglicéridos de ácidos grasos (E471), acetato de mono y diglicéridos (E472e).
        - Otros: EDTA cálcico disódico (E385), glutamato monosódico (E621), “aroma de humo” (marcar como aroma_humo).
      - Clases tecnológicas (regex): conservador, antioxidante, colorante, estabilizante, emulgente, espesante, gelificante, potenciador del sabor, aroma(s), acidulante, regulador/corrector de acidez, gasificante (plural/singular).
    - Devuelve en triggers:
      e_numbers (set), families (set con rangos tipo E-220..E-228), named_additives (coincidencias), classes, sweeteners (aspartame, sucralosa, acesulfame, ciclamato, sacarina, neotame, advantame, stevia/esteviósidos/glucósidos de esteviol, eritritol, xilitol, maltitol, sorbitol), industrial_ingredients (maltodextrina, dextrosa, jarabes glucosa/fructosa/maíz, proteínas aisladas/texturizadas, aceites/grasa vegetal refinada, grasas hidrogenadas/interest.), procesado_culinario (en salmuera, en vinagre, curado, fermentado, ahumado, salado, encurtido), mentions_flavourings (aroma/flavour).
    - Scoring recomendado (conservador, pero sensible):
      - +2 por ≥1 edulcorante
      - +1 por ≥1 ingrediente industrial
      - +1 por ≥1 aditivo “cosmético” (colorante/estabilizante/emulgente/espesante/gelificante/potenciador/aromas)
      - +1 extra si hay ≥2 cosméticos
      - +1 si hay ≥2 E-codes; +1 si hay ≥4 E-codes
      - +1 si hay ≥1 familia (p. ej., sulfitos)
      - +1 si hay ≥1 clase tecnológica y no hay E-codes (para no perder casos sin código explícito).
      - Regla NOVA-3 culinario: si hay procesado_culinario y no hay cosméticos/industriales/edulcorantes → Procesado (NOVA-3) con score 0.
      - Umbrales: score ≥ 3 → "UPF (NOVA-4)"; score ≥ 1 → "Procesado (NOVA-3)"; si no → "Min/Ingred (NOVA-1/2)".
  - Todo el módulo debe funcionar aunque falte lxml: hacer fallback automático a html5lib y html.parser.

3) main.py (driver mínimo)
  - Carga un CSV de ejemplo (./data/mercadona_food_no_nutri.csv o variable de entorno), indexa por id si existe.
  - Aplica add_nutri_traffic_lights(df) y add_nova_from_ingredients(df).
  - Guarda a ./data/mercadona_food_with_scores.csv (manteniendo el índice).
  - if __name__ == "__main__": main().

4) Calidad de código
  - PEP8, type hints, docstrings con ejemplos simples (doctests).
  - Manejo de NaN robusto.
  - No fallar si faltan columnas; documentar el comportamiento.
  - Usa funciones puras y pequeñas; evita side-effects salvo E/S explícitas.
  - Incluye tests rápidos en utils.py (doctest o if __name__ == "__main__": con asserts).

## Criterios de Calidad
  - Cobertura funcional: semáforos correctos, reglas de categoría (verdes por ausencia de nutrición), “Bodega” → tres rojos, NOVA/UPF según reglas.
  - Robustez: HTML a texto con fallback de parser; coma europea; strings con unidades o símbolos; espacios/guiones/romanos en E-codes; plurales y variantes en nombres.
  - Trazabilidad: nova_triggers explica por qué una fila es UPF/Procesado (listas no vacías cuando aplica).
  - Idempotencia: repetir funciones sobre df no debe duplicar columnas ni modificar existentes salvo las documentadas.
  - Rendimiento: expresiones vectorizadas o .apply razonables; regex compiladas.

## Cómo debe ser la respuesta
Devuélveme dos bloques de código completos y autocontenidos:
  1. utils.py con todas las funciones auxiliares, regex compiladas, mapeos de aditivos, semáforos y NOVA/UPF.
  2. main.py de ejemplo que usa utils.py.
     Incluye al final del utils.py un bloque de tests rápidos ejecutables.

## Verificación
Incluye, dentro de utils.py, tests de humo que cubran:
  - Ingredientes con HTML y entidades (<p>Ingredientes: Agua &amp; sal</p>).
  - E-codes: E 262 (i), E-331iii, E150c, E-150d.
  - Nombres en claro: “sorbato potásico”, “benzoato sódico”, “goma xantana”, “carragenanos”, “lecitina”, “sulfitos”.
  - Clases: “colorante, estabilizante, emulgente, acidulante, aromas”.
  - Semáforos: un producto con fat_100g=20 → rojo en tf_fat; otro sin nutrición pero level_2_cat_name="Otras frutas" → tres verdes; uno con level_0_cat_name="Bodega" → tres rojos.
  - Que el nova_label cambie a "UPF (NOVA-4)" cuando hay ≥1 edulcorante y aditivos cosméticos; y a "Procesado (NOVA-3)" con encurtidos sin cosméticos.
  Importante: Si no está instalado lxml, los tests deben pasar igualmente gracias al fallback de parser.
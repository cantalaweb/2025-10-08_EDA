<!-- Title -->
<h1 align='center'> Análisis Nutricional de Productos de Mercadona </h1>

<p align='center'>
    <img src='./presentation/img/logo-mercadona.png' width='400' />
</p>

Autor: Diego Cantalapiedra de la Fuente

Fecha: Octubre 2025

Contexto: Proyecto final del Bootcamp de Data Science - The Bridge | Digital Talent Accelerator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

<!-- tech stack badges ---------------------------------- -->
<p align='center'>
    <!-- Python -->
    <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff" alt="Python"></a>
    <!-- Numpy -->
    <a href="https://numpy.org"><img src="https://img.shields.io/badge/NumPy-4DABCF?logo=numpy&logoColor=fff" alt="NumPy"></a>
    <!-- Pandas -->
    <a href="https://pandas.pydata.org"><img src="https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=fff" alt="Pandas"></a>
    <!-- Matplotlib -->
    <a href="https://matplotlib.org"><img src="https://custom-icon-badges.demolab.com/badge/Matplotlib-71D291?logo=matplotlib&logoColor=fff" alt="Matplotlib"></a>
    <!-- Seaborn -->
    <a href="https://seaborn.pydata.org"><img src="https://img.shields.io/badge/Seaborn-grey?logo=Seaborn" alt="Seaborn"></a>
    <!-- ChatGPT -->
    <a href="https://chatgpt.com"><img src="https://img.shields.io/badge/ChatGPT-74aa9c?logo=openai&logoColor=white" alt="ChatGPT"></a>
</p>
<br/>


## Tabla de Contenidos

- [Introducción](#introducción)
- [Hipótesis](#hipótesis)
- [Objetivos](#objetivos)
- [Metodología](#metodología)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Requerimientos](#requerimientos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Sistemas de Clasificación](#sistemas-de-clasificación)
- [Limitaciones](#limitaciones)
- [Trabajo Futuro](#trabajo-futuro)
- [Licencia](#licencia)
- [Agradecimientos](#agradecimientos)

---

## Introducción

Este proyecto analiza la calidad nutricional y el grado de procesamiento de los productos alimenticios disponibles en Mercadona, una de las principales cadenas de supermercados de España. Utilizando técnicas de web scraping, procesamiento de imágenes con IA (GPT-4o) y análisis de datos, se evalúan más de **3,000 productos** para determinar su impacto en la salud pública.

El análisis combina múltiples sistemas de clasificación nutricional reconocidos internacionalmente:
- **Sistema de semáforos nutricionales** (UK Food Standards Agency)
- **Clasificación NOVA** (nivel de procesamiento industrial)
- **Puntuación mixta personalizada** que combina ambos criterios

---

## Hipótesis

**Hipótesis principal:**  
> "El 70-75% de la comida disponible en un supermercado es ultraprocesada, y de ella, un alto porcentaje es nutricionalmente insalubre".

Esta hipótesis surge de la preocupación creciente sobre la prevalencia de alimentos ultraprocesados (UPF - Ultra-Processed Foods) en los supermercados modernos y su relación con problemas de salud pública como la obesidad, diabetes tipo 2 y enfermedades cardiovasculares.

---

## Objetivos

### Objetivo Principal
Validar o refutar la hipótesis sobre la proporción de alimentos ultraprocesados e insalubres en el catálogo de Mercadona.

### Objetivos Secundarios
1. **Extraer y estructurar** información nutricional de productos mediante scraping e IA.
2. **Clasificar productos** según su nivel de procesamiento (sistema NOVA).
3. **Evaluar la calidad nutricional** usando el sistema de semáforos del Reino Unido.
4. **Desarrollar una métrica combinada** que integre procesamiento y nutrición.
5. **Visualizar patrones** en los datos mediante análisis exploratorio (EDA).
6. **Identificar categorías** de productos más y menos saludables.

---

## Metodología

### 1. Extracción de Datos (Web Scraping)
- **Script:** `mercadona_scraper.py`
- **Fuente:** API privada de Mercadona (`tienda.mercadona.es/api`)
- **Datos extraídos:**
  - Metadatos de productos (nombre, categoría, precio, ingredientes, etc).
  - Imágenes de productos (del producto y de sus etiquetas).
  - Información nutricional básica cuando está disponible.

### 2. Procesamiento de Información Nutricional
- **Script:** `nutri.py`
- **Método:** Extracción mediante GPT-4o Vision
- **Proceso:**
  - Lectura automática de tablas nutricionales en imágenes.
  - Validación cruzada entre múltiples imágenes del mismo producto.
  - Consenso o promedio cuando hay discrepancias.
- **Campos extraídos:**
  - Valor energético (kcal/100g)
  - Grasas totales (g/100g)
  - Grasas saturadas (g/100g)
  - Carbohidratos (g/100g)
  - Azúcares (g/100g)
  - Proteínas (g/100g)
  - Sal (g/100g)

### 3. Clasificación y Análisis
- **Script:** `semáforos.py`
- **Funciones principales:**
  - `add_traffic_lights()`: Semáforos nutricionales (verde/ámbar/rojo).
  - `add_nova_from_ingredients()`: Clasificación NOVA basada en ingredientes.
  - `add_mixed_score()`: Puntuación compuesta (0-100).

### 4. Análisis Exploratorio de Datos
- **Notebook:** `EDA.ipynb`
- **Análisis realizados:**
  - Distribuciones de macronutrientes.
  - Correlaciones entre variables nutricionales.
  - Análisis por categoría NOVA.
  - Análisis de semáforos nutricionales.
  - Visualizaciones comparativas.

---

## Estructura del Proyecto

```
.
├── data/                           # Datos del proyecto
│   ├── mercadona.csv              # Datos brutos del scraping
│   ├── mercadona_food_no_nutri.csv # Productos sin info nutricional
│   ├── mercadona_food.csv         # Productos con info nutricional
│   ├── mercadona_food_final.csv   # Dataset final con clasificaciones
│   ├── food_ready_for_EDA.csv     # Dataset limpio para análisis
│   └── img/                       # Imágenes de productos
│       ├── 9995_img_0.jpg
│       ├── 9995_img_1.jpg
│       └── ...
│
├── src/                           # Código fuente
│   ├── mercadona_scraper.py       # Scraper de la API de Mercadona
│   ├── nutri.py                   # Extracción de info nutricional con IA
│   ├── semáforos.py               # Clasificación nutricional y NOVA
│   ├── utils.py                   # Funciones auxiliares
│   └── EDA.ipynb                  # Análisis exploratorio de datos
│
├── prompts/                       # Prompts para GPT-4o
│   ├── nutri_prompt.md           # Prompt para extracción nutricional
│   ├── nutri_script.md
│   ├── scraper_script.md
│   └── semáforos.md
│
├── presentation/                  # Recursos para presentación
│   └── img/                      # Gráficos y visualizaciones
│       ├── histograma_de_azúcares.png
│       ├── histograma_de_nova_score.png
│       ├── productos_por_nivel_NOVA.png
│       ├── productos_por_salubridad.png
│       └── ...
│
├── pyproject.toml                # Configuración del proyecto (uv)
├── uv.lock                       # Archivo de bloqueo de dependencias
├── ruff.toml                     # Configuración del linter
└── README.md                     # Este archivo
```

---

## Requerimientos

### Software
- **Python:** 3.11 o superior
- **Gestor de paquetes:** `uv` (recomendado) o `pip`
- **API Key:** OpenAI (para GPT-4o)

### Librerías Principales
```toml
pandas >= 2.0.0
numpy >= 1.24.0
requests >= 2.31.0
beautifulsoup4 >= 4.12.0
openai >= 1.0.0
python-dotenv >= 1.0.0
matplotlib >= 3.7.0
seaborn >= 0.12.0
jupyter >= 1.0.0
```

---

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/cantalaweb/2025-10-08_EDA.git
cd 2025-10-08_EDA
```

### 2. Configurar el entorno virtual (opción A - con uv)
```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Crear entorno e instalar dependencias
uv sync
```

### 2. Configurar el entorno virtual (opción B - con pip)
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto:
```bash
OPENAI_API_KEY=tu_api_key_aqui
```

---

## Uso
Seguir  mejor el proceso en el notebook de Jupyter `EDA.ipynb`. Lo descrito a continuación es un mero resumen de la ejecución de los scripts adicionales.

### Paso 1: Extracción de Datos (Web Scraping)

```bash
cd src
python mercadona_scraper.py
```

**Salidas:**
- `data/mercadona.csv`: Dataset completo con metadatos
- `data/img/`: Imágenes de productos descargadas

**Tiempo estimado:** 2-4 horas (dependiendo de la conexión)

---

### Paso 2: Extracción de Información Nutricional

```bash
python nutri.py
```

**Configuración en `nutri.py`:**
```python
updated = utils.extract_nutrition_to_df(
    df,
    images_dir="./data/img",
    prompt_path="./prompts/nutri_prompt.md",
    model="gpt-4o",
    start_from_id=None,     # Iniciar desde un ID específico (opcional)
    save_every=50,          # Guardar progreso cada N productos
    out_csv_path="./data/mercadona_food.csv",
)
```

**Salidas:**
- `data/mercadona_food.csv`: Dataset con información nutricional extraída
- `nutri.log`: Log del proceso

**Tiempo estimado:** 6-12 horas para ~3,000 productos  
**Coste estimado:** ~$17 USD en créditos de OpenAI

---

### Paso 3: Clasificación Nutricional y NOVA

```bash
python semáforos.py
```

**Salidas:**
- `data/mercadona_food_final.csv`: Dataset final con todas las clasificaciones

**Columnas añadidas:**
- `tl_fat`, `tl_sat`, `tl_sugars`, `tl_salt`: Semáforos (green/amber/red)
- `nova_label`: Clasificación NOVA (Min/Ingred, Procesado, UPF)
- `nova_score`: Puntuación NOVA (0-5+)
- `mixed_score`: Puntuación mixta (0-100)
- `mixed_label`: Etiqueta final (Saludable/A valorar/No saludable)

---

### Paso 4: Análisis Exploratorio

```bash
jupyter notebook src/EDA.ipynb
```

El notebook incluye:
- Estadísticas descriptivas
- Distribuciones de macronutrientes
- Análisis de correlaciones
- Visualizaciones por categoría NOVA
- Análisis de semáforos nutricionales
- Gráficos comparativos por categoría de producto

---

## Sistemas de Clasificación

### 1. Semáforos Nutricionales (UK FSA)

Sistema de colores basado en los umbrales de la Food Standards Agency del Reino Unido:

| Nutriente | Verde | Ámbar | Rojo |
|-----------|-------|-------|------|
| **Grasas** | ≤ 3g | 3-17.5g | > 17.5g |
| **Grasas Saturadas** | ≤ 1.5g | 1.5-5g | > 5g |
| **Azúcares** | ≤ 5g | 5-22.5g | > 22.5g |
| **Sal** | ≤ 0.3g | 0.3-1.5g | > 1.5g |

*Valores por 100g de producto*

---

### 2. Clasificación NOVA

Sistema desarrollado por la Universidad de São Paulo que clasifica alimentos según su grado de procesamiento:

#### **NOVA-1: Alimentos sin procesar o mínimamente procesados**
- Frutas, verduras, legumbres, carne fresca, huevos, leche
- **Ejemplo:** Manzanas, lentejas secas, pechuga de pollo fresca.

#### **NOVA-2: Ingredientes culinarios procesados**
- Aceites, mantequilla, azúcar, sal.
- **Ejemplo:** Aceite de oliva virgen extra, sal marina.

#### **NOVA-3: Alimentos procesados**
- Productos con 2-3 ingredientes, procesados con métodos tradicionales.
- **Ejemplo:** Conservas vegetales, quesos, pan artesanal, legumbres en conserva.

#### **NOVA-4: Alimentos ultraprocesados (UPF)**
- Productos con ≥5 ingredientes, contienen aditivos, edulcorantes, etc.
- **Ejemplo:** Refrescos, bollería industrial, platos preparados, snacks.

**Criterios de detección automática:**
- Presencia de códigos E (E-100 a E-1520).
- Edulcorantes artificiales (aspartamo, sucralosa, etc.).
- Ingredientes industriales (jarabes, proteínas aisladas, maltodextrina).
- Aditivos cosméticos (aromas, colorantes, potenciadores del sabor).
- Clases tecnológicas (conservadores, estabilizantes, emulgentes).

---

### 3. Puntuación Mixta (Mixed Score)

Métrica compuesta que integra nutrición y procesamiento:

```
Mixed Score = 0.6 × N_norm + 0.4 × P_norm
```

Donde:
- **N_norm:** Puntuación nutricional (0-100) basada en semáforos.
  - Verde = 2 puntos, Ámbar = 1 punto, Rojo = 0 puntos
  - Normalizado: `(puntos / 8) × 100`
- **P_norm:** Puntuación de procesamiento (0-100) basada en NOVA.
  - NOVA-1/2 = 3 puntos (100%)
  - NOVA-3 = 2 puntos (66.7%)
  - NOVA-4 = 0 puntos (0%)

**Guardarraíles especiales:**
- Aceites vírgenes de un solo ingrediente: Se perdona el semáforo rojo en grasas.
- Frutos secos 100%: Se perdona el semáforo rojo en grasas.
- Bebidas con edulcorantes: Penalización automática.

**Clasificación final:**
- **Saludable:** Mixed Score ≥ 75
- **A valorar:** Mixed Score 55-74
- **No saludable:** Mixed Score < 55

---

## Limitaciones

1. **Muestra específica:** Análisis limitado a Mercadona, no extrapolable a todas las cadenas.
2. **Clasificación NOVA automatizada:** Basada en reglas heurísticas, puede tener falsos positivos/negativos.
3. **OCR con IA:** La extracción nutricional puede contener errores en productos con imágenes de baja calidad.
4. **Productos sin imagen:** Algunos productos no tienen tabla nutricional visible.
5. **Cambios temporales:** El catálogo de productos varía con el tiempo.
6. **Contexto cultural:** Los umbrales del sistema de semáforos son del Reino Unido, no de España.

---

## Trabajo Futuro

### Mejoras Técnicas
- [ ] Implementar validación manual de una muestra aleatoria.
- [ ] Añadir sistema de clasificación Nutri-Score (Francia).
- [ ] Desarrollar modelo de ML para clasificación NOVA.
- [ ] Crear dashboard interactivo con Streamlit/Dash.

### Análisis Adicionales
- [ ] Comparativa entre cadenas de supermercados.
- [ ] Análisis temporal de cambios en el catálogo.
- [ ] Estudio de precios vs. calidad nutricional.
- [ ] Análisis de marketing vs. realidad nutricional.
- [ ] Analizar la diferencia entre aguas y refrescos, que estaban jubtos en la misma categoría. Y de Postres y yogures, Pizzas y platos preparados, Charcutería y quesos.
- [ ] La categoría Bebés sólo contiene potitos, y salen saludables en su gran mayoría. Sin embargo, no hay categoría que reúna todos aquellos alimentos cuyo marketing está dirigido a niños. Sería muy interesante crear una nueva categoría para estos alimentos y poder ver cómo de saludables son en su conjunto.

---

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

```
MIT License

Copyright (c) 2025 Diego Cantalapiedra de la Fuente

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Agradecimientos

- **Borja Barber**: Por sus conocimientos, paciencia y apoyo.
- **The Bridge**: Por la formación en Data Science y el apoyo durante el bootcamp.
- **Mercadona**: Por mantener una API accesible, aunque sea privada.
- **OpenAI**: Por proporcionar la tecnología GPT-4o para extracción de información.
- **Universidad de São Paulo**: Por desarrollar la clasificación NOVA.
- **UK Food Standards Agency**: Por el sistema de semáforos nutricionales.

---

## Contacto

**Diego Cantalapiedra de la Fuente**

- GitHub: [@cantalaweb](https://github.com/cantalaweb)
- LinkedIn: (https://www.linkedin.com/in/diego-cantalapiedra-09a4577/)
- Email: source@cantalaweb.com

---

## Referencias

1. Monteiro CA, et al. (2019). "Ultra-processed foods: what they are and how to identify them." *Public Health Nutrition*, 22(5), 936-941.
2. UK Food Standards Agency. (2013). "Guide to creating a front of pack (FoP) nutrition label for pre-packed products sold through retail outlets."
3. World Health Organization. (2015). "Guideline: Sugars intake for adults and children."
4. Pan American Health Organization. (2015). "Ultra-processed food and drink products in Latin America: Trends, impact on obesity, policy implications."

---

**⭐ Si este proyecto te ha sido útil, considera darle una estrella en GitHub**

---

*Última actualización: Octubre 2025*
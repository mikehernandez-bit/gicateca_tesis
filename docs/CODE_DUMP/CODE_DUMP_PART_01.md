# CODE DUMP (Parte 01)

## Convenciones
- Todos los archivos est?n en UTF-8 (si alguno no lo est?, se indica).
- Archivos binarios no se incluyen aqu?, solo en INDEX.md.
---

## .gitignore
**Tama?o:** 53
**SHA256:** c8028dbde2a79333aebe769acdd36015f5bdde49c878bf276eacef011a718535
**Tipo:** other

```
__pycache__/
*.pyc
.venv/
venv/
.env
.DS_Store

```

---

## 2.10.0
**Tama?o:** 757
**SHA256:** e24e4550a49495f1e3c211e260f0cf9d76c738d6245b4c2e3acf03230f75454b
**Tipo:** other

```
Requirement already satisfied: pydantic in c:\users\steeve\appdata\local\python\pythoncore-3.14-64\lib\site-packages (2.12.5)
Requirement already satisfied: annotated-types>=0.6.0 in c:\users\steeve\appdata\local\python\pythoncore-3.14-64\lib\site-packages (from pydantic) (0.7.0)
Requirement already satisfied: pydantic-core==2.41.5 in c:\users\steeve\appdata\local\python\pythoncore-3.14-64\lib\site-packages (from pydantic) (2.41.5)
Requirement already satisfied: typing-extensions>=4.14.1 in c:\users\steeve\appdata\local\python\pythoncore-3.14-64\lib\site-packages (from pydantic) (4.15.0)
Requirement already satisfied: typing-inspection>=0.4.2 in c:\users\steeve\appdata\local\python\pythoncore-3.14-64\lib\site-packages (from pydantic) (0.4.2)

```

---

## app/__init__.py
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** python

```python

```

---

## app/core/__init__.py
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** python

```python

```

---

## app/core/loaders.py
**Tama?o:** 7334
**SHA256:** 9ba50fefe06324871b96294700ae085b31daf1cb6ef898588487438bceb5181b
**Tipo:** python

```python
"""Shared loaders for data access across modules."""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json_file(file_path: Path) -> Any:
    """Load and parse a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in file: {file_path}")


def get_data_dir(uni: str = "unac") -> Path:
    """Get the path to the data directory for a university code."""
    uni = (uni or "unac").strip().lower()
    app_dir = Path(__file__).resolve().parents[1]
    return app_dir / "data" / uni


@dataclass(frozen=True)
class FormatIndexItem:
    format_id: str
    uni: str
    categoria: str
    enfoque: str
    path: Path
    titulo: str
    data: Optional[Dict[str, Any]] = None


_ENFOQUE_ALIASES = {
    "cual": "cual",
    "cualitativo": "cual",
    "cuant": "cuant",
    "cuantitativo": "cuant",
}

_IGNORE_FILENAMES = {"alerts.json"}
_HIDDEN_PREFIXES = ("_", "__")


def _is_ignored_path(path: Path) -> bool:
    if path.name in _IGNORE_FILENAMES:
        return True
    if path.name.endswith(".sample.json"):
        return True
    for part in path.parts:
        if part.startswith(_HIDDEN_PREFIXES):
            return True
    return False


def _normalize_format_id(raw_id: str, uni: str) -> str:
    if not raw_id:
        return ""
    normalized = re.sub(r"[_\s]+", "-", raw_id.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if not normalized.startswith(f"{uni}-"):
        normalized = f"{uni}-{normalized}"
    return normalized


def _derive_enfoque(tokens: List[str]) -> str:
    for token in tokens:
        mapped = _ENFOQUE_ALIASES.get(token)
        if mapped:
            return mapped
    return "general"


def _humanize_id(format_id: str, uni: str) -> str:
    cleaned = format_id
    if cleaned.startswith(f"{uni}-"):
        cleaned = cleaned[len(uni) + 1 :]
    parts = [p for p in re.split(r"[-_]+", cleaned) if p]
    return " ".join(word.capitalize() for word in parts) or format_id


def _discover_for_uni(uni: str) -> List[FormatIndexItem]:
    from app.universities.registry import get_provider

    data_dir = get_provider(uni).get_data_dir()
    if not data_dir.exists():
        return []

    items: List[FormatIndexItem] = []
    seen_ids: set[str] = set()

    for path in data_dir.rglob("*.json"):
        if _is_ignored_path(path):
            continue

        rel_path = path.relative_to(data_dir)
        categoria = rel_path.parent.name.lower() if rel_path.parent != Path(".") else "general"
        stem = path.stem
        tokens = [t for t in re.split(r"[_-]+", stem.lower()) if t]
        enfoque = _derive_enfoque(tokens)

        try:
            data = load_json_file(path)
        except Exception:
            data = None

        if isinstance(data, list):
            for idx, entry in enumerate(data):
                if not isinstance(entry, dict):
                    continue
                raw_id = entry.get("id") or entry.get("format_id") or f"{stem}-{idx + 1}"
                entry_tokens = [t for t in re.split(r"[_-]+", str(raw_id).lower()) if t]
                entry_categoria = (entry.get("tipo_formato") or entry.get("categoria") or categoria).lower()
                entry_enfoque = (entry.get("enfoque") or _derive_enfoque(entry_tokens)).lower()
                format_id = _normalize_format_id(str(raw_id), uni)
                if format_id in seen_ids:
                    continue
                seen_ids.add(format_id)

                titulo = entry.get("titulo") or entry.get("title") or _humanize_id(format_id, uni)
                items.append(
                    FormatIndexItem(
                        format_id=format_id,
                        uni=uni,
                        categoria=entry_categoria,
                        enfoque=entry_enfoque,
                        path=path.resolve(),
                        titulo=str(titulo),
                        data=dict(entry),
                    )
                )
            continue

        if isinstance(data, dict):
            raw_id = data.get("id") or stem
            titulo = data.get("titulo")
        else:
            raw_id = stem
            titulo = None

        format_id = _normalize_format_id(str(raw_id), uni)
        if format_id in seen_ids:
            continue
        seen_ids.add(format_id)
        if not titulo:
            titulo = _humanize_id(format_id, uni)

        items.append(
            FormatIndexItem(
                format_id=format_id,
                uni=uni,
                categoria=categoria,
                enfoque=enfoque,
                path=path.resolve(),
                titulo=str(titulo),
            )
        )

    items.sort(key=lambda item: (item.categoria, item.enfoque, item.titulo.lower(), item.format_id))
    return items


def discover_format_files(uni: Optional[str] = None) -> List[FormatIndexItem]:
    """Discover JSON format files for a university or all universities."""
    if uni:
        return _discover_for_uni((uni or "unac").strip().lower())

    from app.universities.registry import list_universities

    items: List[FormatIndexItem] = []
    for code in list_universities():
        items.extend(_discover_for_uni(code))

    items.sort(key=lambda item: (item.uni, item.categoria, item.enfoque, item.titulo.lower(), item.format_id))
    return items


def find_format_index(format_id: str) -> Optional[FormatIndexItem]:
    if not format_id:
        return None
    parts = format_id.split("-")
    uni = (parts[0] if parts else "unac").strip().lower()
    normalized = _normalize_format_id(format_id, uni)
    try:
        items = discover_format_files(uni)
    except KeyError:
        return None
    for item in items:
        if item.format_id == normalized:
            return item
    return None


def load_format_by_id(format_id: str) -> Dict[str, Any]:
    """Load raw JSON by format id, attaching metadata in _meta if missing."""
    item = find_format_index(format_id)
    if not item:
        raise FileNotFoundError(f"Formato no encontrado: {format_id}")

    data = item.data if item.data is not None else load_json_file(item.path)
    if isinstance(data, list):
        match = None
        for entry in data:
            if not isinstance(entry, dict):
                continue
            raw_id = entry.get("id") or entry.get("format_id")
            if raw_id and _normalize_format_id(str(raw_id), item.uni) == item.format_id:
                match = entry
                break
        data = match or data
    if isinstance(data, dict):
        payload = dict(data)
        if "_meta" not in payload:
            payload["_meta"] = {
                "format_id": item.format_id,
                "uni": item.uni,
                "categoria": item.categoria,
                "enfoque": item.enfoque,
                "titulo": item.titulo,
                "path": str(item.path),
            }
        return payload
    return {"_meta": {"format_id": item.format_id, "uni": item.uni, "path": str(item.path)}, "data": data}

```

---

## app/core/seed_loader.py
**Tama?o:** 538
**SHA256:** e0aad8c85f6948c10a490a529fd22927c30e6239436f8bac03b102ebe484ca51
**Tipo:** python

```python
"""Lectura simple de data de ejemplo (sin BD).

Los practicantes pueden reemplazar esto luego por:
- Base de datos (PostgreSQL, SQLite)
- API externa
- Panel admin con persistencia
"""

from pathlib import Path
import json
from typing import Any

ROOT = Path(__file__).resolve().parents[2]  # formatoteca_scaffold/
SEED_DIR = ROOT / "data" / "seed"

def load_json(filename: str) -> Any:
    path = SEED_DIR / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

```

---

## app/core/templates.py
**Tama?o:** 200
**SHA256:** 476d2c0768dc5900c5c5e0ebcfca148ef4d1a4994d1f7855999758bb475985ad
**Tipo:** python

```python
from pathlib import Path
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parents[1]  # app/
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

```

---

## app/core/university_registry.py
**Tama?o:** 355
**SHA256:** 8325874216cdea119cc5a59565d0e704a28296593155379cc305d700124bfb4c
**Tipo:** python

```python
from app.universities.registry import discover_providers, get_provider as _get_provider, list_universities

__all__ = ["discover_providers", "get_provider", "list_universities"]


def get_provider(code: str):
    code = (code or "unac").strip().lower()
    try:
        return _get_provider(code)
    except KeyError:
        return _get_provider("unac")

```

---

## app/data/unac/alerts.json
**Tama?o:** 2
**SHA256:** 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
**Tipo:** json

```json
[]
```

---

## app/data/unac/informe/unac_informe_cual.json
**Tama?o:** 20212
**SHA256:** 71f7e3a3385c6edfcb1223e3b53dc091d5d0d89d1714e8df79dcd84137d4a173
**Tipo:** json

```json
{
  "caratula": {
    "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
    "facultad": "FACULTAD DE [NOMBRE DE LA FACULTAD]",
    "escuela": "ESCUELA PROFESIONAL DE [NOMBRE DE LA ESCUELA]",
    "tipo_documento": "INFORME DE TESIS",
    "titulo_placeholder": "\"[ESCRIBA AQUÍ EL TÍTULO DE LA TESIS CUANTITATIVA]\"",
    "frase_grado": "PARA OPTAR EL TÍTULO PROFESIONAL DE:",
    "grado_objetivo": "[INGENIERO DE ...]",
    "label_autor": "AUTOR: [NOMBRES Y APELLIDOS]",
    "label_asesor": "ASESOR: [NOMBRES Y APELLIDOS]",
    "label_linea": "LÍNEA DE INVESTIGACIÓN: [NOMBRE DE LA LÍNEA]",
    "fecha": "Callao, 2026",
    "pais": "PERÚ"
  },
  "preliminares": {
    "dedicatoria": {
      "titulo": "DEDICATORIA / AGRADECIMIENTO",
      "texto": "[Escriba aquí su dedicatoria o agradecimientos...]"
    },
    "resumen": {
      "titulo": "RESUMEN / ABSTRACT",
      "nota": "Nota: Síntesis de objetivos, métodos y resultados principales.",
      "texto": "\n[Escriba aquí el cuerpo del resumen. Debe contener el objetivo, el método, los resultados y las conclusiones principales. No exceder las 200 palabras.]"
    },
    "indices": {
      "contenido": "ÍNDICE DE CONTENIDO",
      "tablas": "ÍNDICE DE TABLAS",
      "figuras": "ÍNDICE DE FIGURAS",
      "abreviaturas": "ÍNDICE DE ABREVIATURAS",
      "placeholder": "(Generarlo)"
    },
    "introduccion": {
      "titulo": "INTRODUCCIÓN",
      "texto": "[La introducción informa tres elementos muy importantes: El propósito, la importancia de la investigación y el conocimiento actual del tema.]"
    }
  },
  "cuerpo": [
    {
      "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "1.1 Descripción de la realidad problemática",
          "nota": "Describa la realidad de cada variable independiente y dependiente de los últimos 5 a 10 años.",
          "instruccion_detallada": "En este apartado debes presentar y contextualizar el problema basándote en hechos y datos, utilizando un enfoque deductivo (de lo general a lo específico).\n\nContexto internacional: Describe cómo se comporta la variable o el problema a nivel mundial o regional. Usa estadísticas, informes de organismos internacionales o tendencias globales.\nContexto nacional: Explica la situación del problema en el Perú. Cita normativas, informes ministeriales o datos estadísticos nacionales que evidencien la deficiencia.\nContexto institucional/local: Describe la realidad específica en la empresa, área o lugar de estudio. Detalla los síntomas observables (fallas, demoras, pérdidas).\nSustento ingenieril (Obligatorio): Debes aplicar al menos una herramienta de ingeniería para diagnosticar el problema, tal como:\nDiagrama de Ishikawa (Causa-Efecto).\nDiagrama de Pareto (80/20).\nÁrbol de problemas.\nMatriz de Vester o Matriz de Priorización.\nCierre: Finaliza mencionando explícitamente la propuesta de solución (ej. 'Por lo expuesto, se propone la implementación de...')."
        },
        {
          "texto": "1.2 Formulación del problema",
          "nota": "Estructure formalmente la idea de investigación (General y Específicos).",
          "instruccion_detallada": "Estructura formalmente la idea de investigación mediante preguntas que relacionen las variables de estudio.\n\nProblema General: Es la interrogante principal que engloba la relación entre la Variable Independiente y la Dependiente (o la variable única en descriptivos).\nEjemplo: ¿De qué manera la implementación de X influye en Y?\nProblemas Específicos: Son sub-preguntas que desglosan el análisis. Generalmente relacionan las Dimensiones de la Variable Independiente con la Variable Dependiente."
        },
        {
          "texto": "1.3 Objetivos",
          "nota": "Defina el propósito, meta o fin a lograr (General y Específicos).",
          "instruccion_detallada": "Expresan el fin medible que se pretende lograr. Deben iniciar con un verbo en infinitivo fuerte (Determinar, Evaluar, Diseñar, Establecer) y ser congruentes con los problemas.\n\nObjetivo General: El logro final del estudio (respuesta al problema general).\nObjetivos Específicos: Los pasos intermedios u operativos necesarios para alcanzar el general (respuestas a los problemas específicos)."
        },
        {
          "texto": "1.4 Justificación",
          "nota": "Explique la naturaleza, magnitud y trascendencia del estudio.",
          "instruccion_detallada": "Explica las razones por las cuales es necesario realizar el estudio. Debes redactar los siguientes enfoques:\n\nJustificación Técnica/Práctica: ¿Qué problema real resuelve? ¿Cómo mejora la eficiencia, productividad o costos en la empresa?\nJustificación Teórica: ¿Cómo aplica o valida conocimientos de ingeniería existentes?\nJustificación Metodológica: ¿Utiliza algún instrumento, software o método de análisis que sirva de modelo para otros?\nJustificación Económica/Social: ¿Cuál es el beneficio costo-beneficio o el impacto en la sociedad/trabajadores?"
        },
        {
          "texto": "1.5 Delimitantes de la investigación",
          "nota": "Defina los límites Teóricos, Temporales y Espaciales.",
          "instruccion_detallada": "Define las fronteras del estudio para asegurar su viabilidad:\n\nTemática: Línea de investigación de la escuela o área de la ingeniería (ej. Mantenimiento, Telecomunicaciones, Control).\nEspacial: Lugar exacto donde se tomarán los datos (Empresa X, Área Y, Ciudad Z).\nTemporal: Periodo de tiempo que abarca la recolección y análisis de datos (ej. Datos históricos de 2023 o mediciones de Enero a Junio 2024)."
        }
      ]
    },
    {
      "titulo": "II. MARCO TEÓRICO",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "2.1 Antecedentes (Internacional y nacional)",
          "nota": "Estado del arte. Se recomiendan 20 a 30 investigaciones afines.",
          "instruccion_detallada": "Presenta el 'estado del arte'. Debes buscar tesis o artículos científicos (papers) indexados, preferiblemente de los últimos 5 a 10 años.\n\nEstructura de cada antecedente: Debes redactar en forma de párrafo fluido (no viñetas) incluyendo:\nApellido del autor y Año.\nTítulo de la investigación.\nObjetivo principal.\nMetodología (Diseño, muestra, instrumentos).\nResultados numéricos más relevantes (datos estadísticos, mejoras porcentuales).\nConclusiones principales.\nCantidad: Se recomienda un promedio de 5 internacionales y 5 nacionales para pregrado (o 20-30 referencias totales para posgrado)."
        },
        {
          "texto": "2.2 Bases teóricas",
          "nota": "Análisis sistemático de las principales teorías existentes.",
          "instruccion_detallada": "Es el sustento científico de la tesis.\n\nDesarrollo: Analiza sistemáticamente las teorías, leyes, principios y modelos matemáticos/físicos que explican tus variables (Variable Independiente y Dependiente).\nRigor: No es un copiado y pegado; debes interpretar la teoría y citar fuentes confiables (Libros de especialidad, IEEE, normas técnicas).\nFundamentación: Incluir brevemente el enfoque epistemológico (positivista/cuantitativo) que guía el estudio."
        },
        {
          "texto": "2.3 Marco conceptual",
          "nota": "Elaboración de nuevos constructos fundamentados.",
          "instruccion_detallada": "Elabora 'constructos' o definiciones teóricas específicas para tu investigación.\n\nDiferencia: A diferencia de las bases teóricas (que explican el funcionamiento), aquí defines conceptualmente las variables y sus dimensiones basándote en la literatura revisada.\nPropósito: Establecer con claridad qué se entiende por cada concepto clave dentro de tu investigación."
        },
        {
          "texto": "2.4 Definición de términos básicos",
          "nota": "Glosario funcional a la investigación.",
          "instruccion_detallada": "Definiciones precisas y funcionales a la investigación del problema, para evitar ambigüedades en la interpretación de los resultados."
        }
      ]
    },
    {
      "titulo": "III. HIPÓTESIS Y VARIABLES",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "3.1 Hipótesis (General y específicas)",
          "nota": "Enunciado presumible de la relación entre dos o más variables.",
          "instruccion_detallada": "Son las respuestas tentativas a los problemas formulados.\n\nRequisito: Deben ser proposiciones afirmativas que establezcan una relación (causa-efecto, correlación o diferencia) entre las variables.\nComprobación: Deben estar formuladas de tal manera que puedan ser aceptadas o rechazadas mediante pruebas estadísticas (Hipótesis Nula vs. Alterna).\nAlineación: Debe haber una Hipótesis General para el Problema General y Hipótesis Específicas para los Específicos."
        },
        {
          "texto": "3.1.1 Operacionalización de variables",
          "nota": "Definición conceptual y operacional, dimensiones e indicadores.",
          "instruccion_detallada": "Es el proceso técnico de convertir conceptos abstractos en datos medibles. Se suele presentar en una matriz (tabla) que contiene:\n\nDefinición Conceptual: Qué es la variable según un autor.\nDefinición Operacional: Cómo se medirá o calculará en este estudio.\nDimensiones: Factores o componentes de la variable.\nIndicadores: La unidad de medida exacta (ej. %, kg, horas, grados).\nEscala de medición: Nominal, Ordinal, de Intervalo o de Razón."
        }
      ]
    },
    {
      "titulo": "IV. METODOLOGÍA",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "4.1 Diseño metodológico",
          "nota": "Conjunto de métodos y procedimientos para recopilar y analizar variables.",
          "instruccion_detallada": "Define la estrategia para probar la hipótesis. Debes especificar y justificar:\n\nTipo de investigación: Básica (teórica) o Aplicada (solución práctica).\nNivel: Exploratorio, Descriptivo, Correlacional o Explicativo.\nDiseño:\nExperimental: Pre-experimental, Cuasi-experimental o Experimental puro (manipulación de variables).\nNo Experimental: Transversal (una medición) o Longitudinal (varias mediciones)."
        },
        {
          "texto": "4.2 Método de investigación",
          "nota": "Procedimientos para lograr los objetivos (Inductivo, Deductivo, etc.).",
          "instruccion_detallada": "Describe el razonamiento lógico utilizado.\n\nGeneralmente en ingeniería se usa el Método Hipotético-Deductivo (parte de una teoría, plantea hipótesis y las deduce/prueba en la realidad) o el Método Cuantitativo (medición numérica y análisis estadístico)."
        },
        {
          "texto": "4.3 Población y muestra",
          "nota": "Universo y subconjunto seleccionado.",
          "instruccion_detallada": "Define quiénes o qué cosas serán medidas.\n\nPoblación: El conjunto total de elementos (personas, máquinas, registros, lotes de producción) con características comunes.\nMuestra: El subconjunto seleccionado para medir. Debes indicar:\nTipo de muestreo: Probabilístico (aleatorio) o No Probabilístico (por conveniencia/criterio).\nCálculo: Presentar la fórmula estadística utilizada para hallar el tamaño de la muestra (n) o sustentar por qué se usó toda la población (censo)."
        },
        {
          "texto": "4.4 Lugar de estudio",
          "nota": "Ubicación geográfica e institucional.",
          "instruccion_detallada": "Ejemplo: Facultad de Ingeniería Eléctrica y Electrónica - UNAC."
        },
        {
          "texto": "4.5 Técnicas e instrumentos de recolección",
          "nota": "Mecanismos para registrar información (Validar por expertos).",
          "instruccion_detallada": "Detalla cómo obtendrás los datos 'crudos'.\n\nTécnicas: El medio de captura (ej. Encuesta, Observación directa, Análisis documental, Medición experimental).\nInstrumentos: La herramienta física o digital (ej. Cuestionario, Ficha de registro de datos, Hoja de verificación, Equipos de medición calibrados).\nValidación y Confiabilidad:\nValidez: Certificado por Juicio de Expertos.\nConfiabilidad: Prueba estadística piloto (Alfa de Cronbach, KR-20) para cuestionarios."
        },
        {
          "texto": "4.6 Análisis y procesamiento de datos",
          "nota": "Transformación de datos en información utilizable.",
          "instruccion_detallada": "Describe cómo transformarás los datos en información.\n\nHerramientas: Mencionar el software (SPSS, Excel, Minitab, Matlab, Python).\nEstadística Descriptiva: Uso de tablas, frecuencias, media, desviación estándar.\nEstadística Inferencial: Especificar las pruebas para la contrastación de hipótesis:\nPrueba de Normalidad (Shapiro-Wilk o Kolmogorov-Smirnov).\nPrueba de Hipótesis (T-Student, U de Mann-Whitney, Wilcoxon, Pearson, Spearman, ANOVA) según la normalidad de los datos."
        },
        {
          "texto": "4.7 Aspectos Éticos",
          "nota": "Cumplimiento de la Conducta Responsable en Investigación (CRI).",
          "instruccion_detallada": "Considerar principios éticos: Respeto por las personas, Beneficencia y Justicia. Evitar plagio y conflictos de interés."
        }
      ]
    },
    {
      "titulo": "V. RESULTADOS",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "5.1 Resultados descriptivos",
          "nota": "Tablas y figuras simples.",
          "instruccion_detallada": "Presenta el análisis exploratorio de los datos.\n\nUtiliza tablas de distribución de frecuencias y gráficos estadísticos (barras, líneas, histogramas) debidamente numerados y titulados según norma (APA/ISO).\nDebajo de cada tabla/figura, redacta una interpretación objetiva de los datos (qué porcentaje es mayor, cuál es la tendencia)."
        },
        {
          "texto": "5.2 Resultados inferenciales",
          "nota": "Contrastación de hipótesis.",
          "instruccion_detallada": "Es la parte crítica de la tesis cuantitativa.\n\nPresenta primero la Prueba de Normalidad para justificar si usas pruebas paramétricas o no paramétricas.\nDesarrolla la Prueba de Hipótesis para la General y las Específicas:\nPlantea H0 (Nula) y H1 (Alterna).\nMuestra el estadístico de prueba y el Valor-p (Sig.).\nToma la decisión estadística: Si p < 0.05, se rechaza la hipótesis nula."
        }
      ]
    },
    {
      "titulo": "VI. DISCUSIÓN DE RESULTADOS",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "6.1 Contrastación y demostración de la hipótesis",
          "nota": "Confrontación con la experiencia y evidencia empírica.",
          "instruccion_detallada": "Realiza la discusión técnica.\n\nAnaliza si la evidencia estadística (Resultados 5.2) respalda o no lo que afirmaste en tu Hipótesis (3.1).\nExplica qué significa este resultado en el contexto de tu problema de ingeniería (ej. 'Se demostró que el nuevo sistema redujo las fallas en un 20%, validando la hipótesis...')."
        },
        {
          "texto": "6.2 Contrastación con otros estudios",
          "nota": "Comparación con antecedentes.",
          "instruccion_detallada": "Triangulación de resultados.\n\nCompara tus hallazgos con los Antecedentes (2.1).\nEjemplo: 'Este resultado coincide con lo hallado por Pérez (2020), quien también observó mejoras...' o 'Difiere de Gómez (2019), posiblemente debido a...'.\nEsto valida la robustez de tu investigación."
        },
        {
          "texto": "6.3 Responsabilidad ética",
          "nota": "Responsabilidad por la información emitida.",
          "instruccion_detallada": "El autor se responsabiliza por la veracidad y rigor ético de los resultados presentados."
        }
      ]
    },
    {
      "titulo": "VII. CONCLUSIONES",
      "nota_capitulo": "Son sentencias directas y precisas que responden a los objetivos.\n\nDeben ser numeradas.\nDebe haber una conclusión por cada objetivo específico y una para el objetivo general.\nDeben incluir datos cuantitativos clave (ej. 'Se determinó que la eficiencia aumentó en 15%...'). No presentar citas ni explicaciones teóricas aquí."
    },
    {
      "titulo": "VIII. RECOMENDACIONES",
      "nota_capitulo": "Sugerencias de acción basadas en las conclusiones.\n\nMetodológicas: Para futuros investigadores (ampliar muestra, cambiar variables).\nAcadémicas: Para la universidad.\nPrácticas: Dirigidas a la empresa o institución (implementar el plan, realizar mantenimientos, capacitar personal). Deben ser viables."
    },
    {
      "titulo": "IX. REFERENCIAS BIBLIOGRÁFICAS",
      "nota_capitulo": "Normas internacionales: ISO 690 o IEEE (Ingenierías), APA o Vancouver (Otras). Uso de gestores como Mendeley o Zotero.",
      "ejemplos_apa": [
        "Hernández-Sampieri, R., & Mendoza, C. (2018). Metodología de la investigación: las rutas cuantitativa, cualitativa y mixta. McGraw-Hill Education.",
        "Creswell, J. W. (2014). Research design: Qualitative, quantitative, and mixed methods approaches (4th ed.). Sage Publications.",
        "Ministerio de Educación del Perú. (2020). Orientaciones para la investigación universitaria. MINEDU."
      ]
    }
  ],
  "finales": {
    "anexos": {
      "titulo_seccion": "ANEXOS",
      "lista": [
        {
          "titulo": "Anexo 1: Matriz de Consistencia",
          "nota": "Resumen lógico de Problemas, Objetivos, Hipótesis, Variables y Método."
        },
        {
          "titulo": "Anexo 2: Instrumento de recolección de datos",
          "nota": "Cuestionario o ficha técnica utilizada."
        },
        {
          "titulo": "Anexo 3: Validación de instrumento",
          "nota": "Constancia de juicio de expertos."
        }
      ]
    }
  },
  "matriz_consistencia": {
    "problemas": {
      "general": "¿De qué manera la implementación de un plan de mantenimiento reduce el tiempo perdido en el área de trapiche?",
      "especificos": [
        "¿Cuál es el diagnóstico inicial midiendo el tiempo perdido?",
        "¿De qué manera realizar un análisis de criticidad?",
        "¿Cómo desarrollar un análisis de modos y efectos de fallas?"
      ]
    },
    "objetivos": {
      "general": "Determinar cómo la implementación de un plan de mantenimiento reduce el tiempo perdido.",
      "especificos": [
        "Realizar un diagnóstico inicial.",
        "Realizar un análisis de criticidad.",
        "Desarrollar un análisis AMEF."
      ]
    },
    "hipotesis": {
      "general": "La implementación de un plan de mantenimiento reduce significativamente el tiempo perdido.",
      "especificos": [
        "El diagnóstico permite identificar causas raíz.",
        "El análisis de criticidad prioriza equipos clave."
      ]
    },
    "variables": {
      "independiente": {
        "nombre": "PLAN DE MANTENIMIENTO",
        "dimensiones": ["Criticidad", "AMEF", "Programación"]
      },
      "dependiente": {
        "nombre": "TIEMPO PERDIDO",
        "dimensiones": ["Disponibilidad", "Confiabilidad"]
      }
    },
    "metodologia": {
      "tipo": "Aplicada",
      "enfoque": "Cuantitativo",
      "nivel": "Explicativo",
      "diseno": "Pre Experimental",
      "poblacion": "32 equipos",
      "muestra": "24 equipos críticos",
      "tecnicas": "Observación",
      "instrumentos": "Ficha de datos",
      "procesamiento": "SPSS v25"
    }
  },
  "version": "2.0.0",
  "descripcion": "Plantilla Oficial Informe de Tesis UNAC - Enfoque Cuantitativo (Directiva 004-2022-R)"
}
```

---

## app/data/unac/informe/unac_informe_cuant.json
**Tama?o:** 21909
**SHA256:** 25ec488407e36cba6ee9b14ed8a2f422d387621d3240bddcd19f662606b70ca4
**Tipo:** json

```json
{
  "caratula": {
    "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
    "facultad": "FACULTAD DE [NOMBRE DE LA FACULTAD]",
    "escuela": "ESCUELA PROFESIONAL DE [NOMBRE DE LA ESCUELA]",
    "tipo_documento": "INFORME DE TESIS",
    "titulo_placeholder": "\"[ESCRIBA AQUÍ EL TÍTULO DE LA TESIS CUANTITATIVA]\"",
    "frase_grado": "PARA OPTAR EL TÍTULO PROFESIONAL DE:",
    "grado_objetivo": "[INGENIERO DE ...]",
    "label_autor": "AUTOR: [NOMBRES Y APELLIDOS]",
    "label_asesor": "ASESOR: [NOMBRES Y APELLIDOS]",
    "label_linea": "LÍNEA DE INVESTIGACIÓN: [NOMBRE DE LA LÍNEA]",
    "fecha": "Callao, 2026",
    "pais": "PERÚ"
  },
  "preliminares": {
    "dedicatoria": {
      "titulo": "DEDICATORIA / AGRADECIMIENTO",
      "texto": "[Escriba aquí su dedicatoria o agradecimientos...]"
    },
    "resumen": {
      "titulo": "RESUMEN / ABSTRACT",
      "nota": "Nota: Síntesis de objetivos, métodos y resultados principales.",
      "texto": "\n[Escriba aquí el cuerpo del resumen. Debe contener el objetivo, el método, los resultados y las conclusiones principales. No exceder las 200 palabras.]"
    },
    "indices": {
      "contenido": "ÍNDICE DE CONTENIDO",
      "tablas": "ÍNDICE DE TABLAS",
      "figuras": "ÍNDICE DE FIGURAS",
      "abreviaturas": "ÍNDICE DE ABREVIATURAS",
      "placeholder": "(Generarlo)"
    },
    "introduccion": {
      "titulo": "INTRODUCCIÓN",
      "texto": "[La introducción informa tres elementos muy importantes: El propósito, la importancia de la investigación y el conocimiento actual del tema.]"
    }
  },
  "cuerpo": [
    {
      "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "1.1 Descripción de la realidad problemática",
          "instruccion_detallada": "En este apartado debes presentar y contextualizar claramente el problema basándote en evidencia objetiva, datos y hechos, utilizando un enfoque deductivo (de lo general a lo específico).\n\nDebes desarrollar el contenido considerando tres niveles de análisis:\n\n- Contexto internacional: Describe cómo se comporta la variable o el problema a nivel mundial o regional. Usa estadísticas, informes de organismos internacionales (ONU, Banco Mundial, etc.) o tendencias globales que demuestren la relevancia del tema.\n- Contexto nacional: Explica la situación del problema en el Perú. Cita normativas, informes ministeriales, planes nacionales o datos estadísticos del INEI que evidencien la deficiencia o necesidad a nivel país.\n- Contexto institucional o local: Describe la realidad específica en la empresa, área o lugar de estudio. Detalla los síntomas observables (fallas, demoras, pérdidas, quejas) con datos preliminares si es posible.\n- Sustento ingenieril (Obligatorio): Debes aplicar al menos una herramienta de ingeniería para diagnosticar técnicamente el problema, tal como:\n  * Diagrama de Ishikawa (Causa-Efecto).\n  * Diagrama de Pareto (80/20).\n  * Árbol de problemas.\n  * Matriz de Vester o Matriz de Priorización.\n- Cierre: Finaliza mencionando explícitamente la propuesta de solución técnica (ej. 'Por lo expuesto, se propone la implementación de...')."
        },
        {
          "texto": "1.2 Formulación del problema",
          "instruccion_detallada": "Estructura formalmente la idea de investigación mediante preguntas claras y precisas que relacionen las variables de estudio.\n\n- Problema General: Es la interrogante principal que engloba la relación entre la Variable Independiente y la Dependiente (o la variable única en estudios descriptivos). Debe formularse de manera que invite a la medición o prueba estadística.\n  * Ejemplo: ¿De qué manera la implementación de X influye en Y?\n- Problemas Específicos: Son sub-preguntas que desglosan el análisis. Generalmente relacionan las Dimensiones de la Variable Independiente con la Variable Dependiente o sus dimensiones. Deben ser medibles y concretas."
        },
        {
          "texto": "1.3 Objetivos",
          "instruccion_detallada": "Expresan el fin medible y verificable que se pretende lograr con la investigación. Deben iniciar con un verbo en infinitivo fuerte (Determinar, Evaluar, Diseñar, Establecer) y ser congruentes con los problemas formulados.\n\n- Objetivo General: El logro final del estudio que responde directamente al problema general.\n- Objetivos Específicos: Los pasos intermedios, operativos o secuenciales necesarios para alcanzar el objetivo general (responden a los problemas específicos)."
        },
        {
          "texto": "1.4 Justificación",
          "instruccion_detallada": "Explica las razones por las cuales es necesario y útil realizar el estudio. Debes redactar los siguientes enfoques:\n\n- Justificación Técnica/Práctica: ¿Qué problema real resuelve? ¿Cómo mejora la eficiencia, productividad, seguridad o costos en la entidad de estudio?\n- Justificación Teórica: ¿Cómo aplica, valida o contrasta conocimientos de ingeniería existentes? ¿Llena algún vacío de conocimiento?\n- Justificación Metodológica: ¿Utiliza algún instrumento, software, algoritmo o método de análisis novedoso o riguroso que sirva de modelo para futuras investigaciones?\n- Justificación Económica/Social: ¿Cuál es el beneficio costo-beneficio para la empresa? ¿Cuál es el impacto positivo en la sociedad, trabajadores o medio ambiente?"
        },
        {
          "texto": "1.5 Delimitantes de la investigación",
          "instruccion_detallada": "Define las fronteras y alcances del estudio para asegurar su viabilidad técnica y operativa:\n\n- Delimitación Temática: Línea de investigación de la escuela o área específica de la ingeniería (ej. Mantenimiento, Telecomunicaciones, Control, Software).\n- Delimitación Espacial: Lugar exacto donde se tomarán los datos o se realizará la implementación (Nombre de la Empresa, Área específica, Ciudad).\n- Delimitación Temporal: Periodo de tiempo que abarca la recolección y análisis de datos (ej. Datos históricos de 2023 o mediciones de campo de Enero a Junio 2024)."
        }
      ]
    },
    {
      "titulo": "II. MARCO TEÓRICO",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "2.1 Antecedentes (Internacional y nacional)",
          "instruccion_detallada": "Presenta el 'estado del arte' revisando investigaciones previas. Debes buscar tesis o artículos científicos (papers) indexados, preferiblemente de los últimos 5 a 10 años.\n\nEstructura de cada antecedente: Debes redactar en forma de párrafo fluido (no viñetas aisladas) incluyendo obligatoriamente:\n- Apellido del autor y Año.\n- Título de la investigación.\n- Objetivo principal del estudio.\n- Metodología empleada (Diseño, muestra, instrumentos).\n- Resultados numéricos más relevantes (datos estadísticos, mejoras porcentuales, correlaciones).\n- Conclusiones principales.\n\nCantidad: Se recomienda un promedio de 5 antecedentes internacionales y 5 nacionales para pregrado (o 20-30 referencias totales para posgrado)."
        },
        {
          "texto": "2.2 Bases teóricas",
          "instruccion_detallada": "Es el sustento científico y técnico de la tesis.\n\n- Desarrollo: Analiza sistemáticamente las teorías, leyes, principios, modelos matemáticos o físicos que explican tus variables (Variable Independiente y Dependiente).\n- Rigor: No es un glosario ni un 'copiar y pegar'; debes interpretar la teoría, sintetizarla y citar fuentes confiables (Libros de especialidad, IEEE, normas técnicas, papers).\n- Fundamentación: Incluir brevemente el enfoque epistemológico (positivista/cuantitativo) que guía el estudio, validando el uso del método científico."
        },
        {
          "texto": "2.3 Marco conceptual",
          "instruccion_detallada": "Elabora 'constructos' o definiciones teóricas específicas para tu investigación.\n\n- Diferencia: A diferencia de las bases teóricas (que explican el funcionamiento y leyes), aquí defines conceptualmente las variables y sus dimensiones basándote en la literatura revisada para este contexto específico.\n- Propósito: Establecer con claridad y sin ambigüedades qué se entiende por cada concepto clave dentro de *tu* investigación."
        },
        {
          "texto": "2.4 Definición de términos básicos",
          "instruccion_detallada": "Es un glosario técnico funcional a la investigación.\n\nInstrucción: Define términos técnicos especializados que se usan en la tesis y que podrían prestarse a confusión. Las definiciones deben ser precisas, citadas y funcionales para evitar ambigüedades en la interpretación de los resultados."
        }
      ]
    },
    {
      "titulo": "III. HIPÓTESIS Y VARIABLES",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "3.1 Hipótesis (General y específicas)",
          "instruccion_detallada": "Son las respuestas tentativas y probables a los problemas formulados.\n\n- Requisito: Deben ser proposiciones afirmativas que establezcan una relación clara (causa-efecto, correlación, diferencia de grupos) entre las variables.\n- Comprobación: Deben estar formuladas de tal manera que puedan ser aceptadas o rechazadas mediante pruebas estadísticas (Hipótesis Nula vs. Alterna).\n- Alineación: Debe existir una Hipótesis General para el Problema General y Hipótesis Específicas para cada Problema Específico."
        },
        {
          "texto": "3.1.1 Operacionalización de variables",
          "instruccion_detallada": "Es el proceso técnico fundamental de convertir conceptos abstractos en datos medibles. Se suele presentar en una matriz (tabla) que contiene:\n\n- Definición Conceptual: Qué es la variable teóricamente según un autor.\n- Definición Operacional: Cómo se medirá, calculará o manipulará en este estudio específico.\n- Dimensiones: Factores, componentes o grandes aspectos de la variable.\n- Indicadores: La unidad de medida exacta y observable (ej. %, kg, horas, grados, puntaje).\n- Escala de medición: Nominal, Ordinal, de Intervalo o de Razón."
        }
      ]
    },
    {
      "titulo": "IV. METODOLOGÍA",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "4.1 Diseño metodológico",
          "instruccion_detallada": "Define la estrategia operativa para probar la hipótesis. Debes especificar y justificar técnicamente:\n\n- Tipo de investigación: Básica (teórica/pura) o Aplicada (solución práctica/tecnológica).\n- Nivel: Exploratorio, Descriptivo, Correlacional o Explicativo (Causal).\n- Diseño:\n  * Experimental: Pre-experimental, Cuasi-experimental o Experimental puro (si manipulas deliberadamente la variable independiente).\n  * No Experimental: Transversal (una sola medición en el tiempo) o Longitudinal (varias mediciones a lo largo del tiempo)."
        },
        {
          "texto": "4.2 Método de investigación",
          "instruccion_detallada": "Describe el razonamiento lógico utilizado para la obtención de conocimiento.\n\nInstrucción: Generalmente en ingeniería se usa el Método Hipotético-Deductivo (parte de una teoría general, plantea hipótesis y las deduce/prueba en la realidad particular) o el Método Cuantitativo (basado en la medición numérica y el análisis estadístico objetivo)."
        },
        {
          "texto": "4.3 Población y muestra",
          "instruccion_detallada": "Define quiénes o qué cosas serán medidas y analizadas.\n\n- Población: El conjunto total de elementos (personas, máquinas, registros, lotes de producción, expedientes) con características comunes observables.\n- Muestra: El subconjunto representativo seleccionado para medir. Debes indicar:\n  * Tipo de muestreo: Probabilístico (aleatorio simple, estratificado) o No Probabilístico (por conveniencia, criterio de expertos).\n  * Cálculo: Presentar la fórmula estadística utilizada para hallar el tamaño de la muestra (n) con sus parámetros (error, confianza) o sustentar por qué se usó toda la población (censo)."
        },
        {
          "texto": "4.4 Lugar de estudio",
          "instruccion_detallada": "Describe el entorno físico.\n\nInstrucción: Ubicación geográfica e institucional exacta donde se recolectan los datos (Dirección, Ciudad, Departamento, País)."
        },
        {
          "texto": "4.5 Técnicas e instrumentos de recolección",
          "instruccion_detallada": "Detalla cómo obtendrás los datos 'crudos' de la realidad.\n\n- Técnicas: El medio o procedimiento de captura (ej. Encuesta, Observación directa, Análisis documental, Medición experimental con equipos).\n- Instrumentos: La herramienta física o digital de registro (ej. Cuestionario, Ficha de registro de datos, Hoja de verificación, Equipos de medición calibrados).\n- Validación y Confiabilidad:\n  * Validez: Mencionar si fue validado por Juicio de Expertos (adjuntar constancias en anexos).\n  * Confiabilidad: Indicar la prueba estadística piloto realizada (Alfa de Cronbach para encuestas, KR-20, o análisis de repetibilidad para instrumentos mecánicos)."
        },
        {
          "texto": "4.6 Análisis y procesamiento de datos",
          "instruccion_detallada": "Describe cómo transformarás los datos brutos en información útil y conclusiones.\n\n- Herramientas: Mencionar el software utilizado (SPSS, Excel, Minitab, Matlab, Python, etc.).\n- Estadística Descriptiva: Uso de tablas de frecuencia, medidas de tendencia central (media, mediana) y dispersión (desviación estándar).\n- Estadística Inferencial: Especificar las pruebas para la contrastación de hipótesis:\n  * Prueba de Normalidad (Shapiro-Wilk o Kolmogorov-Smirnov).\n  * Prueba de Hipótesis (T-Student, U de Mann-Whitney, Wilcoxon, Pearson, Spearman, ANOVA) seleccionada según la normalidad de los datos."
        },
        {
          "texto": "4.7 Aspectos Éticos",
          "instruccion_detallada": "Declaración de integridad científica.\n\nInstrucción: Declaración explícita del cumplimiento de principios éticos (beneficencia, justicia, autonomía) y la Conducta Responsable en Investigación (CRI). Mencionar el cuidado del anonimato, el uso de consentimiento informado y la originalidad del trabajo (anti-plagio)."
        }
      ]
    },
    {
      "titulo": "V. RESULTADOS",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "5.1 Resultados descriptivos",
          "instruccion_detallada": "Presenta el análisis exploratorio de los datos recolectados.\n\nInstrucción: Utiliza tablas de distribución de frecuencias y gráficos estadísticos (barras, líneas, histogramas, sectores) debidamente numerados y titulados según norma (APA/ISO). Debajo de cada tabla/figura, redacta una interpretación objetiva de los datos (qué porcentaje es mayor, cuál es la tendencia, qué dato resalta). No emitas juicios de valor aquí, solo describe los datos."
        },
        {
          "texto": "5.2 Resultados inferenciales",
          "instruccion_detallada": "Es la parte crítica de la tesis cuantitativa donde se prueban las hipótesis.\n\nInstrucción:\n1. Presenta primero la Prueba de Normalidad para justificar si usas pruebas paramétricas o no paramétricas.\n2. Desarrolla la Prueba de Hipótesis para la General y las Específicas:\n  * Plantea estadísticamente H0 (Nula) y H1 (Alterna).\n  * Muestra el estadístico de prueba calculado y el Valor-p (Sig.).\n  * Toma la decisión estadística: 'Como p < 0.05, se rechaza la hipótesis nula y se acepta la alterna'."
        }
      ]
    },
    {
      "titulo": "VI. DISCUSIÓN DE RESULTADOS",
      "vista_previa": true,
      "tipo_vista": "pdf_capitulo",
      "contenido": [
        {
          "texto": "6.1 Contrastación y demostración de la hipótesis",
          "instruccion_detallada": "Realiza la discusión técnica de los hallazgos inferenciales.\n\nInstrucción: Analiza si la evidencia estadística obtenida (en el cap. 5.2) respalda o no lo que afirmaste teóricamente en tu Hipótesis (cap. 3.1). Explica qué significa este resultado en el contexto de tu problema de ingeniería (ej. 'Se demostró estadísticamente que el nuevo sistema redujo las fallas en un 20%, validando la hipótesis de mejora...')."
        },
        {
          "texto": "6.2 Contrastación con otros estudios",
          "instruccion_detallada": "Triangulación de resultados para dar validez externa.\n\nInstrucción: Compara tus hallazgos con los Antecedentes presentados en el capítulo 2.1.\n* Ejemplo: 'Este resultado coincide con lo hallado por Pérez (2020), quien también observó mejoras significativas...' o 'Difiere de Gómez (2019), posiblemente debido a las diferentes condiciones de...'.\nEsto valida la robustez y coherencia de tu investigación frente al conocimiento existente."
        },
        {
          "texto": "6.3 Responsabilidad ética",
          "instruccion_detallada": "Declaración final de integridad sobre los resultados.\n\nInstrucción: El autor asume la responsabilidad por la veracidad, autenticidad y el rigor científico de los datos presentados, asegurando que no han sido manipulados ni fabricados."
        }
      ]
    },
    {
      "titulo": "VII. CONCLUSIONES",
      "nota_capitulo": "Son sentencias directas, precisas y numeradas que responden a los objetivos planteados.\n\nInstrucción:\n- Deben ser numeradas.\n- Debe haber al menos una conclusión por cada objetivo específico y una para el objetivo general.\n- Deben incluir datos cuantitativos clave hallados en la investigación (ej. 'Se determinó que la eficiencia aumentó en 15%...', 'Existe una correlación positiva alta de 0.85...').\n- No presentar citas de autores ni explicaciones teóricas aquí, solo hallazgos directos."
    },
    {
      "titulo": "VIII. RECOMENDACIONES",
      "nota_capitulo": "Sugerencias de acción prácticas y viables basadas en las conclusiones.\n\nInstrucción:\n- Metodológicas: Para futuros investigadores (ej. ampliar muestra, incluir nuevas variables, usar otro diseño).\n- Académicas: Para la universidad o línea de investigación.\n- Prácticas: Dirigidas a la empresa o institución estudiada (ej. implementar el plan diseñado, realizar mantenimientos periódicos, capacitar al personal en X). Deben ser acciones concretas y realizables."
    },
    {
      "titulo": "IX. REFERENCIAS BIBLIOGRÁFICAS",
      "nota_capitulo": "Listado riguroso según norma (ISO 690/IEEE para Ingeniería, APA otras). Usar gestores bibliográficos.",
      "ejemplos_apa": [
        "Chávez, S. (2018). Manual de gestión de mantenimiento. Editorial Universitaria.",
        "Rodriguez, M. A. (2020). Implementación de un plan de mantenimiento preventivo. Tesis de Ingeniería, Universidad Nacional del Callao.",
        "Pérez, J., & Gómez, L. (2019). Reliability analysis in industrial systems. IEEE Transactions on Reliability, 68(2), 450-460."
      ]
    }
  ],
  "finales": {
    "anexos": {
      "titulo_seccion": "ANEXOS",
      "lista": [
        {
          "titulo": "Anexo 1: Matriz de Consistencia",
          "nota": "Resumen lógico de Problemas, Objetivos, Hipótesis, Variables y Método (Generado automáticamente)."
        },
        {
          "titulo": "Anexo 2: Instrumento de recolección de datos",
          "nota": "Adjuntar el Cuestionario, Ficha de Registro o Ficha Técnica de los equipos."
        },
        {
          "titulo": "Anexo 3: Validación de instrumento",
          "nota": "Constancia de juicio de expertos y fiabilidad."
        }
      ]
    }
  },
  "matriz_consistencia": {
    "problemas": {
      "general": "¿De qué manera la implementación de un plan de mantenimiento reduce el tiempo perdido en el área de trapiche?",
      "especificos": [
        "¿Cuál es el diagnóstico inicial midiendo el tiempo perdido?",
        "¿De qué manera realizar un análisis de criticidad?",
        "¿Cómo desarrollar un análisis de modos y efectos de fallas?"
      ]
    },
    "objetivos": {
      "general": "Determinar cómo la implementación de un plan de mantenimiento reduce el tiempo perdido.",
      "especificos": [
        "Realizar un diagnóstico inicial.",
        "Realizar un análisis de criticidad.",
        "Desarrollar un análisis AMEF."
      ]
    },
    "hipotesis": {
      "general": "La implementación de un plan de mantenimiento reduce significativamente el tiempo perdido.",
      "especificos": [
        "El diagnóstico permite identificar causas raíz.",
        "El análisis de criticidad prioriza equipos clave."
      ]
    },
    "variables": {
      "independiente": {
        "nombre": "PLAN DE MANTENIMIENTO",
        "dimensiones": ["Criticidad", "AMEF", "Programación"]
      },
      "dependiente": {
        "nombre": "TIEMPO PERDIDO",
        "dimensiones": ["Disponibilidad", "Confiabilidad"]
      }
    },
    "metodologia": {
      "tipo": "Aplicada",
      "enfoque": "Cuantitativo",
      "nivel": "Explicativo",
      "diseno": "Pre Experimental",
      "poblacion": "32 equipos",
      "muestra": "24 equipos críticos",
      "tecnicas": "Observación",
      "instrumentos": "Ficha de datos",
      "procesamiento": "SPSS v25"
    }
  },
  "version": "2.0.0",
  "descripcion": "Plantilla Oficial Informe de Tesis UNAC - Enfoque Cuantitativo (Directiva 004-2022-R)"
}
```

---

## app/data/unac/maestria/unac_maestria_cual.json
**Tama?o:** 16843
**SHA256:** 3c880ac2178b3be50ea26aa2d5c253da665446c6c272bd15d1349984ecde90a2
**Tipo:** json

```json
{
  "caratula": {
    "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
    "facultad": "ESCUELA DE POSGRADO",
    "escuela": "UNIDAD DE POSGRADO DE LA FACULTAD DE [FACULTAD]",
    "tipo_documento": "TESIS DE MAESTRÍA",
    "titulo_placeholder": "\"[TÍTULO COMPLETO DEL TRABAJO]\"",
    "frase_grado": "PARA OPTAR EL GRADO ACADÉMICO DE:",
    "grado_objetivo": "MAESTRO EN [NOMBRE EXACTO DEL PROGRAMA]",
    "label_autor": "AUTOR(ES)\n[NOMBRES Y APELLIDOS]",
    "label_asesor": "ASESOR\n[NOMBRES Y APELLIDOS]",
    "label_linea": "LÍNEA DE INVESTIGACIÓN: [NOMBRE DE LA LÍNEA]",
    "fecha": "Callao, [AÑO]",
    "pais": "PERÚ",
    "guia": "Contiene: variables, unidad de análisis, ámbito de estudio y temporalidad.\nMáx. 15 palabras; sin conectores ni nombres."
  },
  "preliminares": {
    "dedicatoria": {
      "titulo": "DEDICATORIA",
      "texto": "[Escriba aquí su dedicatoria…]"
    },
    "agradecimientos": {
      "titulo": "AGRADECIMIENTO",
      "texto": "[Escriba aquí su agradecimiento…]"
    },
    "abreviaturas": {
      "titulo": "ÍNDICE DE ABREVIATURAS",
      "nota": "Colocar el significado de las abreviaturas utilizadas en la investigación.",
      "ejemplo": "ORGANIZACIÓN MUNDIAL DE LA SALUD (OMS)"
    },
    "indices": {
      "contenido": "ÍNDICE DE CONTENIDO",
      "tablas": "ÍNDICE DE TABLAS",
      "figuras": "ÍNDICE DE FIGURAS",
      "abreviaturas": "ÍNDICE DE ABREVIATURAS",
      "placeholder": "(Generarlo)"
    },
    "hoja_jurado": {
      "titulo": "HOJA DE REFERENCIA DEL JURADO Y APROBACIÓN",
      "miembros": [
        {
          "name": "[Nombre]",
          "role": "PRESIDENTE"
        },
        {
          "name": "[Nombre]",
          "role": "SECRETARIO"
        },
        {
          "name": "[Nombre]",
          "role": "MIEMBRO"
        },
        {
          "name": "[Nombre]",
          "role": "MIEMBRO"
        }
      ],
      "asesor": "[ASESOR]",
      "acta": {
        "libro": "[N°]",
        "actas": "[N°]",
        "folio": "[N°]",
        "fecha": "[dd de mes de aaaa]",
        "resolucion": "[Código]"
      }
    },
    "introduccion": {
      "titulo": "INTRODUCCIÓN",
      "texto": "Manifiesta la importancia y las razones por que realiza la tesis de maestría. Referencie trabajos similares anteriormente publicados (nacionales e internacionales), mencione los objetivos de estudio, la problemática y las soluciones.\n\nAsimismo, presente una descripción de la estructura del documento (máximo 02 páginas)."
    }
  },
  "cuerpo": [
    {
      "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
      "contenido": [
        {
          "texto": "1.1 Descripción de la realidad problemática",
          "instruccion_detallada": "Describe, explica y evidencia la realidad problemática en el contexto internacional y/o nacional y, cuando corresponda, en el contexto institucional.\n\nSustente la identificación del problema relevante y evidencie el análisis de la problemática utilizando al menos una herramienta de ingeniería (por ejemplo: Pareto, Ishikawa, Árbol de problemas, Matriz de relevancia, Matriz de priorización, entre otras).\n\nSe debe mencionar la propuesta de solución del problema de investigación.",
          "imagenes": [
            {
              "titulo": "Figura 1.1. Herramienta de ingeniería (ejemplo)",
              "ruta": "placeholder",
              "fuente": "Ejemplo de figura. Reemplace por un gráfico/diagrama real (Pareto, Ishikawa, árbol de problemas, etc.) con fuente."
            }
          ]
        },
        {
          "texto": "1.2 Formulación del problema",
          "instruccion_detallada": "Formule el problema general y los problemas específicos. Redacte en forma interrogativa, clara y medible."
        },
        {
          "texto": "1.3 Objetivos",
          "instruccion_detallada": "Redacte un objetivo general y objetivos específicos, coherentes con el problema y medibles."
        },
        {
          "texto": "1.4 Justificación e importancia",
          "instruccion_detallada": "Sustente la relevancia teórica, práctica, social e institucional. Indique beneficiarios y aportes."
        },
        {
          "texto": "1.5 Limitaciones",
          "instruccion_detallada": "Indique limitaciones (tiempo, acceso a información, recursos) y cómo se mitigarán."
        }
      ]
    },
    {
      "titulo": "II. REVISIÓN DE LA LITERATURA",
      "contenido": [
        {
          "texto": "2.1 Antecedentes",
          "instruccion_detallada": "Los antecedentes de la presente investigación son el reflejo de una búsqueda exhaustiva en bases de datos científicas, repositorios universitarios y fuentes oficiales relacionadas al tema de estudio.\n\nPara cada antecedente, indique: autor(es), año, título, objetivo, metodología (tipo/enfoque/diseño), población/muestra, instrumentos, resultados y la conclusión principal que aporta a su investigación.\n\nOrganice en: antecedentes internacionales y nacionales."
        },
        {
          "texto": "2.1.1 Antecedentes internacionales",
          "instruccion_detallada": "Presente antecedentes internacionales con el formato: autor(año), título, objetivo, metodología, resultados y conclusión."
        },
        {
          "texto": "2.1.2 Antecedentes nacionales",
          "instruccion_detallada": "Presente antecedentes nacionales con el mismo formato. Relacione explícitamente el aporte al presente estudio."
        },
        {
          "texto": "2.2 Marco conceptual",
          "instruccion_detallada": "Defina términos clave del estudio. Incluya definiciones operacionales si aplica.",
          "imagenes": [
            {
              "titulo": "Figura 2.1. Modelo conceptual / esquema (ejemplo)",
              "ruta": "placeholder",
              "fuente": "Ejemplo de figura para visualizar el formato. Reemplace por un esquema/modelo/diagrama propio con fuente."
            }
          ]
        },
        {
          "texto": "2.3 Definición de términos básicos",
          "instruccion_detallada": "Defina los términos clave que se usarán en la investigación (conceptos técnicos, categorías, actores, etc.). Use definiciones operativas alineadas al contexto del estudio."
        }
      ]
    },
    {
      "titulo": "III. METODOLOGÍA DEL PROYECTO",
      "contenido": [
        {
          "texto": "3.1 Categorías, subcategorías y matriz de categorización",
          "instruccion_detallada": "Defina categorías y subcategorías (si aplica). Explique cómo se observarán/interpretarán.",
          "tabla": {
            "headers": [
              "Categoría",
              "Subcategoría",
              "Definición operativa",
              "Técnica/Instrumento"
            ],
            "rows": [
              [
                "Gestión del proceso",
                "Planificación",
                "Cómo se organiza y planifica la ejecución del proceso en el contexto del estudio.",
                "Entrevista semiestructurada"
              ],
              [
                "Gestión del proceso",
                "Ejecución",
                "Cómo se ejecuta y controla el proceso en la práctica.",
                "Guía de observación"
              ],
              [
                "Percepción",
                "Satisfacción",
                "Percepciones de los participantes sobre el fenómeno estudiado.",
                "Entrevista / Grupo focal"
              ]
            ]
          },
          "tabla_titulo": "Tabla 3.1. Matriz de categorización (ejemplo)",
          "tabla_nota": "Ejemplo de tabla. Reemplace por su matriz de operacionalización completa."
        },
        {
          "texto": "3.2 Escenario de estudio",
          "instruccion_detallada": "Describa el contexto donde se realizará el estudio: institución/empresa, ubicación, condiciones relevantes y por qué es un escenario pertinente."
        },
        {
          "texto": "3.3 Participantes",
          "instruccion_detallada": "Describa población, criterios, muestra y técnica de muestreo. Indique tamaño final."
        },
        {
          "texto": "3.4 Técnicas e instrumentos de recolección de datos",
          "instruccion_detallada": "Detalle técnica(s) e instrumento(s). Incluya validez (juicio de expertos) y confiabilidad (Alfa de Cronbach u otro)."
        },
        {
          "texto": "3.5 Procedimiento",
          "instruccion_detallada": "Explique el procedimiento paso a paso y el plan de análisis (estadística descriptiva e inferencial)."
        },
        {
          "texto": "3.6 Rigor científico",
          "instruccion_detallada": "Explique credibilidad, transferibilidad, dependencia y confirmabilidad. Indique técnicas para asegurar rigor."
        },
        {
          "texto": "3.7 Método de análisis de datos",
          "instruccion_detallada": "Describa el enfoque de análisis (análisis temático, teoría fundamentada, análisis de contenido, etc.), codificación (abierta/axial/selectiva) y uso de software si aplica (NVivo, Atlas.ti)."
        },
        {
          "texto": "3.8 Aspectos Éticos en Investigación",
          "instruccion_detallada": "Incluya consentimiento informado, confidencialidad, resguardo de datos, y aprobación institucional si corresponde."
        }
      ],
      "nota_capitulo": "Describe el diseño cualitativo y cómo se recolectará y analizará la información. Incluya categorías, escenario, participantes, técnicas, procedimiento, rigor científico y aspectos éticos."
    },
    {
      "titulo": "IV. RESULTADOS",
      "contenido": [
        {
          "texto": "4.1 Presentación de resultados",
          "instruccion_detallada": "Presente los resultados de manera ordenada según objetivos/hipótesis.\n\nIncluya tablas y figuras numeradas, con títulos claros y fuente cuando corresponda.\n\nEvite interpretación extensa en esta sección; la discusión va en el apartado correspondiente.",
          "tabla": {
            "headers": [
              "Categoría",
              "Evidencia (cita/paráfrasis)",
              "Interpretación"
            ],
            "rows": [
              [
                "Planificación",
                "\"...\" (Entrevistado 1)",
                "Se evidencia planificación informal sin métricas."
              ],
              [
                "Ejecución",
                "\"...\" (Entrevistado 2)",
                "Se observa variabilidad en la ejecución del proceso."
              ]
            ]
          },
          "tabla_titulo": "Tabla 4.1. Resultados por categoría (ejemplo)",
          "tabla_nota": "Ejemplo de tabla de resultados. Reemplace por sus resultados reales e incluya fuente si aplica."
        }
      ],
      "nota_capitulo": "Presente los hallazgos organizados por categorías/subcategorías. Incluya tablas o figuras solo cuando ayuden a resumir o visualizar resultados."
    },
    {
      "titulo": "V. DISCUSIÓN DE RESULTADOS",
      "contenido": [
        {
          "texto": "5.1 Discusión",
          "instruccion_detallada": "Interprete y compare los resultados con la literatura (antecedentes y bases teóricas).\n\nExplique coincidencias y discrepancias, implicancias prácticas, y limitaciones del estudio."
        }
      ],
      "nota_capitulo": "Interprete y contraste los hallazgos con la literatura revisada. Explique coincidencias, diferencias y aportes del estudio."
    },
    {
      "titulo": "VI. CONCLUSIONES",
      "contenido": [
        {
          "texto": "6.1 Conclusiones",
          "instruccion_detallada": "Redacte conclusiones directas y numeradas, alineadas a los objetivos e hipótesis.\n\nAñada recomendaciones aplicables y, si corresponde, propuestas de investigación futura."
        }
      ],
      "nota_capitulo": "Sintetice los principales hallazgos y responda a los objetivos planteados."
    },
    {
      "titulo": "VII. RECOMENDACIONES",
      "contenido": [
        {
          "texto": "7.1 Recomendaciones",
          "instruccion_detallada": "Presente recomendaciones aplicables para la institución/sector y sugerencias para futuras investigaciones."
        }
      ],
      "nota_capitulo": "Proponga acciones, mejoras o futuras líneas de investigación en función de los hallazgos."
    }
  ],
  "finales": {
    "referencias": {
      "titulo": "VIII. REFERENCIAS BIBLIOGRÁFICAS",
      "nota": "Liste todas las fuentes citadas en el texto. Use un estilo de citación consistente (según norma indicada por su programa).\n\nVerifique: autor, año, título, editorial/revista, volumen(número), páginas, DOI/URL.\n\nIncluya solo referencias citadas en el texto. Orden alfabético. Use estilo APA (última edición indicada por la UNAC).",
      "ejemplos_apa": [
        "Ejemplos (formato referencial):",
        "Hernández, R., Fernández, C., & Baptista, P. (2018). Metodología de la investigación (6.a ed.). McGraw-Hill.",
        "Oblitas, M., & Villegas, M. (2023). Gestión de la calidad y desempeño organizacional. Revista Científica UNAC, 12(2), 45–60.",
        "Organización Mundial de la Salud. (2021). Título del documento. Sitio web institucional. https://ejemplo.org"
      ]
    },
    "anexos": {
      "titulo_seccion": "ANEXOS",
      "nota": "Incluya instrumentos, matrices (consistencia, operacionalización), evidencias, y documentos complementarios.\n\nNumere los anexos y refiéralos dentro del texto cuando corresponda.",
      "lista": [
        {
          "titulo": "ANEXO 1. Matriz de consistencia (ejemplo completo)",
          "nota": "Incluya la matriz de consistencia completa (problema, objetivos, hipótesis si aplica, variables, metodología).",
          "tabla": {
            "headers": [
              "Problema",
              "Objetivo",
              "Hipótesis",
              "Variables",
              "Metodología"
            ],
            "rows": [
              [
                "¿Problema general?",
                "Objetivo general",
                "Hipótesis general",
                "VI/VD",
                "Tipo/diseño/nivel"
              ],
              [
                "Problema específico 1",
                "Objetivo específico 1",
                "Hipótesis específica 1",
                "Indicadores",
                "Población/muestra"
              ]
            ]
          },
          "tabla_titulo": "Tabla A1. Matriz de consistencia (ejemplo)",
          "tabla_nota": "Ejemplo de anexo. Reemplace cada celda con su información real."
        },
        {
          "titulo": "ANEXO 2. Instrumento / evidencias (ejemplo completo)",
          "nota": "Adjunte el instrumento (cuestionario, guía de entrevista, ficha) y/o evidencias necesarias.",
          "parrafos": [
            "Instrumento (ejemplo):",
            "1) Pregunta 1: ________________________________",
            "2) Pregunta 2: ________________________________",
            "3) Pregunta 3: ________________________________",
            "",
            "Evidencia (ejemplo): actas, resoluciones, autorizaciones, fotografías u otros documentos pertinentes."
          ]
        }
      ]
    }
  },
  "version": "1.0.0",
  "descripcion": "Plantilla oficial de tesis de maestría (legacy).",
  "informacion_basica": {
    "titulo": "INFORMACIÓN BÁSICA",
    "elementos": [
      {
        "label": "FACULTAD:",
        "valor": "[FACULTAD]"
      },
      {
        "label": "UNIDAD DE INVESTIGACIÓN:",
        "valor": "[Unidad de Investigación]"
      },
      {
        "label": "TÍTULO:",
        "valor": "[TÍTULO DE TESIS]"
      },
      {
        "label": "AUTOR(ES) / CÓDIGO ORCID / DNI:",
        "valor": "[AUTOR]\nCódigo orcid:[0000-0000-0000-0000]\nDNI:[00000000]"
      },
      {
        "label": "ASESOR / COASESOR / CÓDIGO ORCID / DNI:",
        "valor": "[ASESOR]\nCódigo orcid:[0000-0000-0000-0000]\nDNI:[00000000]"
      },
      {
        "label": "LUGAR DE EJECUCIÓN:",
        "valor": "[Lugar de ejecución]"
      },
      {
        "label": "UNIDAD DE ANÁLISIS:",
        "valor": "[Unidad de análisis]"
      },
      {
        "label": "INVESTIGACIÓN:",
        "valor": "TIPO: [Tipo] / ENFOQUE: CUALITATIVO / DISEÑO: [Diseño] / NIVEL: [Nivel]"
      },
      {
        "label": "TEMA OCDE:",
        "valor": "[Código y descripción OCDE]"
      }
    ]
  }
}
```

---

## app/data/unac/maestria/unac_maestria_cuant.json
**Tama?o:** 15338
**SHA256:** 781a6bf5893e36e8d7f4b6396a78b19d7016077f2f48822f92766afb0dfc96c0
**Tipo:** json

```json
{
  "caratula": {
    "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
    "facultad": "ESCUELA DE POSGRADO",
    "escuela": "UNIDAD DE POSGRADO DE LA FACULTAD DE [FACULTAD]",
    "tipo_documento": "TESIS DE MAESTRÍA",
    "titulo_placeholder": "\"[TÍTULO COMPLETO DEL TRABAJO]\"",
    "frase_grado": "PARA OPTAR EL GRADO ACADÉMICO DE:",
    "grado_objetivo": "MAESTRO EN [NOMBRE EXACTO DEL PROGRAMA]",
    "label_autor": "AUTOR(ES)\n[NOMBRES Y APELLIDOS]",
    "label_asesor": "ASESOR\n[NOMBRES Y APELLIDOS]",
    "label_linea": "LÍNEA DE INVESTIGACIÓN: [NOMBRE DE LA LÍNEA]",
    "fecha": "Callao, [AÑO]",
    "pais": "PERÚ",
    "guia": "Contiene: variables, unidad de análisis, ámbito de estudio y temporalidad.\nMáx. 15 palabras; sin conectores ni nombres."
  },
  "preliminares": {
    "dedicatoria": {
      "titulo": "DEDICATORIA",
      "texto": "[Escriba aquí su dedicatoria…]"
    },
    "agradecimientos": {
      "titulo": "AGRADECIMIENTO",
      "texto": "[Escriba aquí su agradecimiento…]"
    },
    "abreviaturas": {
      "titulo": "ÍNDICE DE ABREVIATURAS",
      "nota": "Colocar el significado de las abreviaturas utilizadas en la investigación.",
      "ejemplo": "ORGANIZACIÓN MUNDIAL DE LA SALUD (OMS)"
    },
    "indices": {
      "contenido": "ÍNDICE DE CONTENIDO",
      "tablas": "ÍNDICE DE TABLAS",
      "figuras": "ÍNDICE DE FIGURAS",
      "abreviaturas": "ÍNDICE DE ABREVIATURAS",
      "placeholder": "(Generarlo)"
    },
    "hoja_jurado": {
      "titulo": "HOJA DE REFERENCIA DEL JURADO Y APROBACIÓN",
      "miembros": [
        {
          "name": "[Nombre]",
          "role": "PRESIDENTE"
        },
        {
          "name": "[Nombre]",
          "role": "SECRETARIO"
        },
        {
          "name": "[Nombre]",
          "role": "MIEMBRO"
        },
        {
          "name": "[Nombre]",
          "role": "MIEMBRO"
        }
      ],
      "asesor": "[ASESOR]",
      "acta": {
        "libro": "[N°]",
        "actas": "[N°]",
        "folio": "[N°]",
        "fecha": "[dd de mes de aaaa]",
        "resolucion": "[Código]"
      }
    },
    "introduccion": {
      "titulo": "INTRODUCCIÓN",
      "texto": "Manifiesta la importancia y las razones por que realiza la tesis de maestría. Referencie trabajos similares anteriormente publicados (nacionales e internacionales), mencione los objetivos de estudio, la problemática y las soluciones.\n\nAsimismo, presente una descripción de la estructura del documento (máximo 02 páginas)."
    }
  },
  "cuerpo": [
    {
      "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
      "contenido": [
        {
          "texto": "1.1 Descripción de la realidad problemática",
          "instruccion_detallada": "Describe, explica y evidencia la realidad problemática en el contexto internacional y/o nacional y, cuando corresponda, en el contexto institucional.\n\nSustente la identificación del problema relevante y evidencie el análisis de la problemática utilizando al menos una herramienta de ingeniería (por ejemplo: Pareto, Ishikawa, Árbol de problemas, Matriz de relevancia, Matriz de priorización, entre otras).\n\nSe debe mencionar la propuesta de solución del problema de investigación.",
          "imagenes": [
            {
              "titulo": "Figura 1.1. Herramienta de ingeniería (ejemplo)",
              "ruta": "placeholder",
              "fuente": "Ejemplo de figura. Reemplace por un gráfico/diagrama real (Pareto, Ishikawa, árbol de problemas, etc.) con fuente."
            }
          ]
        },
        {
          "texto": "1.2 Formulación del problema",
          "instruccion_detallada": "Formule el problema general y los problemas específicos. Redacte en forma interrogativa, clara y medible."
        },
        {
          "texto": "1.3 Objetivos",
          "instruccion_detallada": "Redacte un objetivo general y objetivos específicos, coherentes con el problema y medibles."
        },
        {
          "texto": "1.4 Justificación e importancia",
          "instruccion_detallada": "Sustente la relevancia teórica, práctica, social e institucional. Indique beneficiarios y aportes."
        },
        {
          "texto": "1.5 Limitaciones",
          "instruccion_detallada": "Indique limitaciones (tiempo, acceso a información, recursos) y cómo se mitigarán."
        }
      ]
    },
    {
      "titulo": "II. MARCO TEÓRICO",
      "contenido": [
        {
          "texto": "2.1 Antecedentes",
          "instruccion_detallada": "Los antecedentes de la presente investigación son el reflejo de una búsqueda exhaustiva en bases de datos científicas, repositorios universitarios y fuentes oficiales relacionadas al tema de estudio.\n\nPara cada antecedente, indique: autor(es), año, título, objetivo, metodología (tipo/enfoque/diseño), población/muestra, instrumentos, resultados y la conclusión principal que aporta a su investigación.\n\nOrganice en: antecedentes internacionales y nacionales."
        },
        {
          "texto": "2.1.1 Antecedentes internacionales",
          "instruccion_detallada": "Presente antecedentes internacionales con el formato: autor(año), título, objetivo, metodología, resultados y conclusión."
        },
        {
          "texto": "2.1.2 Antecedentes nacionales",
          "instruccion_detallada": "Presente antecedentes nacionales con el mismo formato. Relacione explícitamente el aporte al presente estudio."
        },
        {
          "texto": "2.2 Bases teóricas",
          "instruccion_detallada": "Desarrolle teorías, modelos y conceptos que sustentan las variables. Cite fuentes científicas.",
          "imagenes": [
            {
              "titulo": "Figura 2.1. Modelo conceptual / esquema (ejemplo)",
              "ruta": "placeholder",
              "fuente": "Ejemplo de figura para visualizar el formato. Reemplace por un esquema/modelo/diagrama propio con fuente."
            }
          ]
        },
        {
          "texto": "2.3 Marco conceptual",
          "instruccion_detallada": "Defina términos clave del estudio. Incluya definiciones operacionales si aplica."
        }
      ]
    },
    {
      "titulo": "III. HIPÓTESIS Y VARIABLES",
      "contenido": [
        {
          "texto": "3.1 Hipótesis",
          "instruccion_detallada": "Formule la hipótesis general y específicas (si aplica) en coherencia con los objetivos."
        },
        {
          "texto": "3.2 Variables",
          "instruccion_detallada": "Identifique claramente las variables (independiente y dependiente), dimensiones e indicadores.\n\nIncluya una matriz de consistencia (problema, objetivos, hipótesis, variables y metodología) y una matriz de operacionalización (variable, dimensión, indicador, escala, técnica/instrumento).\n\nUse definiciones conceptuales y operacionales; indique cómo se medirá cada indicador."
        }
      ]
    },
    {
      "titulo": "IV. METODOLOGÍA",
      "contenido": [
        {
          "texto": "4.1 Enfoque, tipo, diseño y nivel",
          "instruccion_detallada": "Defina el tipo de investigación (aplicada/básica), enfoque (cuantitativo), diseño (experimental/no experimental), nivel (descriptivo/correlacional/explicativo) y el método.\n\nDescriba la población, criterios de inclusión/exclusión, tamaño de muestra y técnica de muestreo.\n\nDetalle técnicas e instrumentos de recolección de datos (validez y confiabilidad), procedimientos y plan de análisis estadístico.",
          "tabla": {
            "headers": [
              "Variable",
              "Dimensión",
              "Indicador",
              "Instrumento"
            ],
            "rows": [
              [
                "Variable independiente",
                "Dimensión A",
                "Indicador A1",
                "Cuestionario"
              ],
              [
                "Variable dependiente",
                "Dimensión B",
                "Indicador B1",
                "Ficha de observación"
              ]
            ]
          },
          "tabla_titulo": "Tabla 4.1. Matriz de operacionalización (ejemplo)",
          "tabla_nota": "Ejemplo de tabla. Reemplace por su matriz de operacionalización completa."
        },
        {
          "texto": "4.2 Población y muestra",
          "instruccion_detallada": "Describa población, criterios, muestra y técnica de muestreo. Indique tamaño final."
        },
        {
          "texto": "4.3 Técnicas e instrumentos",
          "instruccion_detallada": "Detalle técnica(s) e instrumento(s). Incluya validez (juicio de expertos) y confiabilidad (Alfa de Cronbach u otro)."
        },
        {
          "texto": "4.4 Procedimientos y análisis de datos",
          "instruccion_detallada": "Explique el procedimiento paso a paso y el plan de análisis (estadística descriptiva e inferencial)."
        }
      ]
    },
    {
      "titulo": "V. RESULTADOS",
      "contenido": [
        {
          "texto": "5.1 Presentación de resultados",
          "instruccion_detallada": "Presente los resultados de manera ordenada según objetivos/hipótesis.\n\nIncluya tablas y figuras numeradas, con títulos claros y fuente cuando corresponda.\n\nEvite interpretación extensa en esta sección; la discusión va en el apartado correspondiente.",
          "tabla": {
            "headers": [
              "Indicador",
              "Antes",
              "Después",
              "Δ%"
            ],
            "rows": [
              [
                "Indicador 1",
                "10",
                "15",
                "50%"
              ],
              [
                "Indicador 2",
                "20",
                "24",
                "20%"
              ]
            ]
          },
          "tabla_titulo": "Tabla 5.1. Resultados por indicador (ejemplo)",
          "tabla_nota": "Ejemplo de tabla de resultados. Reemplace por sus resultados reales e incluya fuente si aplica."
        },
        {
          "texto": "5.2 Discusión",
          "instruccion_detallada": "Interprete y compare los resultados con la literatura (antecedentes y bases teóricas).\n\nExplique coincidencias y discrepancias, implicancias prácticas, y limitaciones del estudio."
        }
      ]
    },
    {
      "titulo": "VI. CONCLUSIONES Y RECOMENDACIONES",
      "contenido": [
        {
          "texto": "6.1 Conclusiones",
          "instruccion_detallada": "Redacte conclusiones directas y numeradas, alineadas a los objetivos e hipótesis.\n\nAñada recomendaciones aplicables y, si corresponde, propuestas de investigación futura."
        },
        {
          "texto": "6.2 Recomendaciones",
          "instruccion_detallada": "Presente recomendaciones aplicables para la institución/sector y sugerencias para futuras investigaciones."
        }
      ]
    }
  ],
  "finales": {
    "referencias": {
      "titulo": "REFERENCIAS BIBLIOGRÁFICAS",
      "nota": "Liste todas las fuentes citadas en el texto. Use un estilo de citación consistente (según norma indicada por su programa).\n\nVerifique: autor, año, título, editorial/revista, volumen(número), páginas, DOI/URL.\n\nIncluya solo referencias citadas en el texto. Orden alfabético. Use estilo APA (última edición indicada por la UNAC).",
      "ejemplos_apa": [
        "Ejemplos (formato referencial):",
        "Hernández, R., Fernández, C., & Baptista, P. (2018). Metodología de la investigación (6.a ed.). McGraw-Hill.",
        "Oblitas, M., & Villegas, M. (2023). Gestión de la calidad y desempeño organizacional. Revista Científica UNAC, 12(2), 45–60.",
        "Organización Mundial de la Salud. (2021). Título del documento. Sitio web institucional. https://ejemplo.org"
      ]
    },
    "anexos": {
      "titulo_seccion": "ANEXOS",
      "nota": "Incluya instrumentos, matrices (consistencia, operacionalización), evidencias, y documentos complementarios.\n\nNumere los anexos y refiéralos dentro del texto cuando corresponda.",
      "lista": [
        {
          "titulo": "ANEXO 1. Matriz de consistencia (ejemplo completo)",
          "nota": "Incluya la matriz de consistencia completa (problema, objetivos, hipótesis si aplica, variables, metodología).",
          "tabla": {
            "headers": [
              "Problema",
              "Objetivo",
              "Hipótesis",
              "Variables",
              "Metodología"
            ],
            "rows": [
              [
                "¿Problema general?",
                "Objetivo general",
                "Hipótesis general",
                "VI/VD",
                "Tipo/diseño/nivel"
              ],
              [
                "Problema específico 1",
                "Objetivo específico 1",
                "Hipótesis específica 1",
                "Indicadores",
                "Población/muestra"
              ]
            ]
          },
          "tabla_titulo": "Tabla A1. Matriz de consistencia (ejemplo)",
          "tabla_nota": "Ejemplo de anexo. Reemplace cada celda con su información real."
        },
        {
          "titulo": "ANEXO 2. Instrumento / evidencias (ejemplo completo)",
          "nota": "Adjunte el instrumento (cuestionario, guía de entrevista, ficha) y/o evidencias necesarias.",
          "parrafos": [
            "Instrumento (ejemplo):",
            "1) Pregunta 1: ________________________________",
            "2) Pregunta 2: ________________________________",
            "3) Pregunta 3: ________________________________",
            "",
            "Evidencia (ejemplo): actas, resoluciones, autorizaciones, fotografías u otros documentos pertinentes."
          ]
        }
      ]
    }
  },
  "version": "1.0.0",
  "descripcion": "Plantilla oficial de tesis de maestría (legacy).",
  "informacion_basica": {
    "titulo": "INFORMACIÓN BÁSICA",
    "elementos": [
      {
        "label": "FACULTAD:",
        "valor": "[FACULTAD]"
      },
      {
        "label": "UNIDAD DE INVESTIGACIÓN:",
        "valor": "[Unidad de Investigación]"
      },
      {
        "label": "TÍTULO:",
        "valor": "[TÍTULO DE TESIS]"
      },
      {
        "label": "AUTOR(ES) / CÓDIGO ORCID / DNI:",
        "valor": "[AUTOR]\nCódigo orcid:[0000-0000-0000-0000]\nDNI:[00000000]"
      },
      {
        "label": "ASESOR / COASESOR / CÓDIGO ORCID / DNI:",
        "valor": "[ASESOR]\nCódigo orcid:[0000-0000-0000-0000]\nDNI:[00000000]"
      },
      {
        "label": "LUGAR DE EJECUCIÓN:",
        "valor": "[Lugar de ejecución]"
      },
      {
        "label": "UNIDAD DE ANÁLISIS:",
        "valor": "[Unidad de análisis]"
      },
      {
        "label": "INVESTIGACIÓN:",
        "valor": "TIPO: [Tipo] / ENFOQUE: CUANTITATIVO / DISEÑO: [Diseño] / NIVEL: [Nivel]"
      },
      {
        "label": "TEMA OCDE:",
        "valor": "[Código y descripción OCDE]"
      }
    ]
  }
}
```

---

## app/data/unac/proyecto/unac_proyecto_cual.json
**Tama?o:** 23742
**SHA256:** dc4b543437bb1cbaa03696c58f7f20a335d13cbafee74790ab8035715e5fffdc
**Tipo:** json

```json
{
  "configuracion": {
    "fuente_normal": "Times New Roman",
    "tamano_normal": 12,
    "ruta_logo": "app/static/assets/LogoUNAC.png",
    "color_encabezado": "BDD7EE"
  },
  "caratula": {
    "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
    "facultad": "FACULTAD DE INGENIERÍA MECÁNICA Y DE ENERGÍA",
    "escuela": "UNIDAD DE POSGRADO",
    "tipo_documento": "PROYECTO DE INVESTIGACIÓN",
    "titulo_placeholder": "“TÍTULO DEL PROYECTO”",
    "frase_grado": "[Nota: Contiene: Las variables, unidad de análisis, ámbito de estudio. Máximo 15 palabras sin considerar artículos conectores.]",
    "grado_objetivo": "",
    "label_autor": "AUTOR(ES)\n\nNombres y Apellidos",
    "label_asesor": "ASESOR\nDr. Abel Tapia Díaz",
    "label_linea": "LÍNEA DE INVESTIGACIÓN:\nIngeniería y Tecnología",
    "fecha": "Callao, 2025",
    "pais": "PERÚ"
  },
  "pagina_respeto": {
    "titulo": "PÁGINA DE RESPETO",
    "notas": [
      {
        "texto": "Los datos no deben tener más de 4 años de antigüedad una vez terminada la experiencia.\n\nEn caso de tener la autorización de la empresa, se deberá presentar en una hoja membretada (o un formato oficial).\n\nAnexo 3",
        "formato": "recuadro"
      }
    ]
  },
  "informacion_basica": {
    "titulo": "INFORMACIÓN BÁSICA",
    "elementos": [
      {
        "label": "FACULTAD:",
        "valor": "Facultad de Ingeniería Mecánica y de Energía"
      },
      {
        "label": "UNIDAD DE INVESTIGACIÓN:",
        "valor": "Unidad de Posgrado..."
      },
      {
        "label": "TÍTULO:",
        "valor": "Implementación xxx"
      },
      {
        "label": "AUTOR(ES):",
        "valor": "Nombres y Apellidos / DNI: XXX / ORCID: YYYY"
      },
      {
        "label": "ASESOR:",
        "valor": "Dr. Abel Tapia Díaz / DNI: ... / ORCID: ..."
      },
      {
        "label": "LUGAR DE EJECUCIÓN:",
        "valor": ""
      },
      {
        "label": "ESCENARIO Y PARTICIPANTES:", "valor": "[Lugar y personas claves]"
      },
      {
        "label": "TIPO:",
        "valor": ""
      },
      {
        "label": "ENFOQUE:",
        "valor": ""
      },
      {
        "label": "DISEÑO DE INVESTIGACIÓN:",
        "valor": ""
      },
      {
        "label": "TEMA OCDE:",
        "valor": ""
      }
    ]
  },
  "preliminares": {
    "indices": [
      {
        "titulo": "ÍNDICE",
        "items": [
          {
            "texto": "ÍNDICE",
            "pag": 1
          },
          {
            "texto": "ÍNDICE DE TABLAS",
            "pag": 2
          },
          {
            "texto": "ÍNDICE DE FIGURAS",
            "pag": 3
          },
          {
            "texto": "ÍNDICE DE ABREVIATURAS",
            "pag": 4
          },
          {
            "texto": "INTRODUCCIÓN",
            "pag": 5
          },
          {
            "texto": "I. PLANTEAMIENTO DEL PROBLEMA",
            "pag": 6,
            "bold": true
          },
          {
            "texto": "II. MARCO TEÓRICO",
            "pag": 10,
            "bold": true
          },
          {
            "texto": "III. HIPÓTESIS Y VARIABLES",
            "pag": 17,
            "bold": true
          },
          {
            "texto": "IV. METODOLOGÍA DEL PROYECTO",
            "pag": 19,
            "bold": true
          },
          {
            "texto": "V. CRONOGRAMA DE ACTIVIDADES",
            "pag": 21,
            "bold": true
          },
          {
            "texto": "VI. PRESUPUESTO",
            "pag": 22,
            "bold": true
          },
          {
            "texto": "VII. REFERENCIAS BIBLIOGRÁFICAS",
            "pag": 23,
            "bold": true
          },
          {
            "texto": "VIII. ANEXOS",
            "pag": 24,
            "bold": true
          }
        ]
      },
      {
        "titulo": "ÍNDICE DE TABLAS",
        "items": [
          {
            "texto": "Tabla 1.1. Frecuencia de fallas en los equipos",
            "pag": 8
          },
          {
            "texto": "Tabla 1.2. Diagrama de Pareto",
            "pag": 8
          },
          {
            "texto": "Tabla 2.1. Mapa de Procesos",
            "pag": 12
          },
          {
            "texto": "Tabla 2.2. Diagrama de Procesos",
            "pag": 12
          }
        ]
      },
      {
        "titulo": "ÍNDICE DE FIGURAS",
        "items": [
          {
            "texto": "Figura 1.1 Frecuencia de los fallas en el área de mantenimiento",
            "pag": 7
          },
          {
            "texto": "Figura 1.2 Ejemplo",
            "pag": 7
          },
          {
            "texto": "Figura 2.1 Matriz de consistencia de variable simple",
            "pag": 13
          },
          {
            "texto": "Figura 2.2 Matriz de consistencia de implementación",
            "pag": 13
          },
          {
            "texto": "Figura 2.3 Matriz de operacionalización de diseño",
            "pag": 14
          },
          {
            "texto": "Figura 2.4 Matriz de operacionalización de diseño",
            "pag": 15
          }
        ]
      },
      {
        "titulo": "ÍNDICE DE ABREVIATURAS",
        "items": [
          {
            "texto": "ORGANIZACIÓN MUNDIAL DE LA SALUD (OMS)",
            "pag": 6
          }
        ],
        "nota": "Colocar el significado de las abreviaturas utilizadas en la investigación sin la paginación"
      }
    ],
    "introduccion": {
      "titulo": "INTRODUCCIÓN",
      "texto": "Manifiesta la importancia y las razones por las que realiza el proyecto de tesis, referencia algunos trabajos similares anteriormente publicados, menciona los objetivos de estudio, la problemática y las soluciones. Asimismo presentar una descripción de la estructura del proyecto (máximo 02 páginas)."
    }
  },
  "cuerpo": [
    {
      "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
      "nota_capitulo": "Nota: Los datos no deben tener más de 4 años de antigüedad una vez terminada la experiencia.",
      "contenido": [
        {
          "texto": "1.1 Descripción de la realidad problemática",
          "nota": "Describe, explica y evidencia la realidad problemática en el contexto internacional y/o nacional y de la empresa.",
          "instruccion_detallada": "Describe, explica y evidencia la realidad problemática en el contexto internacional y/o nacional y de la empresa, de las líneas de investigación prioritarias o transversales utilizando fuentes científicas y/o oficiales. Sustenta la identificación del problema relevante y evidencia el análisis de la problemática utilizando al menos una herramienta de ingeniería (Pareto, Ishikawa, árbol de problemas, matriz de relevancia, matriz de priorización, entre otras). Se debe mencionar la propuesta de solución del problema de investigación."
        },
        {
          "texto": "1.2 Formulación del problema",
          "nota": "Problema general y específicos expresados en forma interrogativa.",
          "instruccion_detallada": "Problema general: Se expresa en forma interrogativa, incluye las variables, unidad de análisis, lugar de la investigación y está redactado en tiempo presente.\nProblemas específicos: Están expresados en forma interrogativa, se derivan del problema general, su enunciado es claro y conciso."
        },
        {
          "texto": "1.3 Objetivos",
          "nota": "Objetivo general y específicos (verbo en infinitivo).",
          "instruccion_detallada": "Objetivo general: Es coherente con el problema, incluye las variables, inicia con verbo en infinitivo (Ejemplo: Establecer, determinar, incrementar, etc.), enuncia la acción para la propuesta de solución. Guarda relación con el problema general. (Sugerencia revisar la taxonomía de Bloom).\nObjetivos específicos: Orientan todas las acciones parciales para lograr el objetivo general. Se inician con verbos en infinitivo y guarda relación con los problemas específicos."
        },
        {
          "texto": "1.4 Justificación",
          "nota": "Sustenta el por qué se realiza el trabajo (teórica, práctica, metodológica).",
          "instruccion_detallada": "Sustenta adecuadamente el por qué se realiza el trabajo de investigación de acuerdo con la naturaleza del problema explicando cuáles son las contribuciones científicas o sociales y los beneficiarios de su trabajo. Definir los tipos de justificación (teórica, práctica, metodológica, etc) citando adecuadamente y el sustento respectivo explicando las razones por las cuales la investigación posee dicha justificación. Se redacta en tiempo futuro."
        },
        {
          "texto": "1.5 Delimitantes de la investigación",
          "nota": "Delimitante Teórica, Temporal y Espacial.",
          "instruccion_detallada": "Delimitante Teórica: Especifica las teorías que soportan su investigación.\nDelimitante Temporal: Especifica en qué momento (tiempo) se realiza la investigación.\nDelimitante Espacial: Especifica en qué lugar se realiza la investigación."
        }
      ]
    },
   {
      "titulo": "II. REVISIÓN DE LITERATURA",
      "contenido": [
        {
          "texto": "2.1 Antecedentes",
          "nota": "Nacionales e Internacionales (priorizar estudios cualitativos).",
          "instruccion_detallada": "Presenta el estado del arte revisando investigaciones previas. Se recomienda buscar tesis o artículos con enfoque CUALITATIVO o MIXTO que aborden el mismo fenómeno de estudio.\n\nEn cada antecedente, resalta:\n- El objetivo de comprensión (no de medición).\n- La metodología cualitativa usada (fenomenología, etnografía, etc.).\n- Los hallazgos descriptivos o interpretativos más relevantes (categorías emergentes)."
        },
        {
          "texto": "2.2 Bases teóricas",
          "nota": "Teorías sustantivas que fundamentan el fenómeno.",
          "instruccion_detallada": "Desarrolla las teorías o enfoques que permiten interpretar el fenómeno estudiado.\n\nDiferencia clave: No se busca una teoría para 'medir variables', sino marcos interpretativos (ej. Teoría de la Motivación, Interaccionismo Simbólico, Gestión por Procesos) que ayuden a entender las **Categorías de estudio** y sus relaciones."
        },
        {
          "texto": "2.3 Marco conceptual",
          "nota": "Definición de las Categorías Apriorísticas.",
          "instruccion_detallada": "Define conceptualmente las **CATEGORÍAS** y **SUBCATEGORÍAS** que guiarán la investigación inicial.\n\nInstrucción: A diferencia de las variables (que se operacionalizan en números), aquí debes definir el concepto abstracto de la categoría tal como se entiende en tu contexto (ej. 'Percepción de seguridad', 'Cultura organizacional', 'Vivencia del duelo')."
        },
        {
          "texto": "2.4 Definición de términos básicos",
          "nota": "Glosario funcional.",
          "instruccion_detallada": "Define términos técnicos o propios del contexto (jerga de la empresa, términos técnicos específicos) para evitar ambigüedades en la lectura de las entrevistas o resultados."
        }
      ]
    },
    {
      "titulo": "III. METODOLOGÍA DEL PROYECTO",
      "nota_capitulo": "En este capítulo se detalla el abordaje cualitativo para comprender el fenómeno.",
      "contenido": [
        {
          "texto": "3.1 Enfoque y Diseño de Investigación",
          "instruccion_detallada": "Define el enfoque (Cualitativo) y el diseño específico (Fenomenológico, Etnográfico, Teoría Fundamentada, Estudio de Caso, etc.). Justifica por qué este diseño es el más adecuado para responder a tu problema."
        },
        {
          "texto": "3.2 Escenario de Estudio y Participantes",
          "instruccion_detallada": "Describe el contexto (lugar, área, empresa) y quiénes son los informantes clave (Participantes). No se usa fórmula de muestra, sino criterios de inclusión (ej. 'trabajadores con más de 5 años de experiencia')."
        },
        {
          "texto": "3.3 Matriz de Categorización",
          "instruccion_detallada": "Tabla que organiza las Categorías Apriorísticas (conceptos clave a investigar) y sus Subcategorías. Reemplaza a la operacionalización de variables.",
          "tablas_especiales": [
            {
              "titulo": "Tabla 3.1 Matriz de Categorización Apriorística",
              "headers": [
                "CATEGORÍA",
                "DEFINICIÓN CONCEPTUAL",
                "SUBCATEGORÍAS",
                "PREGUNTAS ORIENTADORAS (Instrumento)"
              ],
              "rows": [
                [
                  "GESTIÓN DEL CAMBIO (Ejemplo)",
                  "Proceso mediante el cual la organización transita de un estado actual a uno deseado (Autor, Año).",
                  "- Resistencia al cambio\n- Adaptación tecnológica\n- Comunicación interna",
                  "¿Cómo percibió el equipo la llegada de la nueva maquinaria?\n¿Qué canales de comunicación fueron más efectivos?"
                ]
              ]
            }
          ]
        },
        {
          "texto": "3.4 Técnicas e instrumentos de recolección de datos",
          "instruccion_detallada": "Técnicas: Entrevista semiestructurada, Observación participante, Focus Group, Análisis documental.\nInstrumentos: Guía de entrevista (preguntas abiertas), Guía de observación, Ficha de bitácora."
        },
        {
          "texto": "3.5 Procedimiento de recolección y análisis",
          "instruccion_detallada": "Describe los pasos: 1. Inmersión en el campo. 2. Aplicación de entrevistas. 3. Transcripción. 4. Codificación (abierta, axial). 5. Triangulación de datos."
        },
        {
          "texto": "3.6 Rigor Científico",
          "instruccion_detallada": "Criterios de calidad que reemplazan a la validez y confiabilidad estadística:\n- Credibilidad (Validez interna)\n- Transferibilidad (Validez externa)\n- Dependencia (Consistencia)\n- Confirmabilidad (Objetividad)"
        },
        {
          "texto": "3.7 Aspectos Éticos",
          "instruccion_detallada": "Consentimiento informado, confidencialidad de los participantes (uso de códigos en lugar de nombres) y honestidad en el manejo de la información."
        }
      ]
    },
    {
      "titulo": "IV. METODOLOGÍA DEL PROYECTO",
      "contenido": [
        {
          "texto": "4.1 Diseño metodológico",
          "nota": "Tipo, Enfoque, Nivel y Diseño de investigación.",
          "instruccion_detallada": "En esta sección se debe indicar: Tipo de investigación (Básica o Aplicada), Enfoque de Investigación (Cuantitativa o Cualitativa), Nivel de Investigación (Descriptiva, Correlacional, explicativo u otros), Diseño de Investigación (No experimental, Experimental, y su esquema correspondiente) especificando el tipo. Debe definir cada clasificación de su investigación citando y argumentar su elección."
        },
        {
          "texto": "4.2 Método de investigación",
          "nota": "Método científico y etapas de desarrollo.",
          "instruccion_detallada": "Método de investigación científica. Definir el método citando un autor y argumentar su elección especificando las etapas ¿Cómo se va a desarrollar? estableciendo los procedimientos del desarrollo de la investigación."
        },
        {
          "texto": "4.3 Población y muestra",
          "nota": "Descripción de población y tipo de muestreo.",
          "instruccion_detallada": "Describe la población y argumenta la elección de la muestra, si la naturaleza de la investigación lo requiere (indicando el tipo de muestreo). En caso de que no aplique argumentar adecuadamente (Tesis de Diseño)."
        },
        {
          "texto": "4.4 Lugar de estudio",
          "nota": "Ubicación y descripción del área.",
          "instruccion_detallada": "Muestra la ubicación de la empresa y describe el área o lugar específico donde se realiza la investigación. Se recomienda: Usar Google maps indicando la ubicación. Usar una herramienta que permita visualizar el área donde se realiza la investigación. Contexto de la empresa."
        },
        {
          "texto": "4.5 Técnicas e instrumentos para la recolección de la información",
          "instruccion_detallada": "Define (citando) y sustente el uso de las técnicas e instrumentos utilizados en la investigación, especificando que información van a obtener. Las fichas de recolección de datos no requieren validación."
        },
        {
          "texto": "4.6 Análisis y procesamiento de datos",
          "instruccion_detallada": "Explica ¿Cómo se utiliza la información? Seguir las etapas del procedimiento especificando las herramientas utilizadas y como se analizan los datos."
        },
        {
          "texto": "4.7 Aspectos éticos en Investigación",
          "instruccion_detallada": "Considerar los principios del código de ética de la UNAC y especificar ¿Cómo se aplican los principios mencionados?"
        }
      ]
    },
    {
      "titulo": "V. CRONOGRAMA DE ACTIVIDADES",
      "contenido": [
        {
          "texto": "Cronograma de ejecución",
          "nota": "Secuencia del desarrollo de la investigación.",
          "instruccion_detallada": "Evidencia la secuencia del desarrollo de la investigación hasta la elaboración del informe final. La frecuencia (meses / semanas / días) va a depender de la investigación. No requiere enumerar como tabla. No requiere indicar elaboración propia."
        }
      ]
    },
    {
      "titulo": "VI. PRESUPUESTO",
      "contenido": [
        {
          "texto": "Recursos y Presupuesto",
          "nota": "Inversión, recursos humanos, materiales y financieros.",
          "instruccion_detallada": "Se debe presentar lo que el investigador ha invertido bajo su responsabilidad, en la investigación. Se considera los recursos humanos, materiales y financieros necesarios para el desarrollo de la investigación (en soles) e indicar la fuente de financiamiento."
        }
      ]
    }
  ],
   "finales": {
    "referencias": {
      "titulo": "VII. REFERENCIAS BIBLIOGRÁFICAS",
      "nota": "Las referencias deben seguir el estilo APA (7ma edición). Deben contener únicamente las fuentes citadas en el cuerpo del proyecto y ordenarse alfabéticamente.",
      "ejemplos": [
        "Chiavenato, I. (2011). Administración de recursos humanos (5.ª ed.). McGraw-Hill.",
        "Hernández Sampieri, R., Fernández Collado, C., & Baptista Lucio, P. (2014). Metodología de la investigación (6.ª ed.). McGraw-Hill.",
        "Pérez, J. (2023). Implementación de un sistema de mantenimiento preventivo [Tesis de pregrado, Universidad Nacional del Callao]. Repositorio Institucional UNAC.",
        "Rodríguez, L. (2022). Análisis de fallas en sistemas de bombeo. Revista Ingeniería Mecánica, 15(2), 45-52. https://doi.org/10.1016/j.eng.2022.01.001"
      ]
    },
    "anexos": {
      "titulo_seccion": "VIII. ANEXOS",
      "lista": [
        {
          "titulo": "Anexo 1: Matriz de consistencia",
          "nota": "Está conformada por una matriz (cuadro) formado por columnas y filas que permite evaluar la coherencia y conexión lógica que existe entre el título de la investigación, la formulación del problema, el (los) objetivo(s), la (s) hipótesis, las variables, y la metodología. (Resolución 017-18-CU)."
        },
        {
          "titulo": "Anexo 2: Herramienta de ingeniería para el análisis de la problemática",
          "nota": "Se debe incluir la aplicación de al menos una herramienta de ingeniería utilizada para evidenciar el problema central (Ejemplo: Diagrama de Pareto, Diagrama de Ishikawa, Árbol de problemas, Matriz de relevancia, entre otras)."
        },
        {
          "titulo": "Anexo 3: Autorización del uso de datos",
          "nota": "Utilice este formato para imprimirlo en papel membretado con las firmas correspondientes:\n\nYo .................................................................................., identificado con DNI .................................., en mi calidad de ........................................................... del área ......................................... de la empresa/institución ................................................................................................. con R.U.C N° ................................................., ubicada en la ciudad de ............................................\n\nOTORGO LA AUTORIZACIÓN..."
        },
        {
          "titulo": "Anexo 4: Ficha de recolección de datos",
          "nota": "Adjuntar los formatos de las fichas, cuestionarios o guías de observación utilizados para la captura de datos en campo. Nota: Las fichas de recolección de datos no requieren validación por juicio de expertos según normativa vigente."
        }
      ]
    }
  },
  "matriz_consistencia": {
    "problemas": {
      "general": "¿De qué manera la implementación de un plan de mantenimiento reduce el tiempo perdido en el área de trapiche de la empresa Pomalca - 2023?",
      "especificos": [
        "Realizar un diagnóstico inicial midiendo el tiempo perdido en el área de trapiche",
        "Realizar un análisis de criticidad de los equipos del área de trapiche.",
        "Desarrollar un análisis de modos y efectos de fallas de los equipos críticos.",
        "Programar las actividades del plan de mantenimiento de los equipos.",
        "Implementar el plan de mantenimiento preventivo elaborado.",
        "Medir el tiempo perdido después de la implementación del plan."
      ]
    },
    "objetivos": {
      "general": "Determinar cómo la implementación de un plan de mantenimiento reduce el tiempo perdido en el área de trapiche de la empresa Pomalca",
      "especificos": [
        "Realizar un diagnóstico inicial midiendo el tiempo perdido en el área de trapiche",
        "Realizar un análisis de criticidad de los equipos del área de trapiche.",
        "Desarrollar un análisis de modos y efectos de fallas de los equipos críticos.",
        "Programar las actividades del plan de mantenimiento de los equipos.",
        "Implementar el plan de mantenimiento preventivo elaborado.",
        "Medir el tiempo perdido después de la implementación del plan."
      ]
    },
    "hipotesis": {
      "general": "La implementación de un plan de mantenimiento reduce el tiempo perdido en el área de trapiche de la empresa Pomalca",
      "especificos": []
    },
    "variables": {
  "independiente": {
    "nombre": "CATEGORÍA PRINCIPAL",
    "dimensiones": ["Subcategoría 1", "Subcategoría 2"]
  },
  "dependiente": {
    "nombre": "CATEGORÍA SECUNDARIA (Si aplica)",
    "dimensiones": []
  }
    },
    "metodologia": {
      "tipo": "Aplicada",
      "enfoque": "Cualitativo",
      "nivel": "Explicativo",
      "diseno": "Pre Experimental",
      "poblacion": "32 equipos del área de Trapiche",
      "muestra": "24 equipos críticos",
      "tecnicas": "Análisis documental, Observación",
      "instrumentos": "Ficha de recolección de datos",
      "procesamiento": "SPSS v25"
    }
  }
}

```

---

## app/data/unac/proyecto/unac_proyecto_cuant.json
**Tama?o:** 25985
**SHA256:** 56d36ac05138d4adc45934cfffaf89c7ddaa5d8753a34297df987429b69e7ad7
**Tipo:** json

```json
{
  "configuracion": {
    "fuente_normal": "Times New Roman",
    "tamano_normal": 12,
    "ruta_logo": "app/static/assets/LogoUNAC.png",
    "color_encabezado": "BDD7EE"
  },
  "caratula": {
    "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
    "facultad": "FACULTAD DE INGENIERÍA MECÁNICA Y DE ENERGÍA",
    "escuela": "UNIDAD DE POSGRADO",
    "tipo_documento": "PROYECTO DE INVESTIGACIÓN",
    "titulo_placeholder": "“TÍTULO DEL PROYECTO”",
    "frase_grado": "[Nota: Contiene: Las variables, unidad de análisis, ámbito de estudio. Máximo 15 palabras sin considerar artículos conectores.]",
    "grado_objetivo": "",
    "label_autor": "AUTOR(ES)\n\nNombres y Apellidos",
    "label_asesor": "ASESOR\nDr. Abel Tapia Díaz",
    "label_linea": "LÍNEA DE INVESTIGACIÓN:\nIngeniería y Tecnología",
    "fecha": "Callao, 2025",
    "pais": "PERÚ"
  },
  "pagina_respeto": {
    "titulo": "PÁGINA DE RESPETO",
    "notas": [
      {
        "texto": "Los datos no deben tener más de 4 años de antigüedad una vez terminada la experiencia.\n\nEn caso de tener la autorización de la empresa, se deberá presentar en una hoja membretada (o un formato oficial).\n\nAnexo 3",
        "formato": "recuadro"
      }
    ]
  },
  "informacion_basica": {
    "titulo": "INFORMACIÓN BÁSICA",
    "elementos": [
      {
        "label": "FACULTAD:",
        "valor": "Facultad de Ingeniería Mecánica y de Energía"
      },
      {
        "label": "UNIDAD DE INVESTIGACIÓN:",
        "valor": "Unidad de Posgrado..."
      },
      {
        "label": "TÍTULO:",
        "valor": "Implementación xxx"
      },
      {
        "label": "AUTOR(ES):",
        "valor": "Nombres y Apellidos / DNI: XXX / ORCID: YYYY"
      },
      {
        "label": "ASESOR:",
        "valor": "Dr. Abel Tapia Díaz / DNI: ... / ORCID: ..."
      },
      {
        "label": "LUGAR DE EJECUCIÓN:",
        "valor": ""
      },
      {
        "label": "UNIDAD DE ANÁLISIS:",
        "valor": ""
      },
      {
        "label": "TIPO:",
        "valor": ""
      },
      {
        "label": "ENFOQUE:",
        "valor": ""
      },
      {
        "label": "DISEÑO DE INVESTIGACIÓN:",
        "valor": ""
      },
      {
        "label": "TEMA OCDE:",
        "valor": ""
      }
    ]
  },
  "preliminares": {
    "indices": [
      {
        "titulo": "ÍNDICE",
        "items": [
          {
            "texto": "ÍNDICE",
            "pag": 1
          },
          {
            "texto": "ÍNDICE DE TABLAS",
            "pag": 2
          },
          {
            "texto": "ÍNDICE DE FIGURAS",
            "pag": 3
          },
          {
            "texto": "ÍNDICE DE ABREVIATURAS",
            "pag": 4
          },
          {
            "texto": "INTRODUCCIÓN",
            "pag": 5
          },
          {
            "texto": "I. PLANTEAMIENTO DEL PROBLEMA",
            "pag": 6,
            "bold": true
          },
          {
            "texto": "II. MARCO TEÓRICO",
            "pag": 10,
            "bold": true
          },
          {
            "texto": "III. HIPÓTESIS Y VARIABLES",
            "pag": 17,
            "bold": true
          },
          {
            "texto": "IV. METODOLOGÍA DEL PROYECTO",
            "pag": 19,
            "bold": true
          },
          {
            "texto": "V. CRONOGRAMA DE ACTIVIDADES",
            "pag": 21,
            "bold": true
          },
          {
            "texto": "VI. PRESUPUESTO",
            "pag": 22,
            "bold": true
          },
          {
            "texto": "VII. REFERENCIAS BIBLIOGRÁFICAS",
            "pag": 23,
            "bold": true
          },
          {
            "texto": "VIII. ANEXOS",
            "pag": 24,
            "bold": true
          }
        ]
      },
      {
        "titulo": "ÍNDICE DE TABLAS",
        "items": [
          {
            "texto": "Tabla 1.1. Frecuencia de fallas en los equipos",
            "pag": 8
          },
          {
            "texto": "Tabla 1.2. Diagrama de Pareto",
            "pag": 8
          },
          {
            "texto": "Tabla 2.1. Mapa de Procesos",
            "pag": 12
          },
          {
            "texto": "Tabla 2.2. Diagrama de Procesos",
            "pag": 12
          }
        ]
      },
      {
        "titulo": "ÍNDICE DE FIGURAS",
        "items": [
          {
            "texto": "Figura 1.1 Frecuencia de los fallas en el área de mantenimiento",
            "pag": 7
          },
          {
            "texto": "Figura 1.2 Ejemplo",
            "pag": 7
          },
          {
            "texto": "Figura 2.1 Matriz de consistencia de variable simple",
            "pag": 13
          },
          {
            "texto": "Figura 2.2 Matriz de consistencia de implementación",
            "pag": 13
          },
          {
            "texto": "Figura 2.3 Matriz de operacionalización de diseño",
            "pag": 14
          },
          {
            "texto": "Figura 2.4 Matriz de operacionalización de diseño",
            "pag": 15
          }
        ]
      },
      {
        "titulo": "ÍNDICE DE ABREVIATURAS",
        "items": [
          {
            "texto": "ORGANIZACIÓN MUNDIAL DE LA SALUD (OMS)",
            "pag": 6
          }
        ],
        "nota": "Colocar el significado de las abreviaturas utilizadas en la investigación sin la paginación"
      }
    ],
    "introduccion": {
      "titulo": "INTRODUCCIÓN",
      "texto": "Manifiesta la importancia y las razones por las que realiza el proyecto de tesis, referencia algunos trabajos similares anteriormente publicados, menciona los objetivos de estudio, la problemática y las soluciones. Asimismo presentar una descripción de la estructura del proyecto (máximo 02 páginas)."
    }
  },
  "cuerpo": [
    {
      "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
      "nota_capitulo": "Nota: Los datos no deben tener más de 4 años de antigüedad una vez terminada la experiencia.",
      "contenido": [
        {
          "texto": "1.1 Descripción de la realidad problemática",
          "nota": "Describe, explica y evidencia la realidad problemática en el contexto internacional y/o nacional y de la empresa.",
          "instruccion_detallada": "Describe, explica y evidencia la realidad problemática en el contexto internacional y/o nacional y de la empresa, de las líneas de investigación prioritarias o transversales utilizando fuentes científicas y/o oficiales. Sustenta la identificación del problema relevante y evidencia el análisis de la problemática utilizando al menos una herramienta de ingeniería (Pareto, Ishikawa, árbol de problemas, matriz de relevancia, matriz de priorización, entre otras). Se debe mencionar la propuesta de solución del problema de investigación."
        },
        {
          "texto": "1.2 Formulación del problema",
          "nota": "Problema general y específicos expresados en forma interrogativa.",
          "instruccion_detallada": "Problema general: Se expresa en forma interrogativa, incluye las variables, unidad de análisis, lugar de la investigación y está redactado en tiempo presente.\nProblemas específicos: Están expresados en forma interrogativa, se derivan del problema general, su enunciado es claro y conciso."
        },
        {
          "texto": "1.3 Objetivos",
          "nota": "Objetivo general y específicos (verbo en infinitivo).",
          "instruccion_detallada": "Objetivo general: Es coherente con el problema, incluye las variables, inicia con verbo en infinitivo (Ejemplo: Establecer, determinar, incrementar, etc.), enuncia la acción para la propuesta de solución. Guarda relación con el problema general. (Sugerencia revisar la taxonomía de Bloom).\nObjetivos específicos: Orientan todas las acciones parciales para lograr el objetivo general. Se inician con verbos en infinitivo y guarda relación con los problemas específicos."
        },
        {
          "texto": "1.4 Justificación",
          "nota": "Sustenta el por qué se realiza el trabajo (teórica, práctica, metodológica).",
          "instruccion_detallada": "Sustenta adecuadamente el por qué se realiza el trabajo de investigación de acuerdo con la naturaleza del problema explicando cuáles son las contribuciones científicas o sociales y los beneficiarios de su trabajo. Definir los tipos de justificación (teórica, práctica, metodológica, etc) citando adecuadamente y el sustento respectivo explicando las razones por las cuales la investigación posee dicha justificación. Se redacta en tiempo futuro."
        },
        {
          "texto": "1.5 Delimitantes de la investigación",
          "nota": "Delimitante Teórica, Temporal y Espacial.",
          "instruccion_detallada": "Delimitante Teórica: Especifica las teorías que soportan su investigación.\nDelimitante Temporal: Especifica en qué momento (tiempo) se realiza la investigación.\nDelimitante Espacial: Especifica en qué lugar se realiza la investigación."
        }
      ]
    },
    {
      "titulo": "II. MARCO TEÓRICO",
      "contenido": [
        {
          "texto": "2.1 Antecedentes",
          "nota": "Búsqueda exhaustiva en bases de datos (mínimo 5 antecedentes).",
          "instruccion_detallada": "Los antecedentes de la presente investigación son el reflejo de una búsqueda exhaustiva en diferentes bases de datos de las universidades y de artículos científicos relacionados al tema de estudio.\n2.1.1 Antecedentes Internacionales.\n2.1.2 Antecedentes Nacionales.\n(Se debe considerar mínimo 5 antecedentes, puede incluir artículos científicos nacionales)."
        },
        {
          "texto": "2.2 Bases teóricas",
          "nota": "Principios, leyes, enfoques y teorías relacionadas con las variables.",
          "instruccion_detallada": "Describen y explican principios, leyes, enfoques, teorías relacionadas con sus variables de investigación.\n• Todas las bases teóricas tienen las citas textuales o parafraseados correspondientes.\n• Las bases teóricas tienen relación con las variables de investigación.\nTambién se puede considerar marco legal, ambiental u otro que requiera la investigación.",
          "mostrar_matriz": true,
          "tablas_especiales": [
  {
    "titulo": "Figura 2.2 Matriz de consistencia de implementación",
    "headers": ["PROBLEMA GENERAL", "OBJETIVO GENERAL", "HIPÓTESIS GENERAL", "VARIABLES", "METODOLOGÍA"],
    "rows": [
      [
        "¿De qué manera la implementación de un plan de mantenimiento preventivo mejora la disponibilidad del sistema de bombeo?",
        "Determinar cómo la implementación de un plan de mantenimiento preventivo mejora la disponibilidad del sistema de bombeo.",
        "La implementación de un plan de mantenimiento preventivo mejora la disponibilidad del sistema de bombeo.",
        "VARIABLE INDEPENDIENTE:\nPLAN DE MANTENIMIENTO PREVENTIVO",
        "TIPO: Aplicada\nENFOQUE: Cuantitativo\nNIVEL: Explicativo"
      ],
      [
        "PROBLEMAS ESPECÍFICOS:\n¿De qué manera mejora la confiabilidad?",
        "OBJETIVOS ESPECÍFICOS:\nDeterminar cómo mejora la confiabilidad.",
        "HIPÓTESIS ESPECÍFICAS:\nLa implementación mejora la confiabilidad.",
        "DIMENSIONES VI:\n- Diagnóstico inicial\n- AMEF\n- Programación de actividades",
        "DISEÑO: Pre Experimental\nPOBLACIÓN: Sistema de bombeo\nMUESTRA: 2 estaciones"
      ],
      [
        "¿De qué manera mejora la mantenibilidad?",
        "Determinar cómo mejora la mantenibilidad.",
        "La implementación mejora la mantenibilidad.",
        "VARIABLE DEPENDIENTE:\nDISPONIBILIDAD\n\nDIMENSIONES VD:\n- Confiabilidad\n- Mantenibilidad",
        "TÉCNICAS: Análisis documental, Observación\nINSTRUMENTOS: Ficha de datos\nPROCESAMIENTO: SPSS v25"
      ]
    ]
  },
  {
    "titulo": "Figura 2.3 Matriz de operacionalización de diseño",
    "headers": ["VARIABLES", "DIMENSIONES", "INDICADORES", "ÍNDICE", "MÉTODO Y TÉCNICA"],
    "rows": [
      [
        "VARIABLE I:\nDiseño de un sistema de ventilación mecánica con jetfan",
        "Parámetros básicos de diseño",
        "Volumen\nCaudal",
        "Área x altura\nVolumen de aire/minuto",
        "MÉTODO:\nCuantitativo"
      ],
      [
        "",
        "Redes de distribución de aire",
        "Pérdidas\nRuta crítica",
        "Pulg. columna agua/100 pies\nMáxima pérdida de presión",
        "MÉTODO:\nCualitativo"
      ],
      [
        "",
        "Selección de equipos",
        "Caída de presión\nCaudal de operación\nEficiencia",
        "Pérdida real\nVolumen real\nPotencia mecánica/eléctrica",
        "TÉCNICA:\nDocumental"
      ],
      [
        "",
        "Validación de diseño",
        "Preproceso\nResolución\nPostproceso",
        "Diseño, mallado\nEcuaciones diferenciales\nGráficos",
        "TÉCNICA:\nEmpírica"
      ]
    ]
  }
]
        },
        {
          "texto": "2.3 Marco conceptual",
          "instruccion_detallada": "Elabora nuevos constructos fundamentados de las teorías en relación al problema de investigación. Recopila, sistematiza y construye conceptos para el desarrollo de la investigación.\n2.3.1 Variable 1 (Dimensiones, Indicadores).\n2.3.2 Variable 2 (en caso fuese necesario)."
        },
        {
          "texto": "2.4 Definición de términos básicos",
          "instruccion_detallada": "Se recomienda declarar los términos que permitan facilitar el entendimiento de la investigación al lector, como términos propios de la industria o de la investigación."
        }
      ]
    },
    {
      "titulo": "III. HIPÓTESIS Y VARIABLES",
      "contenido": [
        {
          "texto": "3.1 Hipótesis",
          "nota": "Afirmación que debe ser probada (General y Específicas).",
          "instruccion_detallada": "En caso de no aplicar a la investigación sustentar el motivo. Las investigaciones descriptivas simples no requieren hipótesis.\nHipótesis General: Plantearse como afirmación, las cuales deben ser probada por medio de técnicas de investigación usando datos empíricos y ser acordes a los objetivos planteados.\nHipótesis Específicas: Expresa respuestas coherentes de cómo dar solución a cada uno de los problemas específicos y está formulado en forma afirmativa de proposición."
        },
        {
          "texto": "3.2 Operacionalización de variable",
          "nota": "Matriz de operacionalización (sin rotulado de tabla).",
          "instruccion_detallada": "Se puede colocar un texto previo a la matriz de operacionalización de variables (opcional). No lleva rotulado de tabla ni fuente. Constituye el conjunto de procedimientos para medir una variable.",
          "tabla": {
            "headers": [
              "VARIABLES",
              "DEFINICIÓN CONCEPTUAL",
              "DEFINICIÓN OPERACIONAL",
              "DIMENSIONES",
              "INDICADORES",
              "ÍNDICE",
              "MÉTODO Y TÉCNICA"
            ],
            "rows": [
              [
                "",
                "Definición según un autor de un libro, ley, norma o artículo científico (Citar)",
                "Constituye el conjunto de procedimientos, actividades u operaciones que deben realizarse para medir una variable.",
                "Pueden denominarse como sub variables. En conjunto detallan el comportamiento de la variable en estudio; se recomienda que las dimensiones provengan de teorías, las cuales deben estar detalladas en el marco teórico.",
                "Elemento observable, que permiten estudiar o cuantificar las dimensiones. Información transformable en valores numéricos que nos permitirán realizar operaciones de cálculo, estadísticas, que nos permiten nuevas operaciones para describir la realidad estudiada, comprenderla, explicar e, incluso, predecir acontecimientos en términos probabilísticos.",
                "Permiten medir características de las variables de manera general según dimensiones. Debe tener coherencia con el marco teórico y con lo que propuesto en los instrumentos de recolección de datos.\nLos índices expresan la intensidad de la cualidad de los indicadores.",
                "Menciona el método y la técnica que empleará para cuantificar u observar las variables."
              ]
            ]
          }
        }
      ]
    },
    {
      "titulo": "IV. METODOLOGÍA DEL PROYECTO",
      "contenido": [
        {
          "texto": "4.1 Diseño metodológico",
          "nota": "Tipo, Enfoque, Nivel y Diseño de investigación.",
          "instruccion_detallada": "En esta sección se debe indicar: Tipo de investigación (Básica o Aplicada), Enfoque de Investigación (Cuantitativa o Cualitativa), Nivel de Investigación (Descriptiva, Correlacional, explicativo u otros), Diseño de Investigación (No experimental, Experimental, y su esquema correspondiente) especificando el tipo. Debe definir cada clasificación de su investigación citando y argumentar su elección."
        },
        {
          "texto": "4.2 Método de investigación",
          "nota": "Método científico y etapas de desarrollo.",
          "instruccion_detallada": "Método de investigación científica. Definir el método citando un autor y argumentar su elección especificando las etapas ¿Cómo se va a desarrollar? estableciendo los procedimientos del desarrollo de la investigación."
        },
        {
          "texto": "4.3 Población y muestra",
          "nota": "Descripción de población y tipo de muestreo.",
          "instruccion_detallada": "Describe la población y argumenta la elección de la muestra, si la naturaleza de la investigación lo requiere (indicando el tipo de muestreo). En caso de que no aplique argumentar adecuadamente (Tesis de Diseño)."
        },
        {
          "texto": "4.4 Lugar de estudio",
          "nota": "Ubicación y descripción del área.",
          "instruccion_detallada": "Muestra la ubicación de la empresa y describe el área o lugar específico donde se realiza la investigación. Se recomienda: Usar Google maps indicando la ubicación. Usar una herramienta que permita visualizar el área donde se realiza la investigación. Contexto de la empresa."
        },
        {
          "texto": "4.5 Técnicas e instrumentos para la recolección de la información",
          "instruccion_detallada": "Define (citando) y sustente el uso de las técnicas e instrumentos utilizados en la investigación, especificando que información van a obtener. Las fichas de recolección de datos no requieren validación."
        },
        {
          "texto": "4.6 Análisis y procesamiento de datos",
          "instruccion_detallada": "Explica ¿Cómo se utiliza la información? Seguir las etapas del procedimiento especificando las herramientas utilizadas y como se analizan los datos."
        },
        {
          "texto": "4.7 Aspectos éticos en Investigación",
          "instruccion_detallada": "Considerar los principios del código de ética de la UNAC y especificar ¿Cómo se aplican los principios mencionados?"
        }
      ]
    },
    {
      "titulo": "V. CRONOGRAMA DE ACTIVIDADES",
      "contenido": [
        {
          "texto": "Cronograma de ejecución",
          "nota": "Secuencia del desarrollo de la investigación.",
          "instruccion_detallada": "Evidencia la secuencia del desarrollo de la investigación hasta la elaboración del informe final. La frecuencia (meses / semanas / días) va a depender de la investigación. No requiere enumerar como tabla. No requiere indicar elaboración propia."
        }
      ]
    },
    {
      "titulo": "VI. PRESUPUESTO",
      "contenido": [
        {
          "texto": "Recursos y Presupuesto",
          "nota": "Inversión, recursos humanos, materiales y financieros.",
          "instruccion_detallada": "Se debe presentar lo que el investigador ha invertido bajo su responsabilidad, en la investigación. Se considera los recursos humanos, materiales y financieros necesarios para el desarrollo de la investigación (en soles) e indicar la fuente de financiamiento."
        }
      ]
    }
  ],
  "finales": {
    "referencias": {
      "titulo": "VII. REFERENCIAS BIBLIOGRÁFICAS",
      "nota": "Las referencias deben seguir el estilo APA (7ma edición). Deben contener únicamente las fuentes citadas en el cuerpo del proyecto y ordenarse alfabéticamente.",
      "ejemplos": [
        "Chiavenato, I. (2011). Administración de recursos humanos (5.ª ed.). McGraw-Hill.",
        "Hernández Sampieri, R., Fernández Collado, C., & Baptista Lucio, P. (2014). Metodología de la investigación (6.ª ed.). McGraw-Hill.",
        "Pérez, J. (2023). Implementación de un sistema de mantenimiento preventivo [Tesis de pregrado, Universidad Nacional del Callao]. Repositorio Institucional UNAC.",
        "Rodríguez, L. (2022). Análisis de fallas en sistemas de bombeo. Revista Ingeniería Mecánica, 15(2), 45-52. https://doi.org/10.1016/j.eng.2022.01.001"
      ]
    },
    "anexos": {
      "titulo_seccion": "VIII. ANEXOS",
      "lista": [
        {
          "titulo": "Anexo 1: Matriz de consistencia",
          "nota": "Está conformada por una matriz (cuadro) formado por columnas y filas que permite evaluar la coherencia y conexión lógica que existe entre el título de la investigación, la formulación del problema, el (los) objetivo(s), la (s) hipótesis, las variables, y la metodología. (Resolución 017-18-CU)."
        },
        {
          "titulo": "Anexo 2: Herramienta de ingeniería para el análisis de la problemática",
          "nota": "Se debe incluir la aplicación de al menos una herramienta de ingeniería utilizada para evidenciar el problema central (Ejemplo: Diagrama de Pareto, Diagrama de Ishikawa, Árbol de problemas, Matriz de relevancia, entre otras)."
        },
        {
          "titulo": "Anexo 3: Autorización del uso de datos",
          "nota": "Utilice este formato para imprimirlo en papel membretado con las firmas correspondientes:\n\nYo .................................................................................., identificado con DNI .................................., en mi calidad de ........................................................... del área ......................................... de la empresa/institución ................................................................................................. con R.U.C N° ................................................., ubicada en la ciudad de ............................................\n\nOTORGO LA AUTORIZACIÓN..."
        },
        {
          "titulo": "Anexo 4: Ficha de recolección de datos",
          "nota": "Adjuntar los formatos de las fichas, cuestionarios o guías de observación utilizados para la captura de datos en campo. Nota: Las fichas de recolección de datos no requieren validación por juicio de expertos según normativa vigente."
        }
      ]
    }
  },
  "matriz_consistencia": {
    "problemas": {
      "general": "¿De qué manera la implementación de un plan de mantenimiento reduce el tiempo perdido en el área de trapiche de la empresa Pomalca - 2023?",
      "especificos": [
        "Realizar un diagnóstico inicial midiendo el tiempo perdido en el área de trapiche",
        "Realizar un análisis de criticidad de los equipos del área de trapiche.",
        "Desarrollar un análisis de modos y efectos de fallas de los equipos críticos.",
        "Programar las actividades del plan de mantenimiento de los equipos.",
        "Implementar el plan de mantenimiento preventivo elaborado.",
        "Medir el tiempo perdido después de la implementación del plan."
      ]
    },
    "objetivos": {
      "general": "Determinar cómo la implementación de un plan de mantenimiento reduce el tiempo perdido en el área de trapiche de la empresa Pomalca",
      "especificos": [
        "Realizar un diagnóstico inicial midiendo el tiempo perdido en el área de trapiche",
        "Realizar un análisis de criticidad de los equipos del área de trapiche.",
        "Desarrollar un análisis de modos y efectos de fallas de los equipos críticos.",
        "Programar las actividades del plan de mantenimiento de los equipos.",
        "Implementar el plan de mantenimiento preventivo elaborado.",
        "Medir el tiempo perdido después de la implementación del plan."
      ]
    },
    "hipotesis": {
      "general": "La implementación de un plan de mantenimiento reduce el tiempo perdido en el área de trapiche de la empresa Pomalca",
      "especificos": []
    },
    "variables": {
      "independiente": {
        "nombre": "PLAN DE MANTENIMIENTO",
        "dimensiones": [
          "Análisis de Criticidad",
          "AMEF",
          "Programación de actividades"
        ]
      },
      "dependiente": {
        "nombre": "TIEMPO PERDIDO",
        "dimensiones": []
      }
    },
    "metodologia": {
      "tipo": "Aplicada",
      "enfoque": "Cuantitativo",
      "nivel": "Explicativo",
      "diseno": "Pre Experimental",
      "poblacion": "32 equipos del área de Trapiche",
      "muestra": "24 equipos críticos",
      "tecnicas": "Análisis documental, Observación",
      "instrumentos": "Ficha de recolección de datos",
      "procesamiento": "SPSS v25"
    }
  }
}

```

---

## app/data/uni/alerts.json
**Tama?o:** 2
**SHA256:** 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
**Tipo:** json

```json
[]
```

---

## app/data/uni/formatos.json
**Tama?o:** 342
**SHA256:** 4dd73f09321e363073de8bb9674e72a0df48b9d29712b5a82b87b8f10571a233
**Tipo:** json

```json
[
  {
    "id": "uni-civil-suficiencia",
    "uni": "UNI",
    "titulo": "Formato Informe de Suficiencia",
    "facultad": "Ingeniería Civil",
    "escuela": "Modalidad profesional",
    "estado": "VIGENTE",
    "version": "1.1",
    "fecha": "2024-01-10",
    "resumen": "Formato para titulación.",
    "historial": []
  }
]

```

---

## app/main.py
**Tama?o:** 1595
**SHA256:** b16e27fceb4b0dabeabd6e058db5f19d7e46c9afeec5245503ae94098a1b02b2
**Tipo:** python

```python
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.modules.home.router import router as home_router
from app.modules.catalog.router import router as catalog_router
from app.modules.formats.router import router as formats_router
from app.modules.alerts.router import router as alerts_router
from app.modules.admin.router import router as admin_router

app = FastAPI(title="Formatoteca", version="0.1.0")

@app.middleware("http")
async def ensure_utf8_charset(request: Request, call_next):
    response = await call_next(request)
    content_type = response.headers.get("content-type")
    if content_type:
        lower_type = content_type.lower()
        if (
            lower_type.startswith("text/")
            or lower_type.startswith("application/json")
            or lower_type.startswith("application/javascript")
        ) and "charset=" not in lower_type:
            response.headers["content-type"] = f"{content_type}; charset=utf-8"
    return response

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/recursos_data", StaticFiles(directory="app/data/unac"), name="data_unac")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return RedirectResponse(url="/static/assets/LogoUNAC.png")

# Routers (cada módulo es una sección del mockup)
app.include_router(home_router)
app.include_router(catalog_router)
app.include_router(formats_router)
app.include_router(alerts_router)
app.include_router(admin_router)

```

---

## app/modules/admin/__init__.py
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** python

```python

```

---

## app/modules/admin/router.py
**Tama?o:** 471
**SHA256:** d68b942876c34aa60e1e8dbbb7b4a0bd660525cfff7f623c810a2215ae988494
**Tipo:** python

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter()

@router.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    return templates.TemplateResponse(
        "pages/admin.html",
        {
            "request": request,
            "title": "Admin",
            "breadcrumb": "Admin",
            "active_nav": "admin",
        },
    )

```

---

## app/modules/admin/schemas.py
**Tama?o:** 149
**SHA256:** e26035c71136e678bc247393b5717e16e1d86be8a6ce1ac9b253135d4a2b1db2
**Tipo:** python

```python
"""Schemas (placeholder) - módulo admin

Aquí luego pueden ir modelos Pydantic, por ejemplo:
- FormatoOut
- AlertOut
- filtros/requests
"""

```

---

## app/modules/admin/service.py
**Tama?o:** 254
**SHA256:** d76dba01b4da9cb4790d5019ee14b78a500bd27cbe1678a09e248eba361d3100
**Tipo:** python

```python
"""Service layer (placeholder) - módulo admin

Aquí va la lógica del negocio (luego):
- lectura desde BD o API
- validación de vigencia
- filtros, búsquedas
- versionado, auditoría, etc.
"""

# TODO: implementar lógica del módulo admin

```

---

## app/modules/alerts/__init__.py
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** python

```python

```

---

## app/modules/alerts/router.py
**Tama?o:** 762
**SHA256:** 5b8d0963faeb95d3db1ea25ea95ed865a326d945ce6364f6179c80ca6728feae
**Tipo:** python

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.core.university_registry import get_provider

router = APIRouter()

@router.get("/alerts", response_class=HTMLResponse)
def alerts(request: Request):
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)

    return templates.TemplateResponse(
        "pages/alerts.html",
        {
            "request": request,
            "title": "Notificaciones",
            "breadcrumb": "Notificaciones",
            "alerts": provider.list_alerts(),
            "active_nav": "alerts",
            "active_uni": provider.code,
            "uni_name": provider.name,
        },
    )

```

---

## app/modules/alerts/schemas.py
**Tama?o:** 150
**SHA256:** 624ac37b81edef8a6c4bdd62efd11ce8d61c6d5f982031a3fd54003143a716d4
**Tipo:** python

```python
"""Schemas (placeholder) - módulo alerts

Aquí luego pueden ir modelos Pydantic, por ejemplo:
- FormatoOut
- AlertOut
- filtros/requests
"""

```

---

## app/modules/alerts/service.py
**Tama?o:** 256
**SHA256:** d5f2e76689577cf33b72cc0805d2082c3dc284f2642b4b29b6d30b1ba0ae045e
**Tipo:** python

```python
"""Service layer (placeholder) - módulo alerts

Aquí va la lógica del negocio (luego):
- lectura desde BD o API
- validación de vigencia
- filtros, búsquedas
- versionado, auditoría, etc.
"""

# TODO: implementar lógica del módulo alerts

```

---

## app/modules/catalog/__init__.py
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** python

```python

```

---

## app/modules/catalog/router.py
**Tama?o:** 2027
**SHA256:** 8d75150fc29fe77d701707158f75c774fb52f88e3f5c8264c5187686597e3b50
**Tipo:** python

```python
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import ValidationError

from app.core.templates import templates
from app.modules.catalog.schemas import FormatoGenerateIn
from app.modules.catalog import service

router = APIRouter()


@router.get("/catalog", response_class=HTMLResponse)
async def get_catalog(request: Request):
    """Get all formats for catalog view."""
    uni = request.query_params.get("uni")
    if uni and uni.strip().lower() == "all":
        uni = None
    catalog = service.build_catalog(uni)
    formatos = catalog["formatos"]
    return templates.TemplateResponse(
        "pages/catalog.html",
        {
            "request": request,
            "title": "Catalogo",
            "breadcrumb": "Catalogo",
            "active_nav": "catalog",
            "formatos": formatos,
            "catalogo": catalog["grouped"],
            "active_uni": uni,
            "uni_name": (uni or "ALL").upper(),
        },
    )


@router.post("/catalog/generate")
async def generate_document(request: Request, background_tasks: BackgroundTasks):
    """Generate a document from a format."""
    try:
        payload = FormatoGenerateIn(**(await request.json()))
    except ValidationError:
        return JSONResponse({"error": "Datos invalidos"}, status_code=400)

    try:
        output_path, filename = service.generate_document(payload.format, payload.sub_type, payload.uni or "unac")
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except RuntimeError as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)

    background_tasks.add_task(service.cleanup_temp_file, output_path)
    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        background=background_tasks,
    )

```

---

## app/modules/catalog/schemas.py
**Tama?o:** 722
**SHA256:** 5c3a4c7ae68455600b428fa64a39f0e7361415bec80aa4fb9faa7b6503da82d0
**Tipo:** python

```python
"""Schemas for catalog module."""

from typing import List, Optional
from pydantic import BaseModel


class FormatoOut(BaseModel):
    id: Optional[str] = None
    uni: Optional[str] = None
    titulo: Optional[str] = None
    facultad: Optional[str] = None
    escuela: Optional[str] = None
    estado: Optional[str] = None
    version: Optional[str] = None
    fecha: Optional[str] = None
    resumen: Optional[str] = None
    archivos: Optional[List[dict]] = None
    historial: Optional[List[dict]] = None


class FormatoGenerateIn(BaseModel):
    format: str
    sub_type: str
    uni: Optional[str] = None


class FormatoGenerateOut(BaseModel):
    ok: bool
    filename: str
    path: str

```

---

## app/modules/catalog/service.py
**Tama?o:** 6135
**SHA256:** b4c67d3dd6cb35b32e582632b0a48e13cfbe44e0bc066713f99a68684b1341b2
**Tipo:** python

```python
"""Service layer for catalog module."""

from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Sequence, Tuple, Union

from app.core.loaders import discover_format_files, load_format_by_id, load_json_file
from app.universities.registry import get_provider

ALIASES = {
    "pregrado": "informe",
}


TIPO_LABELS = {
    "informe": "Informe de Tesis",
    "maestria": "Tesis de Maestr\u00eda",
    "proyecto": "Proyecto de Tesis",
}
ENFOQUE_LABELS = {"cual": "Cualitativo", "cuant": "Cuantitativo"}
TIPO_FILTRO = {
    "informe": "Inv. Formativa",
    "maestria": "Suficiencia",
    "proyecto": "Tesis",
}


def _build_format_title(categoria: str, enfoque: str, raw_title: str, fallback_title: str) -> str:
    if raw_title:
        return raw_title
    cat_label = TIPO_LABELS.get(categoria)
    enfoque_label = ENFOQUE_LABELS.get(enfoque)
    if cat_label and enfoque_label:
        return f"{cat_label} - {enfoque_label}"
    if cat_label:
        return cat_label
    return fallback_title or categoria.capitalize()


def _build_format_entry(item, data: Dict) -> Dict:
    raw_title = data.get("titulo") if isinstance(data, dict) else None
    titulo = _build_format_title(item.categoria, item.enfoque, raw_title, item.titulo)
    cat_label = TIPO_LABELS.get(item.categoria, item.categoria.capitalize())
    enfoque_label = ENFOQUE_LABELS.get(item.enfoque)
    resumen = None
    if isinstance(data, dict):
        resumen = data.get("descripcion")
    if not resumen:
        if enfoque_label:
            resumen = f"Plantilla oficial de {cat_label} con enfoque {enfoque_label}"
        else:
            resumen = f"Plantilla oficial de {cat_label}"

    return {
        "id": item.format_id,
        "uni": item.uni.upper(),
        "uni_code": item.uni,
        "tipo": TIPO_FILTRO.get(item.categoria, "Otros"),
        "titulo": titulo,
        "facultad": (data.get("facultad") if isinstance(data, dict) and data.get("facultad") else "Centro de Formatos UNAC"),
        "escuela": (data.get("escuela") if isinstance(data, dict) and data.get("escuela") else "Direcci\u00f3n Acad\u00e9mica"),
        "estado": "VIGENTE",
        "version": data.get("version", "1.0.0") if isinstance(data, dict) else "1.0.0",
        "fecha": (data.get("fecha") if isinstance(data, dict) and data.get("fecha") else "2026-01-17"),
        "resumen": resumen,
        "tipo_formato": item.categoria,
        "enfoque": item.enfoque,
    }


def build_catalog(uni: Optional[str] = None) -> Dict[str, Dict]:
    formatos: List[Dict] = []
    grouped: Dict[str, Dict] = {}

    for item in discover_format_files(uni):
        try:
            data = item.data if item.data is not None else load_json_file(item.path)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Warning: Could not load {item.path}: {exc}")
            continue

        entry = _build_format_entry(item, data)
        formatos.append(entry)
        grouped.setdefault(item.uni, {}).setdefault(item.categoria, {}).setdefault(item.enfoque, []).append(entry)

    return {"formatos": formatos, "grouped": grouped}


def get_all_formatos() -> List[Dict]:
    """Get all formats discovered under app/data."""
    return build_catalog(None)["formatos"]



def _normalize_format(fmt_type: str) -> str:
    fmt_type = (fmt_type or "").strip().lower()
    if fmt_type in ALIASES:
        fmt_type = ALIASES[fmt_type]
    return fmt_type


def _resolve_generator_command(
    generator: Union[Path, Sequence[str]],
    json_path: Path,
    output_path: Path,
) -> Tuple[List[str], Optional[Path]]:
    if isinstance(generator, (list, tuple)):
        cmd = [str(part) for part in generator]
        workdir = None
        for part in reversed(generator):
            part_str = str(part)
            if part_str.endswith(".py"):
                workdir = Path(part_str).resolve().parent
                break
        return cmd + [str(json_path), str(output_path)], workdir

    script_path = Path(generator)
    if not script_path.exists():
        raise RuntimeError(f"Script no encontrado: {script_path}")
    return [sys.executable, str(script_path), str(json_path), str(output_path)], script_path.parent


def cleanup_temp_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        print(f"[WARN] No se pudo eliminar temporal: {exc}")


def generate_document(fmt_type: str, sub_type: str, uni: str = "unac"):
    fmt_type = _normalize_format(fmt_type)
    sub_type = (sub_type or "").strip().lower()
    provider = get_provider(uni)
    generator = provider.get_generator_for_category(fmt_type)

    json_path = provider.get_data_dir() / fmt_type / f"{provider.code}_{fmt_type}_{sub_type}.json"
    if not json_path.exists():
        raise RuntimeError(f"JSON no encontrado: {json_path}")

    filename = f"{provider.code.upper()}_{fmt_type.upper()}_{sub_type.upper()}.docx"
    tmp_file = tempfile.NamedTemporaryFile(prefix="unac_", suffix=".docx", delete=False)
    output_path = Path(tmp_file.name)
    tmp_file.close()

    cmd, workdir = _resolve_generator_command(generator, json_path, output_path)
    result = subprocess.run(cmd, cwd=str(workdir) if workdir else None, capture_output=True, text=True)

    if result.returncode != 0:
        print("[ERROR PYTHON]", result.stderr)
        raise RuntimeError("Fallo la generacion interna. Revisa consola.")

    if not output_path.exists():
        raise RuntimeError("El script corrio pero no genero el DOCX")

    return output_path, filename

# NUEVA FUNCIÓN AGREGADA PARA LA VISTA PREVIA (CARÁTULAS)
def get_format_json_content(format_id: str) -> Dict:
    """
    Busca y devuelve el contenido crudo del JSON para las vistas previas.
    ID esperado: unac-informe-cual -> app/data/unac/informe/unac_informe_cual.json
    """
    try:
        return load_format_by_id(format_id)
    except Exception as e:
        print(f"[ERROR SERVICE] No se pudo leer JSON para {format_id}: {e}")
        raise

```

---

## app/modules/formats/__init__.py
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** python

```python

```

---

## app/modules/formats/router.py
**Tama?o:** 5674
**SHA256:** 0b38ad07f2acb5c53a21eb0551646ddb43274dbdf7bde8a77b4567a1c2700f75
**Tipo:** python

```python
"""Router for formats module."""
import tempfile
from pathlib import Path

import pythoncom
import win32com.client
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from app.core.loaders import find_format_index, load_format_by_id
from app.core.templates import templates
from app.modules.formats import service

router = APIRouter(prefix="/formatos", tags=["formatos"])


def _convert_docx_to_pdf(docx_path: str, pdf_path: str) -> None:
    """Convierte a PDF actualizando campos para que el índice salga completo."""
    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(docx_path, ReadOnly=0, AddToRecentFiles=False)
        doc.Fields.Update()
        for toc in doc.TablesOfContents:
            toc.Update()
        for tof in doc.TablesOfFigures:
            tof.Update()
        doc.SaveAs(pdf_path, FileFormat=17)
    finally:
        if doc is not None:
            doc.Close(False)
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


def _get_cached_pdf_path(format_id: str) -> Path:
    cache_dir = Path(tempfile.gettempdir()) / "formatoteca_unac_pdf_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_name = format_id.replace("/", "_")
    return cache_dir / f"{safe_name}.pdf"


def _get_source_mtime(format_id: str) -> float:
    item = find_format_index(format_id)
    if not item:
        return 0.0
    json_path = item.path
    script_name = service.SCRIPTS_CONFIG.get(item.categoria)
    script_path = service.CF_DIR / script_name if script_name else None
    json_mtime = json_path.stat().st_mtime if json_path.exists() else 0.0
    script_mtime = script_path.stat().st_mtime if script_path and script_path.exists() else 0.0
    return max(json_mtime, script_mtime)


@router.get("/{format_id}", response_class=HTMLResponse)
async def get_format_detail(format_id: str, request: Request):
    """Get detail view for a specific format."""
    try:
        formato = service.get_formato(format_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Formato no encontrado")
    
    return templates.TemplateResponse(
        "pages/detail.html",
        {
            "request": request,
            "formato": formato,
            "title": formato["titulo"],
            "breadcrumb": formato["titulo"],
        },
    )


@router.get("/{format_id}/versions", response_class=HTMLResponse)
async def get_format_versions(format_id: str, request: Request):
    """Get version history for a specific format."""
    try:
        formato = service.get_formato(format_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Formato no encontrado")
    
    versions = [
        {"version": "2.0", "date": "2026-01-17", "changes": "Actualización de plantilla"},
        {"version": "1.0", "date": "2025-12-01", "changes": "Versión inicial"},
    ]
    
    return templates.TemplateResponse(
        "pages/versions.html",
        {
            "request": request,
            "formato": formato,
            "versions": versions,
        },
    )


@router.post("/{format_id}/generate")
async def generate_format_document(format_id: str, background_tasks: BackgroundTasks):
    """Generate a DOCX document for the given format."""
    try:
        output_path, filename = service.generate_document(format_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    
    background_tasks.add_task(service.cleanup_temp_file, output_path)
    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/{format_id}/pdf")
async def get_format_pdf(format_id: str):
    """Genera el Word, lo convierte a PDF y lo devuelve."""
    try:
        cached_pdf = _get_cached_pdf_path(format_id)
        source_mtime = _get_source_mtime(format_id)
        if cached_pdf.exists() and cached_pdf.stat().st_mtime >= source_mtime:
            return FileResponse(
                path=str(cached_pdf),
                media_type="application/pdf",
                content_disposition_type="inline",
            )

        docx_path, _ = service.generate_document(format_id)
        _convert_docx_to_pdf(str(docx_path), str(cached_pdf))
        service.cleanup_temp_file(docx_path)

        return FileResponse(
            path=str(cached_pdf),
            media_type="application/pdf",
            content_disposition_type="inline",
        )

    except Exception as e:
        print(f"Error generando PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")


@router.get("/{format_id}/data")
async def get_format_data_json(format_id: str):
    """
    Devuelve el contenido JSON completo del formato.
    Usado para hidratar vistas dinamicas.
    """
    try:
        data = load_format_by_id(format_id)
        return JSONResponse(content=data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="JSON no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


```

---

## app/modules/formats/schemas.py
**Tama?o:** 151
**SHA256:** 6176facc3815e2b1f63e4f62825c08eb1bc766a0817592d4669892782bc4c672
**Tipo:** python

```python
"""Schemas (placeholder) - módulo formats

Aquí luego pueden ir modelos Pydantic, por ejemplo:
- FormatoOut
- AlertOut
- filtros/requests
"""

```

---

## app/modules/formats/service.py
**Tama?o:** 6957
**SHA256:** 27f262a2a134171ef38c5faffb788809c4f2cd71ea470931da3c6bb703c8e8c8
**Tipo:** python

```python
"""Service layer for formats module."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple, Union

from app.core.loaders import find_format_index, load_json_file
from app.universities.registry import get_provider


TIPO_LABELS = {
    "informe": "Informe de Tesis",
    "maestria": "Tesis de Maestr\u00eda",
    "proyecto": "Proyecto de Tesis",
}
ENFOQUE_LABELS = {"cual": "Cualitativo", "cuant": "Cuantitativo"}
TIPO_FILTRO = {
    "informe": "Inv. Formativa",
    "maestria": "Suficiencia",
    "proyecto": "Tesis",
}


def _build_format_title(categoria: str, enfoque: str, raw_title: str, fallback_title: str) -> str:
    if raw_title:
        return raw_title
    cat_label = TIPO_LABELS.get(categoria)
    enfoque_label = ENFOQUE_LABELS.get(enfoque)
    if cat_label and enfoque_label:
        return f"{cat_label} - {enfoque_label}"
    if cat_label:
        return cat_label
    return fallback_title or categoria.capitalize()


def _build_format_entry(item, data: Dict) -> Dict:
    raw_title = data.get("titulo") if isinstance(data, dict) else None
    titulo = _build_format_title(item.categoria, item.enfoque, raw_title, item.titulo)
    cat_label = TIPO_LABELS.get(item.categoria, item.categoria.capitalize())
    enfoque_label = ENFOQUE_LABELS.get(item.enfoque)
    resumen = None
    if isinstance(data, dict):
        resumen = data.get("descripcion")
    if not resumen:
        if enfoque_label:
            resumen = f"Plantilla oficial de {cat_label} con enfoque {enfoque_label}"
        else:
            resumen = f"Plantilla oficial de {cat_label}"

    return {
        "id": item.format_id,
        "uni": item.uni.upper(),
        "uni_code": item.uni,
        "tipo": TIPO_FILTRO.get(item.categoria, "Otros"),
        "titulo": titulo,
        "facultad": (data.get("facultad") if isinstance(data, dict) and data.get("facultad") else "Centro de Formatos UNAC"),
        "escuela": (data.get("escuela") if isinstance(data, dict) and data.get("escuela") else "Direcci\u00f3n Acad\u00e9mica"),
        "estado": "VIGENTE",
        "version": data.get("version", "1.0.0") if isinstance(data, dict) else "1.0.0",
        "fecha": (data.get("fecha") if isinstance(data, dict) and data.get("fecha") else "2026-01-17"),
        "resumen": resumen,
        "tipo_formato": item.categoria,
        "enfoque": item.enfoque,
    }


def get_formato(format_id: str) -> Optional[Dict]:
    """
    Get a specific format by ID.
    """
    item = find_format_index(format_id)
    if not item:
        raise ValueError(f"Format not found: {format_id}")

    try:
        data = item.data if item.data is not None else load_json_file(item.path)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"Format not found: {format_id}") from exc

    return _build_format_entry(item, data)

def _resolve_generator_command(
    generator: Union[Path, Sequence[str]],
    json_path: Path,
    output_path: Path,
) -> Tuple[list[str], Optional[Path]]:
    if isinstance(generator, (list, tuple)):
        cmd = [str(part) for part in generator]
        workdir = None
        for part in reversed(generator):
            part_str = str(part)
            if part_str.endswith(".py"):
                workdir = Path(part_str).resolve().parent
                break
        return cmd + [str(json_path), str(output_path)], workdir

    script_path = Path(generator)
    if not script_path.exists():
        raise RuntimeError(f"Generator script not found: {script_path}")
    return [sys.executable, str(script_path), str(json_path), str(output_path)], script_path.parent


def generate_document(format_id: str, section_filter: Optional[str] = None) -> Tuple[Path, str]:
    """
    Generate a DOCX document for the given format.
    Allows filtering by section.
    """
    item = find_format_index(format_id)
    if not item:
        raise ValueError(f"Invalid format ID: {format_id}")

    tipo = item.categoria
    enfoque = item.enfoque

    provider = get_provider(item.uni)
    generator = provider.get_generator_for_category(tipo)

    json_path = item.path
    if not json_path.exists():
        raise RuntimeError(f"JSON file not found: {json_path}")

    # =========================================================
    # LOGICA DE FILTRADO (SIMPLIFICADA Y AGRESIVA)
    # =========================================================
    path_to_use = json_path

    if section_filter == "planteamiento":
        print(f"[DEBUG] Filtrando SOLO CAP\u00cdTULO I para: {format_id}")

        # 1. Cargamos el JSON original
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 2. LIMPIEZA TOTAL: Vaciamos todo lo que no sea el cuerpo
        data["preliminares"] = {}
        data["finales"] = {}
        data["matriz_consistencia"] = {}

        if "caratula" in data:
            data["caratula"]["tipo_documento"] = "VISTA PREVIA - CAP\u00cdTULO I"

        # 3. FILTRO RAPIDO: Nos quedamos SOLO con el bloque que tenga "PLANTEAMIENTO"
        # Esto elimina cualquier otro capitulo de la lista.
        data["cuerpo"] = [
            cap for cap in data.get("cuerpo", [])
            if "PLANTEAMIENTO" in cap.get("titulo", "").upper()
        ]

        # 4. Guardamos el JSON filtrado
        tmp_json = tempfile.NamedTemporaryFile(prefix="filtered_", suffix=".json", delete=False, mode="w", encoding="utf-8")
        json.dump(data, tmp_json, ensure_ascii=False, indent=2)
        tmp_json.close()

        path_to_use = Path(tmp_json.name)
    # =========================================================

    filename = f"{provider.code.upper()}_{tipo.upper()}_{enfoque.upper()}.docx"
    tmp_file = tempfile.NamedTemporaryFile(prefix="unac_", suffix=".docx", delete=False)
    output_path = Path(tmp_file.name)
    tmp_file.close()

    cmd, workdir = _resolve_generator_command(generator, path_to_use, output_path)
    result = subprocess.run(cmd, cwd=str(workdir) if workdir else None, capture_output=True, text=True)

    # Debug logs (util si falla)
    # print(f"[DEBUG] Stderr: {result.stderr}")

    # Limpiamos el JSON temporal
    if path_to_use != json_path:
        try:
            path_to_use.unlink()
        except Exception:
            pass

    if result.returncode != 0:
        print("[ERROR]", result.stderr)
        raise RuntimeError("Document generation failed. Check console for details.")

    if not output_path.exists():
        raise RuntimeError("Generator script executed but did not create DOCX file.")

    return output_path, filename


def cleanup_temp_file(path: Path) -> None:
    """Clean up temporary file."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        print(f"[WARN] Could not delete temp file: {exc}")

```

---

## app/modules/home/__init__.py
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** python

```python

```

---

## app/modules/home/router.py
**Tama?o:** 738
**SHA256:** b03570801789cad96401e30f3a7ad7a3b8201c822ec2c16970bfefa2d4f12a6f
**Tipo:** python

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.core.university_registry import get_provider

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)

    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "title": "Inicio",
            "breadcrumb": "Inicio",
            "alerts": provider.list_alerts()[:3],
            "active_nav": "home",
            "active_uni": provider.code,
            "uni_name": provider.name,
        },
    )

```

---

## app/modules/home/schemas.py
**Tama?o:** 148
**SHA256:** 6f40e2b62fe3da2f79b4af9366ade8cc12bce10cfd76395e299a50c2d70ff53c
**Tipo:** python

```python
"""Schemas (placeholder) - módulo home

Aquí luego pueden ir modelos Pydantic, por ejemplo:
- FormatoOut
- AlertOut
- filtros/requests
"""

```

---

## app/modules/home/service.py
**Tama?o:** 252
**SHA256:** 0da5172714e357b25445ed582ef8610375ff3d3aeee47a3aa1af93170940678a
**Tipo:** python

```python
"""Service layer (placeholder) - módulo home

Aquí va la lógica del negocio (luego):
- lectura desde BD o API
- validación de vigencia
- filtros, búsquedas
- versionado, auditoría, etc.
"""

# TODO: implementar lógica del módulo home

```

---

## app/static/css/extra.css
**Tama?o:** 620
**SHA256:** fb030f799ac4deb3d96b00c461ba2a7bdc265a914dd24c5a2cae5603c8b5827a
**Tipo:** css

```css
body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; }

/* Animación suave */
.fade-in { animation: fadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Scrollbar sutil */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

```

---

## app/static/js/catalog.js
**Tama?o:** 11284
**SHA256:** f67e72d9a0bf4436cf4247992baf2872ac9207fe611046412095d8c22663bceb
**Tipo:** js

```javascript
/**
 * catalog.js v6.0
 * Flujo: Nivel 1 (Modo) -> Nivel 2 (Categoría Persistente) -> Nivel 3 (Resultados)
 */

let currentMode = 'normal'; // 'normal', 'caratula', 'referencias'

/* ==========================================================================
   1. GESTIÓN VISUAL (SOMBREADO DE TARJETAS)
   ========================================================================== */

// Sombrea las tarjetas de Nivel 1 (Accesos Rápidos)
function highlightTopCard(cardId) {
    document.querySelectorAll('.quick-card').forEach(card => {
        card.classList.remove('ring-2', 'ring-offset-2', 'ring-orange-500', 'ring-indigo-500', 'ring-green-500', 'border-orange-500', 'border-indigo-500', 'border-green-500');
        card.classList.add('border-gray-200');
    });

    const activeCard = document.getElementById(cardId);
    if (!activeCard) return;

    activeCard.classList.remove('border-gray-200');
    if (cardId.includes('caratulas')) activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-orange-500', 'border-orange-500');
    else if (cardId.includes('referencias')) activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-indigo-500', 'border-indigo-500');
    else activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-green-500', 'border-green-500');
}

// Sombrea las tarjetas de Nivel 2 (Filtro Categoría)
function highlightCategoryCard(cardId) {
    document.querySelectorAll('.cat-card').forEach(card => {
        card.classList.remove('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
        card.classList.add('border-gray-200');
        // Reset backgrounds (opcional, si quisieras un estado "inactivo" más fuerte)
    });

    const activeCard = document.getElementById(cardId);
    if (activeCard) {
        activeCard.classList.remove('border-gray-200');
        activeCard.classList.add('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
    }
}

/* ==========================================================================
   2. CONTROL DE FLUJO (NIVEL 1 -> NIVEL 2)
   ========================================================================== */

function iniciarFlujo(modo, cardId) {
    currentMode = modo;
    highlightTopCard(cardId);

    // 1. Mostrar Bloque Categorías (Nivel 2)
    const categorias = document.getElementById("bloque-categorias");
    categorias.classList.remove("hidden");
    setTimeout(() => { 
        categorias.classList.remove("opacity-0", "translate-y-4");
        categorias.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);

    // 2. Ocultar Resultados (Nivel 3) hasta que elija categoría
    const resultados = document.getElementById("bloque-resultados");
    resultados.classList.add("hidden", "opacity-0", "translate-y-4");

    // 3. Limpiar selección visual del Nivel 2
    document.querySelectorAll('.cat-card').forEach(c => {
        c.classList.remove('ring-2', 'ring-offset-2', 'ring-blue-500', 'border-blue-500');
        c.classList.add('border-gray-200');
    });
}

/* ==========================================================================
   3. CONTROL DE FLUJO (NIVEL 2 -> NIVEL 3)
   ========================================================================== */

function seleccionarCategoriaFinal(filtro, cardId) {
    // 1. Visual Nivel 2
    highlightCategoryCard(cardId);

    // 2. Filtrar Grid
    filtrarGrid(filtro);

    // 3. Aplicar Estilos según el Modo (Normal, Carátula, Ref)
    aplicarEstilosGrid();

    // 4. Mostrar Resultados (Nivel 3)
    const resultados = document.getElementById("bloque-resultados");
    resultados.classList.remove("hidden");
    setTimeout(() => { 
        resultados.classList.remove("opacity-0", "translate-y-4");
        // Scroll suave hacia los resultados, pero manteniendo Nivel 2 visible
        resultados.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
}

function filtrarGrid(categoria) {
    const cards = document.querySelectorAll(".formato-card");
    let count = 0;
    cards.forEach((card) => {
        if (categoria === "todos" || card.getAttribute("data-tipo") === categoria) {
            card.style.display = "flex"; 
            count++;
        } else {
            card.style.display = "none";
        }
    });
}

function aplicarEstilosGrid() {
    document.querySelectorAll(".formato-card").forEach(card => {
        const badge = card.querySelector(".mode-badge");
        const actionText = card.querySelector(".action-text");
        
        // Reset clases base
        card.className = "formato-card group bg-white rounded-xl shadow-sm border border-gray-200 transition-all cursor-pointer flex flex-col h-full overflow-hidden relative hover:shadow-lg";
        card.querySelector(".original-badges").classList.remove("opacity-30");
        badge.classList.add("hidden");

        if (currentMode === 'caratula') {
            card.querySelector(".original-badges").classList.add("opacity-30");
            card.classList.add("hover:border-orange-300");
            
            badge.className = "mode-badge absolute top-3 right-3 z-10 bg-orange-100 text-orange-700 text-[10px] font-bold px-2 py-1 rounded shadow-sm border border-orange-200 flex items-center gap-1";
            badge.innerHTML = `<i data-lucide="eye" class="w-3 h-3"></i> CARÁTULA`;
            badge.classList.remove("hidden");

            actionText.innerHTML = `Ver Carátula <i data-lucide="eye" class="w-4 h-4"></i>`;
            actionText.className = "action-text text-orange-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform";

        } else if (currentMode === 'referencias') {
            card.querySelector(".original-badges").classList.add("opacity-30");
            card.classList.add("hover:border-indigo-300");

            badge.className = "mode-badge absolute top-3 right-3 z-10 bg-indigo-100 text-indigo-700 text-[10px] font-bold px-2 py-1 rounded shadow-sm border border-indigo-200 flex items-center gap-1";
            badge.innerHTML = `<i data-lucide="book-open" class="w-3 h-3"></i> REFERENCIAS`;
            badge.classList.remove("hidden");

            actionText.innerHTML = `Ver Normas <i data-lucide="search" class="w-4 h-4"></i>`;
            actionText.className = "action-text text-indigo-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform";

        } else { // Normal
            card.classList.add("hover:border-blue-300");
            actionText.innerHTML = `Ver Estructura <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>`;
            actionText.className = "action-text text-blue-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform";
        }
    });
    
    if(typeof lucide !== 'undefined') lucide.createIcons();
}

/* ==========================================================================
   4. INTERCEPTOR DE CLICS (MODALES vs NAVEGACIÓN)
   ========================================================================== */
function handleCardClick(event, formatId) {
    if (currentMode === 'caratula') {
        event.preventDefault();
        previewCover(formatId);
        return false;
    } 
    else if (currentMode === 'referencias') {
        event.preventDefault();
        previewReferencias(formatId);
        return false;
    }
    return true; 
}

/* ==========================================================================
   5. MODALES (DATA FETCH)
   ========================================================================== */
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

async function fetchFormatData(formatId) {
    const response = await fetch(`/formatos/${formatId}/data`);
    if (!response.ok) throw new Error("Error cargando datos.");
    return await response.json();
}

// Modal Carátula
async function previewCover(formatId) {
    const modal = document.getElementById('coverModal');
    const loader = document.getElementById('coverLoader');
    const content = document.getElementById('coverContent');
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    try {
        const data = await fetchFormatData(formatId);
        const c = data.caratula || {}; 
        document.getElementById('c-uni').textContent = c.universidad || "UNIVERSIDAD NACIONAL DEL CALLAO";
        document.getElementById('c-fac').textContent = c.facultad || "";
        document.getElementById('c-esc').textContent = c.escuela || "";
        document.getElementById('c-titulo').textContent = c.titulo_placeholder || "TÍTULO DEL PROYECTO";
        document.getElementById('c-frase').textContent = c.frase_grado || "";
        document.getElementById('c-grado').textContent = c.grado_objetivo || "";
        document.getElementById('c-lugar').textContent = (c.pais || "CALLAO, PERÚ");
        document.getElementById('c-anio').textContent = (c.fecha || "2026");
        const guiaEl = document.getElementById('c-guia');
        if (guiaEl) {
            const guia = (c.guia || c.nota || "").trim();
            guiaEl.textContent = guia;
            guiaEl.classList.toggle('hidden', !guia);
        }
        loader.classList.add('hidden');
        content.classList.remove('hidden');
    } catch (error) {
        closeModal('coverModal');
        alert("Error cargando carátula.");
    }
}

// Modal Referencias
async function previewReferencias(formatId) {
    const modal = document.getElementById('refModal');
    const loader = document.getElementById('refLoader');
    const content = document.getElementById('refContent');
    const list = document.getElementById('refList');
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    list.innerHTML = "";
    try {
        const data = await fetchFormatData(formatId);
        const refData = data.finales?.referencias || {};
        let htmlContent = "";
        if (refData.titulo) htmlContent += `<h4 class="font-bold text-lg mb-3 text-indigo-900 border-b pb-2">${refData.titulo}</h4>`;
        if (refData.nota) htmlContent += `<div class="p-4 bg-indigo-50 text-indigo-800 rounded-lg mb-4 text-sm italic">${refData.nota}</div>`;
        if (refData.secciones && Array.isArray(refData.secciones)) {
            refData.secciones.forEach(sec => { htmlContent += `<p class="mb-3"><span class="font-bold">${sec.sub || ''}</span> ${sec.texto}</p>`; });
        } else if (refData.contenido && Array.isArray(refData.contenido)) {
             refData.contenido.forEach(item => { htmlContent += `<p class="mb-2">• ${item.texto}</p>`; });
        } else if (!refData.titulo) { htmlContent = "<p class='text-gray-500 italic text-center'>No se encontró información.</p>"; }
        list.innerHTML = htmlContent;
        loader.classList.add('hidden');
        content.classList.remove('hidden');
    } catch (error) {
        closeModal('refModal');
        alert("Error cargando referencias.");
    }
}

```

---

## app/static/js/format-viewer.js
**Tama?o:** 19429
**SHA256:** 30c0e185e95255c194ec5ef813984526e57b5677516a668aa686a87bf56b4c0b
**Tipo:** js

```javascript
/**
 * Lógica para visualización y descarga de formatos.
 * Maneja: Word (Descarga), PDF (Preview), Carátula (JSON), Índice (JSON) y Capítulos (JSON).
 */

function buildJsonPath(formatId) {
  return `/formatos/${formatId}/data`;
}

async function fetchFormatJson(formatId) {
  const jsonPath = buildJsonPath(formatId);
  const response = await fetch(jsonPath + '?t=' + new Date().getTime());
  if (!response.ok) {
    throw new Error(`No se encontr\u00f3 el archivo (Error ${response.status}) en: ${jsonPath}`);
  }
  return response.json();
}

function shortGuide(text) {
  if (!text) return 'Ver detalle en la vista previa.';
  const line = text.split(/\n+/)[0].trim();
  return line || 'Ver detalle en la vista previa.';
}

// --- 1. Descargar DOCX ---
async function downloadDocument(formatId) {
  const btn = document.getElementById('download-btn');
  const btnText = document.getElementById('download-text');
  const originalText = btnText.textContent;
  
  try {
    btn.disabled = true;
    btnText.textContent = 'Generando...';
    
    const response = await fetch(`/formatos/${formatId}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al generar el documento');
    }
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `UNAC_${formatId.split('-').slice(1).join('_').toUpperCase()}.docx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
    
    btnText.textContent = 'Descargado ✓';
    setTimeout(() => {
      btnText.textContent = originalText;
      btn.disabled = false;
    }, 2000);
  } catch (error) {
    console.error('Error:', error);
    alert('Error: ' + error.message);
    btnText.textContent = originalText;
    btn.disabled = false;
  }
}

// --- 2. Modal PDF (Vista Previa General) ---
function openPdfModal(formatId) {
    const modal = document.getElementById('pdfModal');
    const viewer = document.getElementById('pdfViewer');
    const title = document.getElementById('modal-title');
    
    if(title) title.innerText = "Vista de Lectura";

    const pdfUrl = `/formatos/${formatId}/pdf`; 
    
    viewer.src = pdfUrl + "#page=1&view=Fit&toolbar=0&navpanes=0"; 
    modal.classList.remove('hidden'); 
}

function closePdfModal() {
    const modal = document.getElementById('pdfModal');
    const viewer = document.getElementById('pdfViewer');
    modal.classList.add('hidden'); 
    viewer.src = ''; 
}

// --- 3. Visualizador de Carátula (JSON) ---
async function previewCover(formatId) {
    const modal = document.getElementById('coverModal');
    const loader = document.getElementById('coverLoader');
    const content = document.getElementById('coverContent');
    
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');

    try {
        const data = await fetchFormatJson(formatId);
        const c = data.caratula || {};
        if (!Object.keys(c).length) throw new Error("No se encontró configuración de carátula.");

        document.getElementById('c-uni').textContent = c.universidad || "UNIVERSIDAD NACIONAL DEL CALLAO";
        document.getElementById('c-fac').textContent = c.facultad || "";
        document.getElementById('c-esc').textContent = c.escuela || "";
        document.getElementById('c-titulo').textContent = c.titulo_placeholder || "TÍTULO DE INVESTIGACIÓN";
        document.getElementById('c-frase').textContent = c.frase_grado || "";
        document.getElementById('c-grado').textContent = c.grado_objetivo || "";
        document.getElementById('c-lugar').textContent = (c.pais || "CALLAO, PERÚ");
        document.getElementById('c-anio').textContent = (c.fecha || "2026");
        const guiaEl = document.getElementById('c-guia');
        if (guiaEl) {
            const guia = (c.guia || c.nota || "").trim();
            guiaEl.textContent = guia;
            guiaEl.classList.toggle('hidden', !guia);
        }

        loader.classList.add('hidden');
        content.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        alert("Error cargando carátula: " + error.message);
        closeCoverModal();
    }
}

function closeCoverModal() {
    document.getElementById('coverModal').classList.add('hidden');
}

// --- 4. Visualizador de Índice (Inteligente) ---
async function previewIndex(formatId) {
    const modal = document.getElementById('indexModal');
    const loader = document.getElementById('indexLoader');
    const content = document.getElementById('indexContent');
    const listContainer = document.getElementById('indexList');
    
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    listContainer.innerHTML = ''; 

    try {
        const data = await fetchFormatJson(formatId);
        let structure = [];

        if (data.estructura) {
            structure = data.estructura;
        } else {
            if (data.preliminares && data.preliminares.introduccion) {
                structure.push({ titulo: data.preliminares.introduccion.titulo, nivel: 1 });
            }
            if (data.cuerpo) {
                data.cuerpo.forEach(cap => {
                    if (cap.titulo) structure.push({ titulo: cap.titulo, nivel: 1 });
                    if (cap.contenido && Array.isArray(cap.contenido)) {
                        cap.contenido.forEach(sub => {
                            if (sub.texto) structure.push({ titulo: sub.texto, nivel: 2 });
                        });
                    }
                });
            }
            if (data.finales) {
                if (data.finales.referencias) structure.push({ titulo: data.finales.referencias.titulo, nivel: 1 });
                if (data.finales.anexos) structure.push({ titulo: data.finales.anexos.titulo_seccion, nivel: 1 });
            }
        }

        structure.forEach(item => {
            const row = document.createElement('div');
            row.className = "flex items-baseline w-full";
            const isMain = item.nivel === 1;
            const textClass = isMain ? "font-bold text-gray-900 uppercase mt-2" : "pl-6 text-gray-700";
            
            row.innerHTML = `
                <span class="${textClass} flex-shrink-0">${item.titulo}</span>
                <span class="border-b border-dotted border-gray-400 flex-1 mx-2 relative top-[-4px]"></span>
                <span class="text-gray-500 text-xs">00</span>
            `;
            listContainer.appendChild(row);
        });

        loader.classList.add('hidden');
        content.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        alert("Error cargando índice: " + error.message);
        closeIndexModal();
    }
}

function closeIndexModal() {
    document.getElementById('indexModal').classList.add('hidden');
}

// --- 5. Visualizador Genérico de Capítulos (I al VII) ---
async function previewChapter(formatId, searchPrefix) {
    const modal = document.getElementById('chapterModal');
    const loader = document.getElementById('chapterLoader');
    const content = document.getElementById('chapterContent');
    const listContainer = document.getElementById('chapterList');
    const titleContainer = document.getElementById('chapterTitle');
    
    modal.classList.remove('hidden');
    loader.classList.remove('hidden');
    content.classList.add('hidden');
    listContainer.innerHTML = ''; 

    try {
        const data = await fetchFormatJson(formatId);

        // BÚSQUEDA INTELIGENTE
        let capitulo = null;
        // 1. Buscar en el cuerpo
        if (data.cuerpo) {
            capitulo = data.cuerpo.find(cap => 
                cap.titulo && cap.titulo.trim().toUpperCase().startsWith(searchPrefix)
            );
        }
        // 2. Buscar en finales (Referencias/Anexos)
        if (!capitulo && data.finales) {
            const prefix = (searchPrefix || "").toUpperCase();
            if ((prefix.includes("REFERENCIAS") || prefix.includes("BIBLIOGRAF")) && data.finales.referencias) {
                capitulo = data.finales.referencias;
            } else if (prefix.includes("ANEXO") && data.finales.anexos) {
                capitulo = data.finales.anexos;
            }
        }

        if (!capitulo) throw new Error(`No se encontró el Capítulo ${searchPrefix} en el JSON.`);

        // RENDERIZADO
        titleContainer.textContent = capitulo.titulo || capitulo.titulo_seccion || "Capítulo";

        // Caso A: Lista de contenidos
        if (capitulo.contenido && Array.isArray(capitulo.contenido)) {
            capitulo.contenido.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = "p-4 bg-gray-50 rounded-lg border border-gray-100 hover:border-blue-200 transition-colors";
                
                let html = `<h4 class="font-bold text-gray-800 text-base mb-1">${item.texto || ""}</h4>`;

                const notes = [];
                if (item.instruccion_detallada) notes.push(item.instruccion_detallada);
                if (item.nota) notes.push(item.nota);
                if (item.tabla_nota) notes.push(item.tabla_nota);
                if (Array.isArray(item.imagenes)) {
                    item.imagenes.forEach((img) => {
                        if (img && img.fuente) notes.push(img.fuente);
                    });
                }

                notes.forEach((note) => {
                    const noteText = shortGuide(note);
                    html += `
                        <div class="flex gap-2 mt-2">
                            <span class="text-blue-500 mt-0.5"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></span>
                            <p class="text-gray-600 text-sm italic">${noteText}</p>
                        </div>
                    `;
                });
                itemDiv.innerHTML = html;
                listContainer.appendChild(itemDiv);
            });
        } 
        // Caso B: Texto simple (Conclusiones, etc)
        else if (capitulo.nota_capitulo || capitulo.nota) {
            const texto = capitulo.nota_capitulo || capitulo.nota;
            const itemDiv = document.createElement('div');
            itemDiv.className = "p-6 bg-blue-50 rounded-lg border border-blue-100 text-center";
            itemDiv.innerHTML = `
                <p class="text-gray-800 text-lg font-medium italic">"${texto}"</p>
            `;
            listContainer.appendChild(itemDiv);
        }

        loader.classList.add('hidden');
        content.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        alert("Información: " + error.message);
        closeChapterModal();
    }
}

// ESTA ES LA FUNCIÓN QUE FALTABA O FALLABA
function closeChapterModal() {
    document.getElementById('chapterModal').classList.add('hidden');
}

/**
 * Genera dinámicamente la lista de requisitos desde el JSON
 */
async function hydrateRequirementsList() {
    const container = document.getElementById('formatRequirements');
    if (!container) return;
    
    const formatId = container.dataset.formatId;
    if (!formatId) return;

    try {
        // 1. Obtener datos del JSON
        const data = await fetchFormatJson(formatId);
        
        // 2. Limpiar contenedor
        container.innerHTML = '';
        
        // 3. Siempre agregar Carátula e Índice
        container.appendChild(buildRequirementItem(
            "Carátula Institucional",
            "Debe seguir estrictamente el modelo oficial.",
            () => previewCover(formatId)
        ));
        
        container.appendChild(buildRequirementItem(
            "Índice General",
            "Generado automáticamente por Word con estilos aplicados.",
            () => previewIndex(formatId)
        ));
        
        // 4. Agregar capítulos del cuerpo
        if (data.cuerpo && Array.isArray(data.cuerpo)) {
            data.cuerpo.forEach((capitulo) => {
                if (!capitulo.titulo) return;
                
                // Extraer número romano del título (I., II., III., etc.)
                const match = capitulo.titulo.match(/^([IVXLCDM]+)\./);
                const prefijo = match ? match[1] + '.' : '';
                
                // Obtener descripción del capítulo
                let descripcion = "Estructura principal del capítulo.";
                
                if (capitulo.nota_capitulo) {
                    descripcion = capitulo.nota_capitulo;
                } else if (capitulo.contenido && Array.isArray(capitulo.contenido) && capitulo.contenido.length > 0) {
                    // Intentar obtener la primera nota disponible
                    const primerContenido = capitulo.contenido[0];
                    if (primerContenido.instruccion_detallada) {
                        descripcion = primerContenido.instruccion_detallada;
                    } else if (primerContenido.nota) {
                        descripcion = primerContenido.nota;
                    } else if (primerContenido.tabla_nota) {
                        descripcion = primerContenido.tabla_nota;
                    } else if (Array.isArray(primerContenido.imagenes)) {
                        const fuente = primerContenido.imagenes.find(img => img && img.fuente)?.fuente;
                        if (fuente) {
                            descripcion = fuente;
                        }
                    } else if (primerContenido.texto) {
                        descripcion = primerContenido.texto;
                    }
                }
                // Truncar descripción si es muy larga
                if (descripcion.length > 100) {
                    descripcion = descripcion.substring(0, 97) + '...';
                }
                
                container.appendChild(buildRequirementItem(
                    capitulo.titulo,
                    descripcion,
                    () => previewChapter(formatId, prefijo || capitulo.titulo)
                ));
            });
        }
        
        // 5. Agregar Referencias (buscar en finales o en cuerpo)
        let referenciasTitulo = null;
        let referenciasDescripcion = null;
        let referenciasPrefijo = null;
        
        // Opción A: Buscar en data.finales.referencias
        if (data.finales?.referencias?.titulo) {
            referenciasTitulo = data.finales.referencias.titulo;
            referenciasDescripcion = data.finales.referencias.nota || "Normativa bibliográfica según corresponda.";
            referenciasPrefijo = "REFERENCIAS"; // Palabra clave para búsqueda
        } 
        // Opción B: Buscar en el cuerpo (por si está como capítulo)
        else if (data.cuerpo && Array.isArray(data.cuerpo)) {
            const capituloReferencias = data.cuerpo.find(cap => 
                cap.titulo && (
                    cap.titulo.toUpperCase().includes('REFERENCIAS') ||
                    cap.titulo.toUpperCase().includes('BIBLIOGRAF')
                )
            );
            
            if (capituloReferencias) {
                referenciasTitulo = capituloReferencias.titulo;
                referenciasDescripcion = capituloReferencias.nota_capitulo || capituloReferencias.nota || "Normativa bibliográfica según corresponda.";
                const match = capituloReferencias.titulo.match(/^([IVXLCDM]+)\./);
                referenciasPrefijo = match ? match[1] + '.' : 'REFERENCIAS';
            }
        }
        
        // Agregar la tarjeta de Referencias si se encontró
        if (referenciasTitulo) {
            container.appendChild(buildRequirementItem(
                referenciasTitulo,
                referenciasDescripcion,
                () => previewChapter(formatId, referenciasPrefijo)
            ));
        }
        
        // 6. Agregar Anexos (si existen)
        if (data.finales?.anexos) {
            const anexos = data.finales.anexos;
            const anexosTitulo = anexos.titulo_seccion || "Anexos";
            const anexosDescripcion = anexos.nota_general || anexos.nota || "Documentación complementaria.";
            
            container.appendChild(buildRequirementItem(
                anexosTitulo,
                anexosDescripcion,
                null // Sin preview por ahora, o puedes crear una función previewAnexos
            ));
        }
        
        // 7. Reinicializar iconos de Lucide
        if (window.lucide) {
            window.lucide.createIcons();
        }
        
    } catch (error) {
        console.error("Error cargando requisitos:", error);
        container.innerHTML = `
            <div class="p-6 bg-red-50 text-red-700 rounded-lg border border-red-200">
                <p class="font-semibold">Error cargando estructura del formato</p>
                <p class="text-sm mt-1">${error.message}</p>
            </div>
        `;
    }
}
/**
 * Construye un elemento de requisito individual
 */
function buildRequirementItem(title, description, onPreview) {
    const wrapper = document.createElement('div');
    wrapper.className = "flex items-start gap-4 p-4 rounded-lg bg-gray-50 border border-gray-200 group hover:border-blue-300 transition-colors";
    
    // Contenido
    const body = document.createElement('div');
    body.className = "flex-1";
    
    const header = document.createElement('div');
    header.className = "flex items-center justify-between";
    
    const h4 = document.createElement('h4');
    h4.className = "font-semibold text-gray-900";
    h4.textContent = title;
    header.appendChild(h4);
    
    // Botón de preview (si existe callback)
    if (onPreview) {
        const btn = document.createElement('button');
        btn.className = "text-gray-400 hover:text-blue-600 transition-colors p-1 rounded-md hover:bg-blue-50";
        btn.title = "Ver detalle";
        btn.innerHTML = '<i data-lucide="eye" class="w-5 h-5"></i>';
        btn.addEventListener('click', onPreview);
        header.appendChild(btn);
    }
    
    body.appendChild(header);
    
    // Descripción
    if (description) {
        const p = document.createElement('p');
        p.className = "text-sm text-gray-600 mt-1";
        p.textContent = description;
        body.appendChild(p);
    }
    
    wrapper.appendChild(body);
    return wrapper;
}

// Ejecutar al cargar la página
document.addEventListener('DOMContentLoaded', hydrateRequirementsList);



```

---

## app/static/js/navigation.js
**Tama?o:** 582
**SHA256:** 243a58578a2eba31e627b5765ded42d42b99ed824ffafa7043b73b01fd0f6bc3
**Tipo:** js

```javascript
// Activa el item del sidebar según `active_nav` inyectado por el backend (Jinja)
// En este scaffold, se marca con un atributo data-nav, y el backend pasa `active_nav`.

(function() {
  const active = (window.__ACTIVE_NAV__ || "").toString();
  const items = document.querySelectorAll("[data-nav]");
  items.forEach(el => {
    const key = el.getAttribute("data-nav");
    if (key === active) {
      el.classList.add("bg-blue-50", "text-blue-700");
    } else {
      el.classList.add("text-gray-600", "hover:bg-gray-50", "hover:text-gray-900");
    }
  });
})();

```

---

## app/templates/base.html
**Tama?o:** 1160
**SHA256:** 2173fde99d02681387f93bb8e0598dcb0ee19d9b128e263e6f6f24230edb02ba
**Tipo:** html

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{{ title or "Formatoteca" }}</title>

  <!-- Tailwind CDN (cascarón) -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>

  <link rel="stylesheet" href="/static/css/extra.css">
  <link rel="icon" type="image/png" href="/static/assets/LogoUNAC.png">
</head>

<body class="flex h-screen overflow-hidden text-gray-800 bg-gray-50/50">

  {% include "components/sidebar.html" %}

  <main class="flex-1 flex flex-col min-w-0 bg-gray-50/50">
    {% include "components/header.html" %}

    <div id="main-content" class="flex-1 overflow-auto p-8 relative scroll-smooth">
      <div class="fade-in">
        {% block content %}{% endblock %}
      </div>
      <div class="h-12"></div>
    </div>
  </main>

  <script>window.__ACTIVE_NAV__ = "{{ active_nav or "" }}";</script>
  <script src="/static/js/navigation.js"></script>
  <script>
    lucide.createIcons();
  </script>
</body>
</html>

```

---

## app/templates/components/header.html
**Tama?o:** 949
**SHA256:** 9c97080373b8bf0ea63b8bf11de513957c6747812141457c0c0b51c317768dd8
**Tipo:** html

```html
<header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8 shadow-sm z-10">
  <div class="flex items-center gap-2 text-sm text-gray-500">
    <span class="font-medium text-gray-900">Formatoteca</span>
    <i data-lucide="chevron-right" class="w-4 h-4"></i>
    <span>{{ breadcrumb or "Inicio" }}</span>
  </div>

  <div class="flex items-center gap-4">
    <div class="relative w-96 hidden md:block">
      <i data-lucide="search" class="absolute left-3 top-2.5 w-4 h-4 text-gray-400"></i>
      <input type="text"
             placeholder="Buscar formato, tesis, facultad..."
             class="w-full bg-gray-100 border-none rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all">
    </div>
    <button class="p-2 text-gray-500 hover:bg-gray-100 rounded-lg">
      <i data-lucide="help-circle" class="w-5 h-5"></i>
    </button>
  </div>
</header>

```

---

## app/templates/components/sidebar.html
**Tama?o:** 2459
**SHA256:** 829bd5c976b5b6cceedd7fee1d20f9df8f04f0cdad7ed73e8db99a1031bfb613
**Tipo:** html

```html
<aside class="w-64 bg-white border-r border-gray-200 flex flex-col z-20 shadow-sm">
  <!-- Logo -->
  <div class="h-16 flex items-center px-6 border-b border-gray-100">
    <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white mr-3">
      <i data-lucide="library" class="w-5 h-5"></i>
    </div>
    <span class="font-bold text-lg tracking-tight text-gray-900">Formatoteca</span>
  </div>

  <!-- Menu -->
  <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
    <p class="px-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Principal</p>

    <a href="/" class="nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
       data-nav="home">
      <i data-lucide="home" class="w-5 h-5"></i>
      Inicio
    </a>

    <a href="/catalog" class="nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
       data-nav="catalog">
      <i data-lucide="grid" class="w-5 h-5"></i>
      Catálogo
    </a>

    <a href="/alerts" class="nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
       data-nav="alerts">
      <div class="relative">
        <i data-lucide="bell" class="w-5 h-5"></i>
        <span class="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
      </div>
      Notificaciones
    </a>

    <p class="px-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mt-6 mb-2">Admin</p>

    <a href="/admin" class="nav-item w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
       data-nav="admin">
      <i data-lucide="settings" class="w-5 h-5"></i>
      Panel
    </a>
  </nav>

  <!-- Perfil -->
  <div class="p-4 border-t border-gray-100">
    <button class="flex items-center gap-3 w-full p-2 hover:bg-gray-50 rounded-lg transition-colors">
      <div class="w-9 h-9 bg-gray-200 rounded-full flex items-center justify-center overflow-hidden">
        <i data-lucide="user" class="w-5 h-5 text-gray-500"></i>
      </div>
      <div class="text-left">
        <p class="text-sm font-medium text-gray-900">Admin User</p>
        <p class="text-xs text-gray-500">admin@demo.pe</p>
      </div>
      <i data-lucide="chevron-up" class="w-4 h-4 text-gray-400 ml-auto"></i>
    </button>
  </div>
</aside>

```

---

## app/templates/pages/admin.html
**Tama?o:** 1669
**SHA256:** aca49009659a4e7e0a2dd33ae8735af47fe8a42e1585a27176de55b93e22165d
**Tipo:** html

```html
{% extends "base.html" %}
{% block content %}
<div class="max-w-4xl mx-auto">

  <h1 class="text-2xl font-bold text-gray-900 mb-2">Panel Admin (cascarón)</h1>
  <p class="text-gray-500 mb-6">Aquí luego irá el CRUD (crear/editar) formatos, alertas, fuentes, etc.</p>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div class="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
      <h2 class="font-bold text-gray-900 mb-2">Formato</h2>
      <p class="text-sm text-gray-600 mb-4">Formulario placeholder.</p>
      <div class="space-y-3">
        <input class="w-full bg-gray-100 rounded-lg px-3 py-2 text-sm" placeholder="Título del formato">
        <input class="w-full bg-gray-100 rounded-lg px-3 py-2 text-sm" placeholder="Universidad (UNAC/UNI)">
        <button class="w-full bg-gray-900 text-white rounded-lg py-2 text-sm font-medium hover:bg-gray-800">
          Guardar (placeholder)
        </button>
      </div>
    </div>

    <div class="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
      <h2 class="font-bold text-gray-900 mb-2">Alertas</h2>
      <p class="text-sm text-gray-600 mb-4">Formulario placeholder.</p>
      <div class="space-y-3">
        <input class="w-full bg-gray-100 rounded-lg px-3 py-2 text-sm" placeholder="Título de alerta">
        <textarea class="w-full bg-gray-100 rounded-lg px-3 py-2 text-sm" rows="3" placeholder="Mensaje"></textarea>
        <button class="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700">
          Publicar (placeholder)
        </button>
      </div>
    </div>
  </div>

</div>
{% endblock %}

```

---

## app/templates/pages/alerts.html
**Tama?o:** 1641
**SHA256:** 0aa5db1b4c3a662b1212316e1c6b29ac3dff533d73c08d124ff29dcdce7f81cd
**Tipo:** html

```html
{% extends "base.html" %}
{% block content %}
<div class="max-w-3xl mx-auto">

  <div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold text-gray-900">Centro de Notificaciones</h1>
    <button class="text-sm text-blue-600 font-medium hover:text-blue-800">Marcar todo como leído (placeholder)</button>
  </div>

  <div class="bg-white rounded-xl shadow-sm border border-gray-200 divide-y divide-gray-100">
    {% for n in alerts %}
    <div class="p-6 flex gap-4 hover:bg-gray-50 transition-colors relative">
      <div class="absolute left-0 top-0 bottom-0 w-1 {% if n.nivel == 'IMPORTANTE' %}bg-blue-500{% else %}bg-gray-200{% endif %} rounded-l-xl"></div>

      <div class="w-12 h-12 rounded-full {% if n.nivel == 'IMPORTANTE' %}bg-blue-100 text-blue-600{% else %}bg-yellow-100 text-yellow-600{% endif %} flex items-center justify-center flex-shrink-0">
        <i data-lucide="{% if n.nivel == 'IMPORTANTE' %}file-warning{% else %}alert-triangle{% endif %}" class="w-6 h-6"></i>
      </div>

      <div class="flex-1">
        <div class="flex justify-between mb-1">
          <h4 class="font-bold text-gray-900">{{ n.titulo }}</h4>
          <span class="text-xs text-gray-500">{{ n.cuando }}</span>
        </div>
        <p class="text-gray-600 text-sm leading-relaxed mb-2">{{ n.cuerpo }}</p>

        {% if n.relacionado_id %}
        <a href="/formatos/{{ n.relacionado_id }}" class="text-sm font-medium text-blue-600 hover:text-blue-800">Ver documento relacionado</a>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>

</div>
{% endblock %}

```

---

## app/templates/pages/catalog.html
**Tama?o:** 11840
**SHA256:** 38e5274e74b3572370d7237fc507c46047d13e215e93d656b7587a548f57a44e
**Tipo:** html

```html
{% extends "base.html" %}

{% block content %}
<div class="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

  <div class="mb-10">
    <div class="flex items-center gap-2 mb-6">
      <svg class="w-8 h-8 text-yellow-500 fill-current" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
      <h1 class="text-3xl font-bold text-gray-900">Accesos Rápidos</h1>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      <div id="quick-caratulas"
           onclick="iniciarFlujo('caratula', 'quick-caratulas')" 
           class="quick-card group bg-white p-6 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all cursor-pointer h-full">
        <div class="w-14 h-14 bg-orange-50 rounded-2xl flex items-center justify-center mb-5 group-hover:bg-orange-100 transition-colors">
          <i data-lucide="layout-template" class="w-7 h-7 text-orange-600"></i>
        </div>
        <h3 class="font-bold text-gray-900 text-xl mb-2">Carátulas</h3>
        <p class="text-sm text-gray-500 leading-relaxed">Modo visual: Explora las portadas oficiales.</p>
      </div>

      <div id="quick-referencias"
           onclick="iniciarFlujo('referencias', 'quick-referencias')" 
           class="quick-card group bg-white p-6 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all cursor-pointer h-full">
        <div class="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center mb-5 group-hover:bg-indigo-100 transition-colors">
          <i data-lucide="book-open-check" class="w-7 h-7 text-indigo-600"></i>
        </div>
        <h3 class="font-bold text-gray-900 text-xl mb-2">Referencias Bibliográficas</h3>
        <p class="text-sm text-gray-500 leading-relaxed">Modo consulta: Normativas de citación.</p>
      </div>

      <div id="quick-todos"
           onclick="iniciarFlujo('normal', 'quick-todos')" 
           class="quick-card group bg-white p-6 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all cursor-pointer h-full">
        <div class="w-14 h-14 bg-green-50 rounded-2xl flex items-center justify-center mb-5 group-hover:bg-green-100 transition-colors">
          <i data-lucide="layers" class="w-7 h-7 text-green-600"></i>
        </div>
        <h3 class="font-bold text-gray-900 text-xl mb-2">Ver Todo</h3>
        <p class="text-sm text-gray-500 leading-relaxed">Modo estándar: Estructura completa y descargas.</p>
      </div>

    </div>
  </div>

  <div id="bloque-categorias" class="hidden transition-all duration-500 ease-in-out opacity-0 translate-y-4 mb-8">
    <div class="flex items-center gap-2 mb-6 border-t border-gray-200 pt-8">
      <i data-lucide="filter" class="w-5 h-5 text-gray-400"></i>
      <h2 class="text-xl font-bold text-gray-800" id="titulo-paso-2">Selecciona qué documentos ver</h2>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      
      <div id="cat-todos" onclick="seleccionarCategoriaFinal('todos', 'cat-todos')" 
           class="cat-card bg-white p-4 rounded-xl border border-gray-200 hover:border-gray-400 hover:shadow-md transition-all cursor-pointer flex flex-col items-center text-center gap-3">
        <div class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600">
          <i data-lucide="grid" class="w-5 h-5"></i>
        </div>
        <div>
          <h3 class="font-bold text-gray-900 text-sm">Todos</h3>
          <p class="text-[10px] text-gray-500">Todo el catálogo</p>
        </div>
      </div>

      <div id="cat-tesis" onclick="seleccionarCategoriaFinal('Tesis', 'cat-tesis')" 
           class="cat-card bg-white p-4 rounded-xl border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer flex flex-col items-center text-center gap-3">
        <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600">
          <i data-lucide="folder-kanban" class="w-5 h-5"></i>
        </div>
        <div>
          <h3 class="font-bold text-gray-900 text-sm">Proyectos</h3>
          <p class="text-[10px] text-gray-500">Anteproyectos</p>
        </div>
      </div>

      <div id="cat-info" onclick="seleccionarCategoriaFinal('Inv. Formativa', 'cat-info')" 
           class="cat-card bg-white p-4 rounded-xl border border-gray-200 hover:border-purple-400 hover:shadow-md transition-all cursor-pointer flex flex-col items-center text-center gap-3">
        <div class="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center text-purple-600">
          <i data-lucide="file-text" class="w-5 h-5"></i>
        </div>
        <div>
          <h3 class="font-bold text-gray-900 text-sm">Informes</h3>
          <p class="text-[10px] text-gray-500">Sustentación</p>
        </div>
      </div>

      <div id="cat-maestria" onclick="seleccionarCategoriaFinal('Suficiencia', 'cat-maestria')" 
           class="cat-card bg-white p-4 rounded-xl border border-gray-200 hover:border-orange-400 hover:shadow-md transition-all cursor-pointer flex flex-col items-center text-center gap-3">
        <div class="w-10 h-10 bg-orange-50 rounded-lg flex items-center justify-center text-orange-600">
          <i data-lucide="graduation-cap" class="w-5 h-5"></i>
        </div>
        <div>
          <h3 class="font-bold text-gray-900 text-sm">Posgrado</h3>
          <p class="text-[10px] text-gray-500">Maestría/Doc.</p>
        </div>
      </div>

    </div>
  </div>

  <div id="bloque-resultados" class="hidden transition-all duration-500 ease-in-out opacity-0 translate-y-4">
    
    <div class="mb-6 mt-8 border-t border-gray-100 pt-6">
        <h2 class="text-lg font-bold text-gray-900 flex items-center gap-2">
            <span class="w-2 h-6 bg-blue-600 rounded-full"></span>
            Formatos Disponibles
        </h2>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="formatos-grid">
      {% for f in formatos %}
      <a href="/formatos/{{ f.id }}" 
         onclick="return handleCardClick(event, '{{ f.id }}')"
         class="formato-card group bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-lg hover:border-blue-300 transition-all cursor-pointer flex flex-col h-full overflow-hidden relative" 
         data-tipo="{{ f.tipo }}">
        
        <div class="hidden mode-badge absolute top-3 right-3 z-10 text-[10px] font-bold px-2 py-1 rounded shadow-sm border flex items-center gap-1"></div>

        <div class="p-6 flex-1 flex flex-col">
          <div class="flex justify-between items-start gap-3 mb-4 original-badges transition-opacity duration-300">
            <span class="inline-block text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider
              {% if f.uni == 'UNAC' %} bg-blue-50 text-blue-700 border border-blue-100 {% else %} bg-red-50 text-red-700 {% endif %}">
              {{ f.uni }}
            </span>
            <span class="flex items-center gap-1.5 text-[10px] font-bold px-2.5 py-1 rounded-full border
              {% if f.estado == 'VIGENTE' %} bg-green-50 text-green-700 border-green-100 {% else %} bg-orange-50 text-orange-700 border-orange-100 {% endif %}">
              <span class="w-1.5 h-1.5 rounded-full {% if f.estado == 'VIGENTE' %} bg-green-500 {% else %} bg-orange-500 {% endif %}"></span>
              {{ f.estado }}
            </span>
          </div>

          <h3 class="font-bold text-lg text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">{{ f.titulo }}</h3>
          <p class="text-sm text-gray-500 line-clamp-2">{{ f.facultad }}</p>
        </div>

        <div class="px-6 py-4 border-t border-gray-50 bg-gray-50/30 flex items-center justify-between mt-auto">
          <span class="text-xs text-gray-400 font-medium flex items-center gap-1.5">
            <i data-lucide="clock" class="w-3.5 h-3.5"></i> v{{ f.version }}
          </span>
          <span class="action-text text-blue-600 text-sm font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
            Ver Estructura <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </span>
        </div>
      </a>
      {% endfor %}
    </div>
  </div>

</div>

<div id="coverModal" class="fixed inset-0 z-50 hidden" role="dialog" aria-modal="true"><div class="fixed inset-0 bg-gray-900/80 backdrop-blur-sm" onclick="closeModal('coverModal')"></div><div class="fixed inset-0 z-10 overflow-y-auto"><div class="flex min-h-full items-center justify-center p-4"><div class="relative bg-white shadow-2xl sm:max-w-3xl w-full flex flex-col rounded-sm" style="aspect-ratio: 210/297; max-height: 90vh;"><button onclick="closeModal('coverModal')" class="absolute top-4 right-4 text-gray-400 hover:text-red-500 z-20 bg-white rounded-full p-2 shadow-md"><i data-lucide="x" class="w-5 h-5"></i></button><div id="coverLoader" class="absolute inset-0 flex items-center justify-center bg-white z-10"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div></div><div id="coverContent" class="hidden flex-1 flex flex-col items-center text-center px-16 py-12 font-serif text-gray-900 h-full overflow-y-auto border-2 border-gray-100 m-2"><h2 id="c-uni" class="text-xl font-bold uppercase mb-2"></h2><h3 id="c-fac" class="text-lg font-bold uppercase mb-2"></h3><h3 id="c-esc" class="text-lg font-bold uppercase mb-8"></h3><div class="mb-8"><img src="/static/assets/LogoUNAC.png" class="h-28 w-auto object-contain mx-auto opacity-90"></div><div class="w-full flex-1 flex flex-col justify-center my-4"><h2 id="c-titulo" class="text-xl font-bold uppercase leading-snug"></h2><p class="text-sm italic mt-2 text-gray-500">(Título del proyecto)</p><p id="c-guia" class="mt-3 text-xs italic text-gray-500 whitespace-pre-line hidden"></p></div><div class="mb-8 w-full"><p id="c-frase" class="text-base mb-1"></p><h3 id="c-grado" class="text-lg font-bold uppercase"></h3></div><div class="mb-12 w-full text-center space-y-2"><p class="text-sm font-bold">PRESENTADO POR:</p><p class="text-base uppercase text-gray-400">[Nombres]</p><p class="text-sm font-bold mt-4">ASESOR:</p><p class="text-base uppercase text-gray-400">[Grado y Nombre]</p></div><div class="mt-auto"><p id="c-lugar" class="text-base font-bold uppercase">CALLAO, PERÚ</p><p id="c-anio" class="text-base font-bold">2026</p></div></div></div></div></div></div>
<div id="refModal" class="fixed inset-0 z-50 hidden" role="dialog" aria-modal="true"><div class="fixed inset-0 bg-gray-900/80 backdrop-blur-sm" onclick="closeModal('refModal')"></div><div class="fixed inset-0 z-10 overflow-y-auto"><div class="flex min-h-full items-center justify-center p-4"><div class="relative bg-white shadow-2xl rounded-xl sm:max-w-2xl w-full flex flex-col max-h-[85vh]"><div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50 rounded-t-xl"><h3 class="text-lg font-bold text-gray-900 flex items-center gap-2"><i data-lucide="book-open-check" class="w-5 h-5 text-indigo-600"></i> Referencias Bibliográficas</h3><button onclick="closeModal('refModal')" class="text-gray-400 hover:text-gray-600 p-1"><i data-lucide="x" class="w-5 h-5"></i></button></div><div id="refLoader" class="flex-1 flex items-center justify-center py-12"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div><div id="refContent" class="hidden p-6 overflow-y-auto font-serif"><div id="refList" class="space-y-4 text-gray-700 text-sm leading-relaxed text-justify"></div></div></div></div></div>

<script src="/static/js/catalog.js?v=7"></script>
{% endblock %}

```

---

## app/templates/pages/detail.html
**Tama?o:** 14301
**SHA256:** e48137c0aee5ad98699a69a1ad844d063b5e6b200efd809b6f73006bc7b3c8f0
**Tipo:** html

```html
{% extends "base.html" %}
{% block content %}
<div class="max-w-6xl mx-auto">

  <a href="/catalog"
    class="mb-6 flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
    <i data-lucide="arrow-left" class="w-4 h-4 mr-1"></i> Volver al catálogo
  </a>

  <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">

    <div class="lg:col-span-3 space-y-6">

      <div class="bg-white rounded-lg border border-gray-200 p-8 shadow-sm">
        <div class="flex items-center gap-2 mb-6">
          <span class="bg-blue-100 text-blue-700 text-xs font-bold px-3 py-1 rounded-full uppercase">{{ formato.uni
            }}</span>
          <span class="text-gray-400 text-sm">•</span>
          <span class="text-gray-600 text-sm">{{ formato.facultad }}{% if formato.escuela %} / {{ formato.escuela }}{%
            endif %}</span>
        </div>

        <h1 class="text-4xl font-bold text-gray-900 mb-4 leading-tight">{{ formato.titulo }}</h1>

        <p class="text-gray-700 mb-8 text-base leading-relaxed">{{ formato.resumen }}</p>

        <div class="flex flex-wrap gap-3">
          <button id="download-btn"
            class="flex items-center justify-center gap-2 bg-gray-900 text-white px-6 py-3 rounded-lg font-semibold shadow hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onclick="downloadDocument('{{ formato.id }}')">
            <i data-lucide="download" class="w-4 h-4"></i>
            <span id="download-text">Descargar DOCX</span>
          </button>

          <button onclick="openPdfModal('{{ formato.id }}')"
            class="flex items-center justify-center gap-2 bg-white text-gray-700 border border-gray-300 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 transition-colors cursor-pointer">
            <i data-lucide="eye" class="w-4 h-4"></i>
            Vista Previa PDF
          </button>

          <button
            class="p-3 text-gray-400 hover:text-blue-600 border border-transparent hover:bg-blue-50 rounded-lg transition-colors ml-auto"
            title="Compartir">
            <i data-lucide="share-2" class="w-5 h-5"></i>
          </button>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div class="border-b border-gray-200 px-8 py-4 flex gap-8">
          <button
            class="text-sm font-semibold text-blue-600 border-b-2 border-blue-600 pb-4 -mb-4 hover:text-blue-700 transition-colors">
            Requisitos del Formato
          </button>
          <button class="text-sm font-medium text-gray-600 hover:text-gray-900 pb-4 -mb-4 transition-colors">
            Comentarios
          </button>
        </div>

        <div class="p-8 space-y-4" id="formatRequirements" data-format-id="{{ formato.id }}">
          <!-- Se llenará dinámicamente con JavaScript -->
          <div class="flex items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="space-y-6">
      <div class="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 class="font-bold text-gray-900 mb-4 text-lg">Información</h3>
        <div class="space-y-4 text-sm">
          <div class="flex justify-between items-start py-3 border-b border-gray-200">
            <span class="text-gray-600 font-medium">Última actualización</span>
            <span class="text-gray-900 font-semibold">{{ formato.fecha }}</span>
          </div>
          <div class="flex justify-between items-start py-3 border-b border-gray-200">
            <span class="text-gray-600 font-medium">Versión Actual</span>
            <span class="text-gray-900 font-semibold">{{ formato.version }}</span>
          </div>
          <div class="flex justify-between items-start py-3 border-b border-gray-200">
            <span class="text-gray-600 font-medium">Formato</span>
            <span class="text-gray-900 font-semibold">Word (.docx)</span>
          </div>
          <div class="flex justify-between items-start py-3">
            <span class="text-gray-600 font-medium">Tamaño</span>
            <span class="text-gray-900 font-semibold">35.8 KB</span>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-900 text-lg">Historial</h3>
          <a href="/formatos/{{ formato.id }}/versions" class="text-xs font-bold text-blue-600 hover:underline">Ver
            todo</a>
        </div>

        <div class="space-y-3">
          <div class="flex gap-3 pb-3 border-b border-gray-200">
            <div class="flex-shrink-0 mt-0.5">
              <span class="inline-flex items-center justify-center w-2 h-2 rounded-full bg-green-500"></span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-baseline gap-2">
                <p class="text-sm font-bold text-gray-900">v{{ formato.version }}</p>
                <span class="text-xs font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">VIGENTE</span>
              </div>
              <p class="text-xs text-gray-600 mt-1">Versión actual del formato</p>
              <p class="text-xs text-gray-500 mt-1">{{ formato.fecha }}</p>
            </div>
          </div>
        </div>

        <a href="/formatos/{{ formato.id }}/versions"
          class="w-full mt-4 py-2.5 text-sm font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors flex items-center justify-center gap-2">
          <i data-lucide="git-compare" class="w-4 h-4"></i> Comparar Versiones
        </a>
      </div>
    </div>
  </div>
</div>

<div id="pdfModal" class="fixed inset-0 z-50 hidden" aria-labelledby="modal-title" role="dialog" aria-modal="true">
  <div class="fixed inset-0 bg-gray-900/90 transition-opacity backdrop-blur-md" onclick="closePdfModal()"></div>
  <div class="fixed inset-0 z-10 overflow-hidden">
    <div class="flex min-h-full items-center justify-center p-2 sm:p-4 text-center">
      <div
        class="relative transform overflow-hidden rounded-2xl bg-gray-900 text-left shadow-2xl transition-all sm:w-full sm:max-w-7xl h-[90vh] flex flex-col border border-gray-800">
        <div class="bg-gray-900 px-6 py-4 flex justify-between items-center border-b border-gray-800">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-gray-800 rounded-lg">
              <i data-lucide="file-text" class="w-5 h-5 text-blue-400"></i>
            </div>
            <div>
              <h3 class="text-lg font-semibold leading-6 text-white tracking-wide" id="modal-title">Vista de Lectura
              </h3>
              <p class="text-xs text-gray-400">Documento Oficial UNAC</p>
            </div>
          </div>
          <button type="button" onclick="closePdfModal()"
            class="rounded-lg p-2 text-gray-400 hover:text-white hover:bg-gray-800 transition-all focus:outline-none">
            <span class="sr-only">Cerrar</span>
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
              aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="flex-1 bg-gray-900 p-0 relative group">
          <iframe id="pdfViewer" src="" class="w-full h-full border-none bg-gray-900" allowfullscreen></iframe>
        </div>
      </div>
    </div>
  </div>
</div>

<div id="coverModal" class="fixed inset-0 z-50 hidden" aria-labelledby="modal-title" role="dialog" aria-modal="true">
  <div class="fixed inset-0 bg-gray-900/80 transition-opacity backdrop-blur-sm" onclick="closeCoverModal()"></div>
  <div class="fixed inset-0 z-10 overflow-y-auto">
    <div class="flex min-h-full items-center justify-center p-4">
      <div class="relative bg-white shadow-2xl transform transition-all sm:max-w-3xl w-full flex flex-col"
        style="aspect-ratio: 210/297; max-height: 90vh;">
        <button type="button" onclick="closeCoverModal()"
          class="absolute top-4 right-4 text-gray-400 hover:text-red-500 z-20">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <div id="coverLoader" class="absolute inset-0 flex items-center justify-center bg-white z-10">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
        <div id="coverContent"
          class="hidden flex-1 flex flex-col items-center text-center px-16 py-12 font-serif text-gray-900 h-full overflow-y-auto">
          <h2 id="c-uni" class="text-xl font-bold uppercase mb-2 leading-tight"></h2>
          <h3 id="c-fac" class="text-lg font-bold uppercase mb-2 leading-tight"></h3>
          <h3 id="c-esc" class="text-lg font-bold uppercase mb-8 leading-tight"></h3>
          <div class="mb-8">
            <img src="/static/assets/LogoUNAC.png" alt="Logo" class="h-32 w-auto object-contain mx-auto opacity-90">
          </div>
          <div class="w-full flex-1 flex flex-col justify-center my-4">
            <h2 id="c-titulo" class="text-xl font-bold uppercase leading-snug"></h2>
            <p class="text-sm italic mt-2 text-gray-500">(Título provisional)</p>
            <p id="c-guia" class="mt-3 text-xs italic text-gray-500 whitespace-pre-line hidden"></p>
          </div>
          <div class="mb-8 w-full">
            <p id="c-frase" class="text-base mb-1"></p>
            <h3 id="c-grado" class="text-lg font-bold uppercase"></h3>
          </div>
          <div class="mb-12 w-full text-center space-y-2">
            <p class="text-sm font-bold">PRESENTADO POR:</p>
            <p class="text-base uppercase">[Nombres y Apellidos]</p>
            <p class="text-sm font-bold mt-4">ASESOR:</p>
            <p class="text-base uppercase">[Grado y Nombre del Asesor]</p>
          </div>
          <div class="mt-auto">
            <p id="c-lugar" class="text-base font-bold uppercase">CALLAO, PERÚ</p>
            <p id="c-anio" class="text-base font-bold">2026</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div id="indexModal" class="fixed inset-0 z-50 hidden" aria-labelledby="modal-title" role="dialog" aria-modal="true">
  <div class="fixed inset-0 bg-gray-900/80 transition-opacity backdrop-blur-sm" onclick="closeIndexModal()"></div>
  <div class="fixed inset-0 z-10 overflow-y-auto">
    <div class="flex min-h-full items-center justify-center p-4">
      <div class="relative bg-white shadow-2xl transform transition-all sm:max-w-3xl w-full flex flex-col"
        style="aspect-ratio: 210/297; max-height: 90vh;">
        <button type="button" onclick="closeIndexModal()"
          class="absolute top-4 right-4 text-gray-400 hover:text-red-500 z-20">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <div id="indexLoader" class="absolute inset-0 flex items-center justify-center bg-white z-10">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
        <div id="indexContent"
          class="hidden flex-1 flex flex-col px-16 py-12 font-serif text-gray-900 h-full overflow-hidden">
          <h2 class="text-xl font-bold uppercase mb-8 text-center">ÍNDICE GENERAL</h2>
          <div id="indexList" class="flex-1 overflow-y-auto pr-2 space-y-3 text-sm leading-relaxed">
          </div>
          <div class="mt-auto pt-4 border-t border-gray-100 text-center text-xs text-gray-400">
            Estructura referencial basada en normativa UNAC
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div id="chapterModal" class="fixed inset-0 z-50 hidden" aria-labelledby="modal-title" role="dialog" aria-modal="true">
  <div class="fixed inset-0 bg-gray-900/80 transition-opacity backdrop-blur-sm" onclick="closeChapterModal()"></div>
  <div class="fixed inset-0 z-10 overflow-y-auto">
    <div class="flex min-h-full items-center justify-center p-4">
      <div class="relative bg-white shadow-2xl transform transition-all sm:max-w-3xl w-full flex flex-col rounded-xl"
        style="max-height: 85vh;">

        <button type="button" onclick="closeChapterModal()"
          class="absolute top-4 right-4 text-gray-400 hover:text-red-500 z-20">
          <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div id="chapterLoader" class="absolute inset-0 flex items-center justify-center bg-white z-10 rounded-xl">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>

        <div id="chapterContent"
          class="hidden flex-1 flex flex-col px-10 py-8 font-serif text-gray-900 h-full overflow-hidden">
          <h2 id="chapterTitle" class="text-2xl font-bold uppercase mb-2 text-center text-blue-900"></h2>
          <div class="w-16 h-1 bg-blue-600 mx-auto mb-8 rounded"></div>

          <div id="chapterList" class="flex-1 overflow-y-auto pr-4 space-y-6 text-sm leading-relaxed">
          </div>

          <div class="mt-auto pt-6 border-t border-gray-100 text-center text-xs text-gray-400">
            Vista previa basada en estructura JSON
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<script src="/static/js/format-viewer.js?v=9"></script>

{% endblock %}

```

---

## app/templates/pages/home.html
**Tama?o:** 4780
**SHA256:** 3cbfd55ff38d6f1b1cdc5d230e8a242e6f45fd65df64993fcf5abc9e9e07cb15
**Tipo:** html

```html
{% extends "base.html" %}
{% block content %}
<div class="max-w-6xl mx-auto">

  <!-- HERO -->
  <div class="flex flex-col md:flex-row gap-6 mb-8">
    <!-- Bienvenida -->
    <div class="flex-1">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Bienvenido a la Formatoteca</h1>
      <p class="text-gray-500">
        Cascarón base en Python. Selecciona UNI/UNAC y navega sin perder la universidad activa.
      </p>

      <!-- Selector Universidad (FUNCIONAL con ?uni=...) -->
      <div class="inline-flex bg-white p-1 rounded-lg border border-gray-200 mt-6 shadow-sm">
        <a
          href="/?uni=unac"
          class="px-6 py-2 text-sm font-medium rounded-md transition-colors
          {% if active_uni == 'unac' %}
            bg-blue-50 text-blue-700 shadow-sm border border-blue-100
          {% else %}
            text-gray-500 hover:text-gray-700 hover:bg-gray-50
          {% endif %}">
          UNAC
        </a>

        <a
          href="/?uni=uni"
          class="px-6 py-2 text-sm font-medium rounded-md transition-colors
          {% if active_uni == 'uni' %}
            bg-blue-50 text-blue-700 shadow-sm border border-blue-100
          {% else %}
            text-gray-500 hover:text-gray-700 hover:bg-gray-50
          {% endif %}">
          UNI
        </a>
      </div>

      <!-- Accesos rápidos (ejemplo) -->
      <div class="mt-6 flex gap-3 flex-wrap">
        <a
          href="/catalog?uni={{ active_uni }}"
          class="inline-flex items-center gap-2 bg-white border border-gray-200 px-4 py-2 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
          <i data-lucide="grid" class="w-4 h-4"></i> Ir al Catálogo
        </a>
        <a
          href="/alerts?uni={{ active_uni }}"
          class="inline-flex items-center gap-2 bg-white border border-gray-200 px-4 py-2 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
          <i data-lucide="bell" class="w-4 h-4"></i> Ver Alertas
        </a>
      </div>
    </div>

    <!-- Banner -->
    <a
      href="/alerts?uni={{ active_uni }}"
      class="flex-1 bg-gradient-to-br from-blue-700 to-indigo-900 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden flex flex-col justify-center min-h-[160px] hover:shadow-xl transition-shadow">
      <div class="relative z-10 max-w-sm">
        <span class="inline-block px-2 py-1 bg-white/20 rounded text-[10px] font-bold uppercase tracking-wider mb-2">
          Importante
        </span>
        <h3 class="font-bold text-xl mb-1">Centro de notificaciones</h3>
        <p class="text-blue-100 text-sm mb-4">
          Revisa comunicados, cambios de formatos y actualizaciones ({{ uni_name or 'Universidad' }}).
        </p>
        <span class="inline-flex items-center gap-1 text-sm font-medium hover:underline">
          Ir a notificaciones <i data-lucide="arrow-right" class="w-4 h-4"></i>
        </span>
      </div>
      <i data-lucide="book-open" class="absolute right-0 bottom-0 w-40 h-40 text-white/10 transform translate-x-8 translate-y-8"></i>
    </a>
  </div>

  <!-- ALERTAS RÁPIDAS -->
  <h2 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
    <i data-lucide="zap" class="w-5 h-5 text-yellow-500"></i>
    Alertas rápidas ({{ uni_name or 'Universidad' }})
  </h2>

  <div class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
    <div class="divide-y divide-gray-100">
      {% if alerts and alerts|length > 0 %}
        {% for a in alerts %}
        <div class="p-5 flex items-start gap-4 hover:bg-gray-50 transition-colors">
          <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
            <i data-lucide="bell" class="w-5 h-5"></i>
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <p class="font-semibold text-gray-900">{{ a.titulo }}</p>
              <span class="text-xs text-gray-500">{{ a.cuando }}</span>
            </div>
            <p class="text-sm text-gray-600 mt-1">{{ a.cuerpo }}</p>

            {% if a.relacionado_id %}
              <a href="/formatos/{{ a.relacionado_id }}?uni={{ active_uni }}"
                 class="mt-2 inline-block text-sm font-medium text-blue-600 hover:text-blue-800">
                Ver documento relacionado
              </a>
            {% endif %}
          </div>
        </div>
        {% endfor %}
      {% else %}
        <div class="p-6 text-sm text-gray-500">
          No hay alertas registradas aún para {{ uni_name or 'esta universidad' }}.
        </div>
      {% endif %}
    </div>
  </div>

</div>
{% endblock %}

```

---

## app/templates/pages/versions.html
**Tama?o:** 1788
**SHA256:** 34d2d5ac2dc41d9c91997929668fa14bb66e2855fe9be92184c803b8a9ffb764
**Tipo:** html

```html
{% extends "base.html" %}
{% block content %}
<div class="max-w-4xl mx-auto">

  <a href="/formatos/{{ formato.id }}" class="mb-6 flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
    <i data-lucide="arrow-left" class="w-4 h-4 mr-1"></i> Volver al documento
  </a>

  <div class="flex justify-between items-center mb-8">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Historial de Cambios</h1>
      <p class="text-gray-500">{{ formato.titulo }}</p>
    </div>
    <button class="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50">
      Descargar reporte (placeholder)
    </button>
  </div>

  <div class="relative border-l-2 border-gray-200 ml-4 space-y-10">
    {% for h in formato.historial %}
    <div class="relative pl-8">
      <div class="absolute -left-[9px] top-0 w-4 h-4 {% if h.estado == 'VIGENTE' %}bg-green-500{% else %}bg-gray-300{% endif %} rounded-full border-4 border-white shadow-sm"></div>
      <div class="{% if h.estado == 'VIGENTE' %}bg-white{% else %}bg-gray-50{% endif %} p-6 rounded-xl border border-gray-200 shadow-sm">
        <div class="flex justify-between items-start mb-2">
          <div class="flex items-center gap-3">
            <h3 class="text-lg font-bold text-gray-900">Versión {{ h.version }}</h3>
            {% if h.estado == 'VIGENTE' %}
            <span class="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded">VIGENTE</span>
            {% endif %}
          </div>
          <span class="text-sm text-gray-500">{{ h.fecha }}</span>
        </div>
        <p class="text-gray-600">{{ h.nota }}</p>
      </div>
    </div>
    {% endfor %}
  </div>

</div>
{% endblock %}

```

---

## app/universities/__init__.py
**Tama?o:** 28
**SHA256:** 0b63fdcbe42eda740bc85e341661720bf2ff4e66fa46f53eb96ff5dabccab161
**Tipo:** python

```python
# paquete de universidades

```

---

## app/universities/contracts.py
**Tama?o:** 544
**SHA256:** 3b1068338fcf5e45b730b20208961a86d55fb6563fdaff86031337cb2ca43e1b
**Tipo:** python

```python
"""Provider contract for university plugins."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence, Union, runtime_checkable

GeneratorCommand = Union[Path, Sequence[str]]


@runtime_checkable
class Provider(Protocol):
    code: str
    display_name: str

    def get_data_dir(self) -> Path:
        """Return the app/data/<code> directory."""

    def get_generator_for_category(self, category: str) -> GeneratorCommand:
        """Return the generator command or script path for a category."""

```

---

## app/universities/registry.py
**Tama?o:** 2547
**SHA256:** d9c3358b3a4a2790c6cfbfd0ac9bc6109170a4cf88aa944fb561ae0e824f5569
**Tipo:** python

```python
"""Dynamic registry for university providers."""
from __future__ import annotations

import re
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Dict

from app.universities.contracts import Provider

_UNIVERSITIES_DIR = Path(__file__).resolve().parent
_CODE_RE = re.compile(r"^[a-z0-9_-]+$")


def _iter_provider_modules():
    for child in sorted(_UNIVERSITIES_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        name = child.name
        if name in {"__pycache__"} or name.startswith(("_", ".")):
            continue
        if not (child / "provider.py").exists():
            continue
        yield f"app.universities.{name}.provider"


def _load_provider(module_name: str) -> Provider:
    module = import_module(module_name)
    if hasattr(module, "PROVIDER"):
        provider = module.PROVIDER
    elif hasattr(module, "get_provider"):
        provider = module.get_provider()
    else:
        raise ImportError(f"Provider no expuesto en {module_name}")
    return provider


def _validate_provider(provider: Provider) -> None:
    if not isinstance(provider, Provider):
        raise TypeError("Provider no cumple el contrato requerido.")
    if not isinstance(provider.code, str) or not provider.code:
        raise ValueError("Provider.code es requerido.")
    if not _CODE_RE.match(provider.code):
        raise ValueError(f"Provider.code inválido: {provider.code}")
    if not isinstance(provider.display_name, str) or not provider.display_name:
        raise ValueError("Provider.display_name es requerido.")
    data_dir = provider.get_data_dir()
    if not isinstance(data_dir, Path):
        raise TypeError("Provider.get_data_dir() debe retornar Path.")


@lru_cache(maxsize=1)
def discover_providers() -> Dict[str, Provider]:
    providers: Dict[str, Provider] = {}
    for module_name in _iter_provider_modules():
        provider = _load_provider(module_name)
        _validate_provider(provider)
        code = provider.code
        if code in providers:
            raise ValueError(f"Código de universidad duplicado: {code}")
        providers[code] = provider
    return providers


def get_provider(code: str) -> Provider:
    code = (code or "").strip().lower()
    providers = discover_providers()
    if code in providers:
        return providers[code]
    raise KeyError(f"Universidad no registrada: {code}")


def list_universities() -> list[str]:
    return sorted(discover_providers().keys())

```

---

## app/universities/unac/centro_formatos/__init__.py
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** python

```python

```

---

## app/universities/unac/centro_formatos/generador_informe_tesis.py
**Tama?o:** 15129
**SHA256:** 30f8ff57b4f266031ba67cdd8a7a59865c843fc6877439068306812ba595d128
**Tipo:** python

```python
import json
import os
import sys
from docx import Document
from docx.shared import Cm, Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.section import WD_SECTION

# ==========================================
# CONFIGURACIÓN
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", ".."))
FORMATS_DIR = os.path.join(BASE_DIR, "formats")
STATIC_ASSETS_DIR = os.path.join(PROJECT_ROOT, "app", "static", "assets")

def cargar_contenido(path_archivo):
    if not os.path.exists(path_archivo):
        nombre = os.path.basename(path_archivo)
        path_archivo = os.path.join(FORMATS_DIR, nombre)
    if not os.path.exists(path_archivo):
        raise FileNotFoundError(f"No se encontró el JSON en: {path_archivo}")
    try:
        with open(path_archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error de sintaxis en el archivo JSON: {e}")

# ==========================================
# UTILIDADES DE FORMATO Y XML
# ==========================================

def configurar_seccion_unac(section):
    """Establece tamaño A4 y márgenes oficiales UNAC."""
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3.5)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(3.0)
    section.bottom_margin = Cm(3.0)

def configurar_estilos_base(doc):
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'; font.size = Pt(11)
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

def _add_fldSimple(paragraph, instr: str):
    """Agrega campos dinámicos (TOC/PAGE) de Word."""
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instr)
    paragraph._p.append(fld)
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = " "
    r.append(t)
    fld.append(r)

def agregar_bloque(doc, texto, negrita=False, tamano=12, antes=0, despues=0):
    if not texto: return None
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(antes)
    p.paragraph_format.space_after = Pt(despues)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(texto)
    run.bold = negrita; run.font.size = Pt(tamano)
    return p

def agregar_titulo_formal(doc, texto, espaciado_antes=0):
    if not texto: return
    h = doc.add_heading(texto, level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT 
    h.paragraph_format.space_before = Pt(espaciado_antes); h.paragraph_format.space_after = Pt(12)
    run = h.runs[0]
    run.font.name = 'Arial'; run.font.size = Pt(14); run.bold = True; run.font.color.rgb = RGBColor(0, 0, 0)

def agregar_nota_estilizada(doc, texto):
    if not texto: return
    try:
        table = doc.add_table(rows=1, cols=1)
        table.autofit = False; table.columns[0].width = Cm(15.0)
        cell = table.cell(0, 0)
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), 'F2F8FD') 
        tc_pr.append(shd)
        tblBorders = OxmlElement('w:tblBorders')
        for b in ['top', 'left', 'bottom', 'right']:
            border = OxmlElement(f'w:{b}')
            border.set(qn('w:val'), 'single'); border.set(qn('w:sz'), '4'); border.set(qn('w:color'), '8DB3E2')
            tblBorders.append(border)
        table._tbl.tblPr.append(tblBorders)
        for p in cell.paragraphs: p._element.getparent().remove(p._element)
        lineas = texto.split('\n')
        for linea in lineas:
            linea = linea.strip()
            if not linea: continue 
            p = cell.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.left_indent = Pt(6); p.paragraph_format.space_after = Pt(6)
            if linea.startswith("- ") or linea.startswith("• ") or linea.startswith("* "):
                p.paragraph_format.left_indent = Cm(0.75); p.paragraph_format.first_line_indent = Cm(-0.5)
                p.add_run("•\t").font.size = Pt(10)
                p.add_run(linea[2:].strip()).font.size = Pt(10)
            elif ":" in linea and len(linea.split(":", 1)[0]) < 65:
                parts = linea.split(":", 1)
                r_t = p.add_run(parts[0] + ":"); r_t.bold = True; r_t.font.size = Pt(10)
                if len(parts) > 1: p.add_run(parts[1]).font.size = Pt(10)
            else:
                p.add_run(linea).font.size = Pt(10)
        doc.add_paragraph().paragraph_format.space_after = Pt(12)
    except: pass

# --- REFERENCIAS APA 7 ---
def imprimir_ejemplos_apa(doc, lista_ejemplos):
    if not lista_ejemplos: return
    p_head = doc.add_paragraph()
    p_head.add_run("Referencias Bibliográficas (Formato APA 7ma Ed.):").bold = True
    for ej in lista_ejemplos:
        p = doc.add_paragraph(ej)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        # Sangría Francesa (Hanging Indent) de 1.27 cm
        p.paragraph_format.left_indent = Cm(1.27)
        p.paragraph_format.first_line_indent = Cm(-1.27)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        p.paragraph_format.space_after = Pt(12)
        for r in p.runs:
            r.font.name = 'Arial'; r.font.size = Pt(11)

# ==========================================
# UTILIDADES DE MATRIZ
# ==========================================

def add_compact_p(cell, text, bold=False, color=None, bullet=False):
    p = cell.add_paragraph(); p.paragraph_format.line_spacing = 1.0; p.paragraph_format.space_after = Pt(2)
    if bullet: p.style = 'List Bullet'; p.paragraph_format.left_indent = Pt(10)
    run = p.add_run(str(text)); run.font.name = 'Arial'; run.font.size = Pt(8); run.bold = bold
    if color: run.font.color.rgb = color
    return p

def crear_tabla_matriz_consistencia(doc, matriz_data, es_cualitativo=False):
    doc.add_paragraph()
    p_t = doc.add_paragraph(); p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    titulo = "Anexo 1: Matriz de Categorización" if es_cualitativo else "Anexo 1: Matriz de Consistencia"
    r_t = p_t.add_run(titulo); r_t.bold = True; r_t.font.size = Pt(12)
    table = doc.add_table(rows=3, cols=5); table.autofit = False
    for row in table.rows:
        for cell in row.cells: cell.width = Cm(3.0)
    headers = ["PROBLEMAS", "OBJETIVOS", "SUPUESTOS" if es_cualitativo else "HIPÓTESIS", "CATEGORÍAS" if es_cualitativo else "VARIABLES", "METODOLOGÍA"]
    for i, text in enumerate(headers):
        cell = table.rows[0].cells[i]; tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), "D9D9D9"); tcPr.append(shd)
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text); r.bold = True; r.font.size = Pt(8)
    prob = matriz_data.get('problemas', {}); obj = matriz_data.get('objetivos', {}); hip = matriz_data.get('hipotesis', {}); vars_d = matriz_data.get('variables', {}); met = matriz_data.get('metodologia', {})
    for i, d in enumerate([prob, obj, hip]):
        add_compact_p(table.rows[1].cells[i], "General:", bold=True); add_compact_p(table.rows[1].cells[i], d.get('general', ''))
        add_compact_p(table.rows[2].cells[i], "Específicos:", bold=True)
        for item in d.get('especificos', []): add_compact_p(table.rows[2].cells[i], item, bullet=True)
    c_v = table.rows[1].cells[3].merge(table.rows[2].cells[3])
    vi = vars_d.get('independiente', {}); add_compact_p(c_v, vi.get('nombre', ''), bold=True, color=RGBColor(255, 0, 0))
    for d in vi.get('dimensiones', []): add_compact_p(c_v, d, bullet=True)
    add_compact_p(c_v, ""); vd = vars_d.get('dependiente', {}); add_compact_p(c_v, vd.get('nombre', ''), bold=True, color=RGBColor(0, 0, 255))
    for d in vd.get('dimensiones', []): add_compact_p(c_v, d, bullet=True)
    c_m = table.rows[1].cells[4].merge(table.rows[2].cells[4])
    for k, v in met.items():
        p = c_m.add_paragraph(); r_k = p.add_run(f"{k.capitalize()}: "); r_k.font.size = Pt(8); r_k.bold = True
        p.add_run(str(v)).font.size = Pt(8)

# ==========================================
# GENERACIÓN DE SECCIONES
# ==========================================

def crear_caratula_dinamica(doc, data):
    """Carátula distribuida en toda la hoja."""
    c = data.get('caratula', {})
    agregar_bloque(doc, c.get('universidad', ''), negrita=True, tamano=16, despues=4)
    agregar_bloque(doc, c.get('facultad', ''), negrita=True, tamano=13, despues=4)
    agregar_bloque(doc, c.get('escuela', ''), negrita=True, tamano=13, despues=25)
    
    r_l = os.path.join(STATIC_ASSETS_DIR, "LogoUNAC.png")
    if os.path.exists(r_l):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(r_l, width=Inches(2.4))
    
    agregar_bloque(doc, c.get('tipo_documento', ''), negrita=True, tamano=15, antes=40)
    agregar_bloque(doc, c.get('titulo_placeholder', ''), negrita=True, tamano=14, antes=30, despues=40)
    agregar_bloque(doc, "PARA OPTAR EL TITULO PROFESIONAL DE:", tamano=11, antes=20)
    agregar_bloque(doc, c.get('grado_objetivo', ''), negrita=True, tamano=12, despues=50)
    agregar_bloque(doc, c.get('label_autor', ''), negrita=True, tamano=11, despues=5)
    agregar_bloque(doc, c.get('label_asesor', ''), negrita=True, tamano=11, despues=30)
    agregar_bloque(doc, c.get('label_linea', ''), tamano=10, despues=60)
    
    # Empujar pie al final
    
    agregar_bloque(doc, c.get('fecha', ''), tamano=11)
    agregar_bloque(doc, c.get('pais', ''), negrita=True, tamano=11)

def agregar_indice_automatico(doc):
    agregar_bloque(doc, "ÍNDICE DE CONTENIDO", negrita=True, tamano=14, despues=12)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT; p.add_run("Pág.")
    p2 = doc.add_paragraph()
    _add_fldSimple(p2, 'TOC \\o "1-3" \\h \\z \\u')

def agregar_preliminares_dinamico(doc, data):
    p = data.get('preliminares', {})
    for sec in ['dedicatoria', 'resumen']:
        if sec in p:
            agregar_bloque(doc, p[sec].get('titulo', ''), negrita=True, tamano=14, despues=12)
            doc.add_paragraph(p[sec].get('texto', ''))
            doc.add_page_break()
    if 'indices' in p:
        agregar_indice_automatico(doc); doc.add_page_break()
    if 'introduccion' in p:
        agregar_titulo_formal(doc, p['introduccion'].get('titulo', ''))
        doc.add_paragraph(p['introduccion'].get('texto', ''))

def agregar_cuerpo_dinamico(doc, data):
    for cap in data.get('cuerpo', []):
        agregar_titulo_formal(doc, cap.get('titulo', ''), espaciado_antes=10)
        if 'nota_capitulo' in cap: agregar_nota_estilizada(doc, cap['nota_capitulo'])
        # Ejemplos APA dentro de capítulos si existen
        if 'ejemplos_apa' in cap: imprimir_ejemplos_apa(doc, cap['ejemplos_apa'])
        for item in cap.get('contenido', []):
            sub = doc.add_heading(item.get('texto', ''), level=2)
            sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
            sub.runs[0].font.name = 'Arial'; sub.runs[0].font.size = Pt(12); sub.runs[0].font.color.rgb = RGBColor(0,0,0)
            if 'instruccion_detallada' in item: agregar_nota_estilizada(doc, item['instruccion_detallada'])
        doc.add_page_break()

def agregar_finales_dinamico(doc, data):
    fin = data.get('finales', {})
    if 'referencias' in fin:
        agregar_titulo_formal(doc, fin['referencias'].get('titulo', 'REFERENCIAS BIBLIOGRÁFICAS'))
        if 'ejemplos_apa' in fin['referencias']:
            imprimir_ejemplos_apa(doc, fin['referencias']['ejemplos_apa'])
        doc.add_page_break()
    if 'anexos' in fin:
        agregar_titulo_formal(doc, fin['anexos'].get('titulo_seccion', 'ANEXOS'))
        if 'matriz_consistencia' in data:
            es_cuali = "CUALITATIVO" in data.get('caratula', {}).get('tipo_documento', '').upper()
            crear_tabla_matriz_consistencia(doc, data['matriz_consistencia'], es_cuali)
            doc.add_page_break()
        for anexo in fin['anexos'].get('lista', []):
            if "Matriz" in anexo.get('titulo', ''): continue
            p = doc.add_paragraph(anexo.get('titulo', '')); p.runs[0].bold = True; doc.add_page_break()

# ==========================================
# NUMERACIÓN Y EJECUCIÓN
# ==========================================

def configurar_numeracion_tesis(doc):
    doc.sections[0].different_first_page_header_footer = True
    # Carátula y Hoja Respeto no llevan número visible
    for i in range(min(len(doc.sections), 2)):
        doc.sections[i].footer.is_linked_to_previous = False
    # Romanos desde la sección 3 (Dedicatoria)
    if len(doc.sections) > 2:
        s = doc.sections[2]; s.footer.is_linked_to_previous = False
        pg = OxmlElement('w:pgNumType'); pg.set(qn('w:fmt'), 'lowerRoman'); pg.set(qn('w:start'), '1')
        s._sectPr.append(pg); _insertar_n(s.footer)
    # Arábigos desde el Cuerpo
    if len(doc.sections) > 3:
        s = doc.sections[3]; s.footer.is_linked_to_previous = False
        pg = OxmlElement('w:pgNumType'); pg.set(qn('w:fmt'), 'decimal'); pg.set(qn('w:start'), '1')
        s._sectPr.append(pg); _insertar_n(s.footer)

def _insertar_n(footer):
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT; run = p.add_run()
    f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = "PAGE"
    f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'end')
    run._r.extend([f1, it, f2])

def generar_documento_core(ruta_json, ruta_salida):
    data = cargar_contenido(ruta_json); doc = Document(); configurar_estilos_base(doc)
    
    # 1. CARÁTULA
    configurar_seccion_unac(doc.sections[0]); crear_caratula_dinamica(doc, data)
    # 2. HOJA DE RESPETO
    doc.add_section(WD_SECTION.NEW_PAGE); configurar_seccion_unac(doc.sections[-1]); doc.add_paragraph("")
    # 3. PRELIMINARES
    doc.add_section(WD_SECTION.NEW_PAGE); configurar_seccion_unac(doc.sections[-1]); agregar_preliminares_dinamico(doc, data)
    # 4. CUERPO
    doc.add_section(WD_SECTION.NEW_PAGE); configurar_seccion_unac(doc.sections[-1]); agregar_cuerpo_dinamico(doc, data)
    # 5. FINALES
    agregar_finales_dinamico(doc, data)
    # 6. CONFIGURACIÓN FINAL
    configurar_numeracion_tesis(doc)
    doc.settings.element.append(OxmlElement('w:updateFields'))
    doc.save(ruta_salida); return ruta_salida

if __name__ == "__main__":
    if len(sys.argv) > 2: generar_documento_core(sys.argv[1], sys.argv[2])

```

---

## app/universities/unac/centro_formatos/generador_maestria.py
**Tama?o:** 17856
**SHA256:** c0bb136097baf6712fe9de6fbb2a9649379d63895f94ebe25ad470b03a9a5a21
**Tipo:** python

```python
﻿#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de maestria UNAC (legacy-style).
- Espera JSON con schema legacy: caratula/preliminares/cuerpo/finales.
- Mantiene flujo y secciones similares a generador_informe_tesis.py.
"""
import json
import os
import re
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Inches

from generador_informe_tesis import (
    configurar_seccion_unac,
    configurar_estilos_base,
    agregar_bloque,
    agregar_titulo_formal,
    agregar_nota_estilizada,
    imprimir_ejemplos_apa,
    crear_tabla_matriz_consistencia,
    _add_fldSimple,
    _insertar_n,
)
from generador_proyecto_tesis import (
    crear_tabla_estilizada,
    agregar_nota_guia,
    encontrar_recurso,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FORMATS_DIR = os.path.join(BASE_DIR, "formats")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FALLBACK_FIGURE_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", "static", "assets", "figura_ejemplo.png"))


# ==========================================
# CARGA JSON
# ==========================================

def cargar_contenido(path_archivo):
    if not os.path.exists(path_archivo):
        nombre = os.path.basename(path_archivo)
        path_archivo = os.path.join(FORMATS_DIR, nombre)
    if not os.path.exists(path_archivo):
        raise FileNotFoundError(f"No se encontro el JSON en: {path_archivo}")
    try:
        with open(path_archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error de sintaxis en el archivo JSON: {e}")


# ==========================================
# CARATULA
# ==========================================

def crear_caratula_dinamica(doc, data):
    c = data.get("caratula", {})
    agregar_bloque(doc, c.get("universidad", ""), negrita=True, tamano=16, despues=4)
    agregar_bloque(doc, c.get("facultad", ""), negrita=True, tamano=13, despues=4)
    agregar_bloque(doc, c.get("escuela", ""), negrita=True, tamano=13, despues=14)

    ruta_logo = encontrar_recurso("LogoUNAC.png")
    if ruta_logo:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(ruta_logo, width=Inches(2.4))

    agregar_bloque(doc, c.get("tipo_documento", ""), negrita=True, tamano=15, antes=22)
    agregar_bloque(doc, c.get("titulo_placeholder", ""), negrita=True, tamano=14, antes=14, despues=14)

    if c.get("guia"):
        agregar_nota_estilizada(doc, c.get("guia"))

    frase = c.get("frase_grado") or "PARA OPTAR EL GRADO ACADEMICO DE:"
    agregar_bloque(doc, frase, tamano=11, antes=10)
    agregar_bloque(doc, c.get("grado_objetivo", ""), negrita=True, tamano=12, despues=20)
    agregar_bloque(doc, c.get("label_autor", ""), negrita=True, tamano=11, despues=3)
    agregar_bloque(doc, c.get("label_asesor", ""), negrita=True, tamano=11, despues=10)
    agregar_bloque(doc, c.get("label_linea", ""), tamano=10, despues=16)
    agregar_bloque(doc, c.get("fecha", ""), tamano=11)
    agregar_bloque(doc, c.get("pais", ""), negrita=True, tamano=11)


# ==========================================
# PRELIMINARES
# ==========================================

def _add_label_value(doc, label, value):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(label or "")
    run.bold = True
    p.add_run(" ")
    p.add_run(value or "")


def agregar_titulo_preliminar(doc, texto):
    if not texto:
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(texto)
    run.bold = True
    run.font.name = 'Arial'
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)

def agregar_informacion_basica(doc, info, add_page_break=True):
    if not info:
        return
    agregar_titulo_preliminar(doc, info.get("titulo", "INFORMACION BASICA"))
    for item in info.get("elementos", []):
        _add_label_value(doc, item.get("label", ""), item.get("valor", ""))
    if add_page_break:
        doc.add_page_break()


def agregar_hoja_jurado(doc, data, add_page_break=True):
    if not data:
        return
    agregar_titulo_preliminar(doc, data.get("titulo", "HOJA DE REFERENCIA DEL JURADO Y APROBACION"))

    miembros = data.get("miembros", [])
    for miembro in miembros:
        rol = miembro.get("role", "")
        nombre = miembro.get("name", "")
        _add_label_value(doc, f"{rol}:", nombre)

    asesor = data.get("asesor")
    if asesor:
        _add_label_value(doc, "ASESOR:", asesor)

    acta = data.get("acta", {})
    if acta:
        _add_label_value(doc, "LIBRO:", acta.get("libro", ""))
        _add_label_value(doc, "ACTAS:", acta.get("actas", ""))
        _add_label_value(doc, "FOLIO:", acta.get("folio", ""))
        _add_label_value(doc, "FECHA:", acta.get("fecha", ""))
        _add_label_value(doc, "RESOLUCION:", acta.get("resolucion", ""))

    if add_page_break:
        doc.add_page_break()


def agregar_titulo_indice(doc, texto):
    if not texto:
        return
    h = doc.add_heading(texto, level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if h.runs:
        h.runs[0].font.name = 'Arial'
        h.runs[0].font.size = Pt(14)
        h.runs[0].bold = True
        h.runs[0].font.color.rgb = RGBColor(0, 0, 0)



def _strip_caption_prefix(label, texto):
    if not texto:
        return ""
    t = texto.strip()
    if t.lower().startswith(label.lower()):
        t = t[len(label):].lstrip()
        t = re.sub(r"^[0-9IVXLCDM]+([\.-][0-9]+)*[\.:\-]?\s*", "", t, flags=re.I)
    return t

def _infer_caption_label(texto):
    if texto and texto.strip().lower().startswith("figura"):
        return "Figura"
    return "Tabla"

def agregar_caption(doc, label, texto):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"{label} ")
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0, 0, 0)
    _add_fldSimple(p, f"SEQ {label} \\* ARABIC")
    if texto:
        p.add_run(". ")
        t_run = p.add_run(texto)
        t_run.font.name = "Arial"
        t_run.font.size = Pt(11)
        t_run.font.color.rgb = RGBColor(0, 0, 0)


def agregar_abreviaturas(doc, data, add_page_break=True):
    if not data:
        return
    agregar_titulo_indice(doc, data.get("titulo", "INDICE DE ABREVIATURAS"))
    ejemplo = data.get("ejemplo")
    if ejemplo:
        p = doc.add_paragraph(ejemplo)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    nota = data.get("nota")
    if nota:
        agregar_nota_estilizada(doc, nota)
    if add_page_break:
        doc.add_page_break()


def agregar_indices(doc, indices):
    if not indices:
        return
    agregar_titulo_indice(doc, indices.get("contenido", "INDICE DE CONTENIDO"))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run("Pag.")
    p2 = doc.add_paragraph()
    _add_fldSimple(p2, 'TOC \\o "1-3" \\h \\z \\u')
    doc.add_page_break()

    if indices.get("tablas"):
        agregar_titulo_indice(doc, indices.get("tablas"))
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.add_run("Pag.")
        p2 = doc.add_paragraph()
        _add_fldSimple(p2, 'TOC \\h \\z \\c "Tabla"')
        doc.add_page_break()

    if indices.get("figuras"):
        agregar_titulo_indice(doc, indices.get("figuras"))
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.add_run("Pag.")
        p2 = doc.add_paragraph()
        _add_fldSimple(p2, 'TOC \\h \\z \\c "Figura"')
        doc.add_page_break()


def agregar_preliminares_romanos(doc, data):
    p = data.get("preliminares", {})

    info = data.get("informacion_basica") or p.get("informacion_basica")
    hoja_jurado = p.get("hoja_jurado")
    blocks = []
    if info:
        blocks.append(("info", info))
    if hoja_jurado:
        blocks.append(("hoja_jurado", hoja_jurado))
    for sec in ["dedicatoria", "resumen", "agradecimientos"]:
        if sec in p:
            blocks.append((sec, p[sec]))

    for idx, (kind, payload) in enumerate(blocks):
        is_last = idx == len(blocks) - 1
        if kind == "info":
            agregar_informacion_basica(doc, payload, add_page_break=not is_last)
        elif kind == "hoja_jurado":
            agregar_hoja_jurado(doc, payload, add_page_break=not is_last)
        else:
            agregar_bloque(doc, payload.get("titulo", ""), negrita=True, tamano=14, despues=12)
            doc.add_paragraph(payload.get("texto", ""))
            if not is_last:
                doc.add_page_break()


def agregar_indices_y_introduccion(doc, data):
    p = data.get("preliminares", {})
    if "indices" in p:
        agregar_indices(doc, p.get("indices"))

    if "abreviaturas" in p:
        agregar_abreviaturas(doc, p.get("abreviaturas"))

    if "introduccion" in p:
        agregar_titulo_formal(doc, p["introduccion"].get("titulo", ""))
        agregar_nota_estilizada(doc, p["introduccion"].get("texto", ""))
        if data.get("cuerpo"):
            doc.add_page_break()


# ==========================================
# CUERPO
# ==========================================

def _agregar_imagenes(doc, imagenes):
    for img in imagenes or []:
        caption_raw = img.get("titulo") or "Figura"
        caption_text = _strip_caption_prefix("Figura", caption_raw)
        agregar_caption(doc, "Figura", caption_text)

        ruta = img.get("ruta")
        if not ruta or ruta == "placeholder":
            ruta = FALLBACK_FIGURE_PATH if os.path.exists(FALLBACK_FIGURE_PATH) else None
        if ruta:
            path = encontrar_recurso(ruta)
            if path:
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.add_run().add_picture(path, width=Cm(12.0))
            else:
                p = doc.add_paragraph("[IMAGEN NO ENCONTRADA]")
                p.runs[0].font.color.rgb = RGBColor(255, 0, 0)
        else:
            doc.add_paragraph("[IMAGEN]")

        if img.get("fuente"):
            agregar_nota_estilizada(doc, img.get("fuente"))


def agregar_cuerpo_dinamico(doc, data):
    for cap in data.get("cuerpo", []):
        agregar_titulo_formal(doc, cap.get("titulo", ""), espaciado_antes=10)
        if "nota_capitulo" in cap:
            agregar_nota_estilizada(doc, cap["nota_capitulo"])

        if "ejemplos_apa" in cap:
            imprimir_ejemplos_apa(doc, cap.get("ejemplos_apa"))

        for item in cap.get("contenido", []):
            if "texto" in item:
                sub = doc.add_heading(item.get("texto", ""), level=2)
                sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
                if sub.runs:
                    sub.runs[0].font.name = "Arial"
                    sub.runs[0].font.size = Pt(12)
                    sub.runs[0].font.color.rgb = RGBColor(0, 0, 0)

            if "nota" in item:
                agregar_nota_estilizada(doc, item.get("nota", ""))

            if "instruccion_detallada" in item:
                agregar_nota_estilizada(doc, item.get("instruccion_detallada", ""))

            if item.get("mostrar_matriz") and "matriz_consistencia" in data:
                crear_tabla_matriz_consistencia(doc, data["matriz_consistencia"], False)

            if "tablas_especiales" in item:
                for t_esp in item.get("tablas_especiales", []):
                    titulo = t_esp.get("titulo", "")
                    label = _infer_caption_label(titulo)
                    caption_text = _strip_caption_prefix(label, titulo)
                    agregar_caption(doc, label, caption_text)
                    crear_tabla_estilizada(doc, t_esp)

            if "tabla" in item:
                titulo_tabla = item.get("tabla_titulo", "")
                caption_text = _strip_caption_prefix("Tabla", titulo_tabla)
                agregar_caption(doc, "Tabla", caption_text)
                crear_tabla_estilizada(doc, item.get("tabla"))
                if item.get("tabla_nota"):
                    agregar_nota_estilizada(doc, item.get("tabla_nota"))

            if "imagenes" in item:
                _agregar_imagenes(doc, item.get("imagenes"))

            if "parrafos" in item:
                for par in item.get("parrafos", []):
                    doc.add_paragraph(par)

            doc.add_paragraph("")

        doc.add_page_break()


# ==========================================
# FINALES
# ==========================================

def agregar_finales_dinamico(doc, data):
    fin = data.get("finales", {})

    if "referencias" in fin:
        ref = fin.get("referencias", {})
        agregar_titulo_formal(doc, ref.get("titulo", "REFERENCIAS BIBLIOGRAFICAS"))
        if ref.get("nota"):
            agregar_nota_estilizada(doc, ref.get("nota"))
        if ref.get("ejemplos_apa"):
            imprimir_ejemplos_apa(doc, ref.get("ejemplos_apa"))
        elif ref.get("ejemplos"):
            for ejemplo in ref.get("ejemplos", []):
                doc.add_paragraph(ejemplo)
        doc.add_page_break()

    if "anexos" in fin:
        anexos = fin.get("anexos", {})
        agregar_titulo_formal(doc, anexos.get("titulo_seccion", "ANEXOS"))
        if anexos.get("nota"):
            agregar_nota_estilizada(doc, anexos.get("nota"))
        if "matriz_consistencia" in data:
            crear_tabla_matriz_consistencia(doc, data["matriz_consistencia"], False)
            doc.add_page_break()

        for anexo in anexos.get("lista", []):
            p = doc.add_paragraph(anexo.get("titulo", ""))
            if p.runs:
                p.runs[0].bold = True

            if anexo.get("nota"):
                agregar_nota_estilizada(doc, anexo.get("nota"))

            if anexo.get("tabla"):
                titulo_tabla = anexo.get("tabla_titulo", "")
                caption_text = _strip_caption_prefix("Tabla", titulo_tabla)
                agregar_caption(doc, "Tabla", caption_text)
                crear_tabla_estilizada(doc, anexo.get("tabla"))
                if anexo.get("tabla_nota"):
                    agregar_nota_estilizada(doc, anexo.get("tabla_nota"))

            if anexo.get("parrafos"):
                for par in anexo.get("parrafos", []):
                    doc.add_paragraph(par)

            doc.add_page_break()


# ==========================================
# EJECUCION
# ==========================================

def configurar_numeracion_maestria(doc):
    """Numeracion roman para respeto/preliminares y arabiga desde indice."""
    doc.sections[0].different_first_page_header_footer = True
    for i in range(min(len(doc.sections), 2)):
        doc.sections[i].footer.is_linked_to_previous = False

    # Seccion 2 (hoja de respeto): romanos iniciando en II
    if len(doc.sections) > 1:
        s = doc.sections[1]
        s.footer.is_linked_to_previous = False
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), "upperRoman")
        pg.set(qn("w:start"), "2")
        s._sectPr.append(pg)
        _insertar_n(s.footer)

    # Seccion 3 (preliminares): continuar romanos
    if len(doc.sections) > 2:
        s = doc.sections[2]
        s.footer.is_linked_to_previous = False
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), "upperRoman")
        s._sectPr.append(pg)
        _insertar_n(s.footer)

    # Seccion 4 (indices/cuerpo): arabigos desde 1
    if len(doc.sections) > 3:
        s = doc.sections[3]
        s.footer.is_linked_to_previous = False
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:fmt"), "decimal")
        pg.set(qn("w:start"), "1")
        s._sectPr.append(pg)
        _insertar_n(s.footer)


def generar_documento_core(ruta_json, ruta_salida):
    data = cargar_contenido(ruta_json)
    doc = Document()
    configurar_estilos_base(doc)

    # 1. CARATULA
    configurar_seccion_unac(doc.sections[0])
    crear_caratula_dinamica(doc, data)

    # 2. HOJA DE RESPETO (BLANCA O CON NOTAS)
    doc.add_section(WD_SECTION.NEW_PAGE)
    configurar_seccion_unac(doc.sections[-1])
    respeto = data.get("pagina_respeto", {})
    notas = respeto.get("notas", []) if isinstance(respeto, dict) else []
    if notas:
        for nota in notas:
            doc.add_paragraph(nota.get("texto", ""))
    else:
        doc.add_paragraph("")

    # 3. PRELIMINARES (ROMANOS)
    doc.add_section(WD_SECTION.NEW_PAGE)
    configurar_seccion_unac(doc.sections[-1])
    agregar_preliminares_romanos(doc, data)

    # 4. INDICES + CUERPO + FINALES (ARABIGOS)
    doc.add_section(WD_SECTION.NEW_PAGE)
    configurar_seccion_unac(doc.sections[-1])
    agregar_indices_y_introduccion(doc, data)
    agregar_cuerpo_dinamico(doc, data)

    # 5. FINALES
    agregar_finales_dinamico(doc, data)

    # 6. CONFIGURACION FINAL
    configurar_numeracion_maestria(doc)
    doc.settings.element.append(OxmlElement("w:updateFields"))
    doc.save(ruta_salida)
    return ruta_salida


if __name__ == "__main__":
    if len(sys.argv) > 2:
        generar_documento_core(sys.argv[1], sys.argv[2])

```

---

## app/universities/unac/centro_formatos/generador_proyecto_tesis.py
**Tama?o:** 24139
**SHA256:** fbef285926bcea11b4baa617e4d8ef2cfd60f1c8e945a58602ee572cb9664e6a
**Tipo:** python

```python
import json
import os
import sys
from docx import Document
from docx.shared import Cm, Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER

# ==========================================
# 1. CONFIGURACIÓN Y RUTAS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", ".."))
FORMATS_DIR = os.path.join(BASE_DIR, "formats")
STATIC_ASSETS_DIR = os.path.join(PROJECT_ROOT, "app", "static", "assets")

def encontrar_recurso(nombre_archivo):
    """Busca imágenes o logos en varias carpetas comunes."""
    rutas_a_probar = [
        nombre_archivo, # En la misma carpeta
        os.path.join(BASE_DIR, nombre_archivo),
        os.path.join(BASE_DIR, "assets", nombre_archivo),
        os.path.join(BASE_DIR, "static", "assets", nombre_archivo),
        os.path.join(STATIC_ASSETS_DIR, nombre_archivo),
        # Subir un nivel
        os.path.join(BASE_DIR, "..", nombre_archivo),
        os.path.join(BASE_DIR, "..", "assets", nombre_archivo),
        # Estructura típica de proyectos web
        os.path.join(PROJECT_ROOT, "app", "static", "assets", nombre_archivo)
    ]
    
    for ruta in rutas_a_probar:
        if os.path.exists(ruta):
            print(f"[DEBUG] Archivo encontrado: {ruta}")
            return ruta
    return None

def cargar_contenido(path_archivo):
    if not os.path.exists(path_archivo):
        path_archivo = os.path.join(BASE_DIR, path_archivo)
    if not os.path.exists(path_archivo):
        raise FileNotFoundError(f"No se encontró el JSON en: {path_archivo}")

    with open(path_archivo, 'r', encoding='utf-8') as f:
        return json.load(f)

# ==========================================
# 2. FORMATO Y ESTILOS
# ==========================================

def configurar_formato_unac(doc):
    for section in doc.sections:
        section.page_width = Cm(21.0); section.page_height = Cm(29.7)
        section.left_margin = Cm(3.5); section.right_margin = Cm(2.5)
        section.top_margin = Cm(3.0); section.bottom_margin = Cm(3.0)
    
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    
    # Opción B: WD_ALIGN_PARAGRAPH.LEFT (Todo pegado a la izquierda, borde irregular a la derecha - Lo estándar al quitar justificado)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

def agregar_bloque(doc, texto, negrita=False, tamano=12, antes=0, despues=0, cursiva=False):
    if not texto: return
    p = doc.add_paragraph()
    
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER 
    
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE 
    p.paragraph_format.space_before = Pt(antes)
    p.paragraph_format.space_after = Pt(despues)
    run = p.add_run(texto)
    run.bold = negrita; run.italic = cursiva; run.font.size = Pt(tamano)

def agregar_titulo_formal(doc, texto, espaciado_antes=0):
    if not texto: return
    h = doc.add_heading(level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = h.add_run(texto)
    run.font.name = 'Arial'; run.font.size = Pt(14); run.bold = True; run.font.color.rgb = RGBColor(0, 0, 0)
    h.paragraph_format.space_before = Pt(espaciado_antes)
    h.paragraph_format.space_after = Pt(12)

def agregar_nota_guia(doc, texto):
    if not texto: return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(f"Nota: {texto}")
    run.font.name = 'Arial'; run.font.size = Pt(10); run.italic = True; run.font.color.rgb = RGBColor(89, 89, 89) 
    p.paragraph_format.space_after = Pt(12)

def agregar_nota_estilizada(doc, texto):
    """Crea un cuadro azul claro solo con el texto de la nota."""
    if not texto: return
    try:
        # Crear tabla de 1 celda para el fondo
        table = doc.add_table(rows=1, cols=1)
        table.autofit = False 
        table.columns[0].width = Cm(15.0) # Ancho fijo para que no se deforme
        
        cell = table.cell(0, 0)
        
        # Color de fondo (Azul muy suave F2F8FD)
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), 'F2F8FD')
        tc_pr.append(shd)
        
        # Bordes (Azul intermedio 8DB3E2)
        tblBorders = OxmlElement('w:tblBorders')
        for border_name in ['top', 'left', 'bottom', 'right']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), '4')
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), '8DB3E2')
            tblBorders.append(border)
        table._tbl.tblPr.append(tblBorders)

        # Contenido (Sin prefijos, solo el texto)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(texto)
        run.font.name = 'Arial'
        run.font.size = Pt(9) # Letra un poco más pequeña para diferenciar
        
        # Espacio después del cuadro
        doc.add_paragraph().paragraph_format.space_after = Pt(6)
        
    except Exception as e:
        # Fallback por si algo falla en el XML
        print(f"[Warn] No se pudo estilizar nota: {e}")
        p = doc.add_paragraph(texto)
        p.runs[0].font.size = Pt(9)
        p.runs[0].italic = True

def agregar_tabla_simple(doc, data_tabla):
    if not data_tabla: return
    headers = data_tabla.get('headers', [])
    rows = data_tabla.get('rows', [])
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        hdr_cells[i].paragraphs[0].runs[0].bold = True
        
    for r in rows:
        row_cells = table.add_row().cells
        for i, val in enumerate(r):
            if i < len(row_cells): row_cells[i].text = str(val)
    doc.add_paragraph()

def crear_tabla_estilizada(doc, data_tabla):
    if not data_tabla: return
    headers = data_tabla.get('headers', [])
    rows = data_tabla.get('rows', [])
    
    # Crear tabla con bordes definidos
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    table.autofit = False # Usamos ancho fijo para mejor distribución
    
    # Ancho de columnas (Ajuste para que quepa en la hoja)
    ancho_total = 26.0 # cm (considerando hoja horizontal o márgenes estrechos)
    ancho_col = ancho_total / len(headers)
    
    # --- ENCABEZADOS ---
    hdr_cells = table.rows[0].cells
    for i, text in enumerate(headers):
        cell = hdr_cells[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(9) # Letra un poco más pequeña para títulos
        run.font.name = 'Arial'
        
        # Color de Fondo Gris (D9D9D9) igual a la imagen
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), 'D9D9D9')
        tcPr.append(shd)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    # --- FILAS DE CONTENIDO ---
    for row_data in rows:
        row_cells = table.add_row().cells
        for i, cell_text in enumerate(row_data):
            if i < len(row_cells):
                cell = row_cells[i]
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER # Centrado como en la imagen
                
                # Procesar saltos de línea y negritas simuladas
                texto_str = str(cell_text)
                run = p.add_run(texto_str)
                run.font.size = Pt(8) # Letra pequeña (8pt) para que entre todo
                run.font.name = 'Arial Narrow' # Fuente más compacta
                
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    doc.add_paragraph() # Espacio final

# ==========================================
# 3. LÓGICA DE MATRIZ (COMPACTA)
# ==========================================
def establecer_bordes_horizontales(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'bottom', 'insideH']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single'); border.set(qn('w:sz'), '4'); border.set(qn('w:space'), '0'); border.set(qn('w:color'), 'auto')
        tblBorders.append(border)
    for border_name in ['left', 'right', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'nil')
        tblBorders.append(border)
    if tblPr.find(qn('w:tblBorders')) is not None: tbl.tblPr.remove(tbl.tblPr.find(qn('w:tblBorders')))
    tblPr.append(tblBorders)

def add_compact_p(cell, text, bold=False, italic=False, color=None, bullet=False, align=WD_ALIGN_PARAGRAPH.LEFT):
    p = cell.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(3); p.paragraph_format.space_before = Pt(0)
    if bullet:
        p.style = 'List Bullet'
        p.paragraph_format.left_indent = Pt(10)
    run = p.add_run(str(text))
    run.font.name = 'Arial'; run.font.size = Pt(8); run.bold = bold; run.italic = italic
    if color: run.font.color.rgb = color
    return p

def crear_tabla_matriz_consistencia(doc, matriz_data, titulo="Figura 2.1 Matriz de consistencia"):
    p_titulo = doc.add_paragraph(titulo)
    p_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_titulo.runs[0].bold = True; p_titulo.runs[0].font.size = Pt(11)
    
    # Subtítulo con colores
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    vi = matriz_data.get('variables', {}).get('independiente', {}).get('nombre', 'VI')
    vd = matriz_data.get('variables', {}).get('dependiente', {}).get('nombre', 'VD')
    
    r1 = p2.add_run(f"{vi} "); r1.bold = True; r1.font.color.rgb = RGBColor(255, 0, 0); r1.font.size = Pt(9)
    p2.add_run("PARA REDUCIR EL ").font.size = Pt(9)
    r2 = p2.add_run(f"{vd} "); r2.bold = True; r2.font.color.rgb = RGBColor(0, 112, 192); r2.font.size = Pt(9)
    
    table = doc.add_table(rows=3, cols=5)
    establecer_bordes_horizontales(table)
    # Ajuste de anchos manual
    anchos = [Cm(3.5), Cm(3.5), Cm(3.5), Cm(3.0), Cm(3.0)]
    for row in table.rows:
        for idx, cell in enumerate(row.cells): cell.width = anchos[idx]

    headers = ["PROBLEMAS", "OBJETIVOS", "HIPÓTESIS", "VARIABLES", "METODOLOGÍA"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), "D9D9D9"); tcPr.append(shd)
        cell.text = ""; p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h); run.bold = True; run.font.size = Pt(8)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    prob = matriz_data.get('problemas', {})
    obj = matriz_data.get('objetivos', {})
    hip = matriz_data.get('hipotesis', {})
    vars_data = matriz_data.get('variables', {})
    met = matriz_data.get('metodologia', {})

    # Fila 1: General
    add_compact_p(table.rows[1].cells[0], "General:", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_compact_p(table.rows[1].cells[0], prob.get('general', ''), align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_compact_p(table.rows[1].cells[1], "General:", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_compact_p(table.rows[1].cells[1], obj.get('general', ''), align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    add_compact_p(table.rows[1].cells[2], "General:", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_compact_p(table.rows[1].cells[2], hip.get('general', ''), align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # Fila 2: Específicos
    add_compact_p(table.rows[2].cells[0], "Específicos:", bold=True)
    for t in prob.get('especificos', []): add_compact_p(table.rows[2].cells[0], t, bullet=True)
    add_compact_p(table.rows[2].cells[1], "Específicos:", bold=True)
    for t in obj.get('especificos', []): add_compact_p(table.rows[2].cells[1], t, bullet=True)
    add_compact_p(table.rows[2].cells[2], "Específicos:", bold=True)
    for t in hip.get('especificos', []): add_compact_p(table.rows[2].cells[2], t, bullet=True)

    # Variables (Fusionada)
    cell_var = table.rows[1].cells[3].merge(table.rows[2].cells[3])
    add_compact_p(cell_var, "V. INDEPENDIENTE", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_compact_p(cell_var, vars_data.get('independiente', {}).get('nombre', ''), bold=True, color=RGBColor(255,0,0), align=WD_ALIGN_PARAGRAPH.CENTER)
    for d in vars_data.get('independiente', {}).get('dimensiones', []): add_compact_p(cell_var, d, bullet=True)
    add_compact_p(cell_var, "")
    add_compact_p(cell_var, "V. DEPENDIENTE", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_compact_p(cell_var, vars_data.get('dependiente', {}).get('nombre', ''), bold=True, color=RGBColor(0,112,192), align=WD_ALIGN_PARAGRAPH.CENTER)
    for d in vars_data.get('dependiente', {}).get('dimensiones', []): add_compact_p(cell_var, d, bullet=True)

    # Metodología (Fusionada)
    cell_met = table.rows[1].cells[4].merge(table.rows[2].cells[4])
    cell_met.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    for k, v in met.items():
        if k == 'procesamiento': continue
        add_compact_p(cell_met, k.capitalize(), bold=True)
        add_compact_p(cell_met, str(v))
    
    doc.add_page_break()

# ==========================================
# 4. GENERADORES DE SECCIONES
# ==========================================

def crear_caratula_dinamica(doc, data):
    c = data.get('caratula', {})
    agregar_bloque(doc, c.get('universidad', ''), negrita=True, tamano=18, despues=4)
    agregar_bloque(doc, c.get('facultad', ''), negrita=True, tamano=14, despues=4)
    agregar_bloque(doc, c.get('escuela', ''), negrita=True, tamano=14, despues=25)
    
    ruta_logo = encontrar_recurso("LogoUNAC.png")
    if ruta_logo:
        try:
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(ruta_logo, width=Inches(3.2))
        except: pass
    else:
        agregar_bloque(doc, "[LOGO UNAC]", tamano=10, antes=40, despues=40)
        
    agregar_bloque(doc, c.get('tipo_documento', ''), negrita=True, tamano=16, antes=30)
    agregar_bloque(doc, c.get('titulo_placeholder', ''), negrita=True, tamano=14, antes=30, despues=30)
    agregar_bloque(doc, c.get('frase_grado', ''), tamano=12, antes=10)
    agregar_bloque(doc, c.get('grado_objetivo', ''), negrita=True, tamano=13, despues=35)
    agregar_bloque(doc, c.get('label_autor', ''), negrita=True, tamano=12, antes=5)
    agregar_bloque(doc, c.get('label_asesor', ''), negrita=True, tamano=12, antes=5, despues=20)
    agregar_bloque(doc, c.get('label_linea', ''), tamano=11, cursiva=True, despues=40)
    agregar_bloque(doc, c.get('fecha', ''), tamano=12)
    agregar_bloque(doc, c.get('pais', ''), negrita=True, tamano=12)

def generar_pagina_respeto(doc, data):
    respeto = data.get('pagina_respeto', {})
    if not respeto: return
    table = doc.add_table(rows=1, cols=1)
    table.style = 'Table Grid'; table.autofit = False; table.cell(0, 0).width = Cm(15.5)
    cell = table.cell(0, 0); cell._element.clear_content()
    for nota in respeto.get('notas', []):
        p = cell.add_paragraph(nota.get('texto', ''))
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(12)
    doc.add_page_break()

def agregar_preliminares_dinamico(doc, data):
    p = data.get('preliminares', {})
    
    # 1. GENERACIÓN DE ÍNDICES (General, Tablas, Figuras, Abreviaturas)
    if 'indices' in p:
        lista_indices = p['indices']
        # Validamos si es una lista (Tu JSON actual)
        if isinstance(lista_indices, list):
            for bloque_indice in lista_indices:
                # Título del índice (Ej: ÍNDICE DE TABLAS)
                agregar_titulo_formal(doc, bloque_indice.get('titulo', ''))
                
                # Nota opcional (Ej: para Abreviaturas)
                if 'nota' in bloque_indice:
                    p_nota = doc.add_paragraph(bloque_indice['nota'])
                    p_nota.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p_nota.runs[0].italic = True
                    p_nota.paragraph_format.space_after = Pt(12)

                # Generar cada línea del índice
                for item in bloque_indice.get('items', []):
                    paragraph = doc.add_paragraph()
                    paragraph.paragraph_format.space_after = Pt(3) # Espacio pequeño entre líneas
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT # Importante: Alinear izquierda para que los puntos funcionen
                    
                    # Configurar el tabulador derecho (Puntos suspensivos hasta el final)
                    # Ancho A4 (21cm) - Márgenes (2.5+3.5=6cm) = 15cm ancho útil aprox.
                    tab_stops = paragraph.paragraph_format.tab_stops
                    tab_stops.add_tab_stop(Cm(15.0), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
                    
                    # Escribir Texto (Ej: "I. PLANTEAMIENTO...")
                    run = paragraph.add_run(item.get('texto', ''))
                    run.font.name = 'Arial'
                    run.font.size = Pt(11)
                    if item.get('bold'): run.bold = True
                    
                    # Escribir Número de Página (Ej: "6")
                    if 'pag' in item:
                        run_pag = paragraph.add_run(f"\t{item['pag']}")
                        run_pag.font.name = 'Arial'
                        run_pag.font.size = Pt(11)
                
                doc.add_page_break()

def agregar_cuerpo_dinamico(doc, data):
    for cap in data.get('cuerpo', []):
        agregar_titulo_formal(doc, cap.get('titulo', ''), espaciado_antes=24)
        
        if 'nota_capitulo' in cap: 
            agregar_nota_estilizada(doc, cap['nota_capitulo'])
        
        for item in cap.get('contenido', []):
            # 1. Subtítulo
            if 'texto' in item:
                sub = doc.add_paragraph()
                run = sub.add_run(item.get('texto', ''))
                run.font.name = 'Arial'; run.font.size = Pt(12); run.bold = True
            
            # 2. Nota corta
            if 'nota' in item: 
                agregar_nota_guia(doc, item['nota'])
            
            # 3. Instrucción Detallada
            if 'instruccion_detallada' in item:
                agregar_nota_estilizada(doc, item['instruccion_detallada'])
            
            # 4. MATRICES AUTOMÁTICAS (2.1)
            if item.get('mostrar_matriz') == True and 'matriz_consistencia' in data:
                crear_tabla_matriz_consistencia(doc, data['matriz_consistencia'])

            # 5. MATRICES ESPECIALES (2.2, 2.3) - NUEVO BLOQUE
            if 'tablas_especiales' in item:
                for t_esp in item['tablas_especiales']:
                    p_tit = doc.add_paragraph(t_esp.get('titulo', ''))
                    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_tit.runs[0].bold = True
                    p_tit.runs[0].font.size = Pt(11)
                    crear_tabla_estilizada(doc, t_esp)

            # 6. IMÁGENES (Solo si existen)
            if 'imagenes' in item:
                for img in item['imagenes']:
                    if 'titulo' in img:
                        doc.add_paragraph(img['titulo']).paragraph_format.space_after = Pt(6)
                    
                    ruta_img = encontrar_recurso(img['ruta'])
                    if ruta_img:
                        p_img = doc.add_paragraph(); p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_img.add_run().add_picture(ruta_img, width=Cm(12.0))
                    else:
                        doc.add_paragraph(f"[ERROR: Imagen no encontrada {img['ruta']}]").runs[0].font.color.rgb = RGBColor(255,0,0)
                    
                    if 'fuente' in img:
                        doc.add_paragraph(img['fuente']).paragraph_format.space_after = Pt(12)

            # 7. TABLAS NORMALES (3.2)
            if 'tabla' in item: 
                crear_tabla_estilizada(doc, item['tabla'])
            
            doc.add_paragraph("") 

        doc.add_page_break()

def agregar_finales_dinamico(doc, data):
    fin = data.get('finales', {})
    
    # --- SECCIÓN REFERENCIAS ---
    if 'referencias' in fin:
        ref_data = fin['referencias']
        agregar_titulo_formal(doc, "REFERENCIAS BIBLIOGRÁFICAS")
        
        # 1. Agregar la nota instructiva (cuadro azul)
        if 'nota' in ref_data:
            agregar_nota_estilizada(doc, ref_data['nota'])
        
        # 2. Agregar los ejemplos de referencias (ESTO ES LO QUE FALTABA)
        if 'ejemplos' in ref_data:
            p_ej = doc.add_paragraph()
            p_ej.add_run("Ejemplos de formato:").bold = True
            p_ej.paragraph_format.space_after = Pt(6)
            
            for ejemplo in ref_data['ejemplos']:
                p = doc.add_paragraph(ejemplo)
                p.style = 'List Bullet' # Ponerlos con viñeta para que se vea ordenado
                p.paragraph_format.space_after = Pt(6)

        doc.add_page_break()

    # --- SECCIÓN ANEXOS ---
    if 'anexos' in fin:
        agregar_titulo_formal(doc, "ANEXOS")
        for anexo in fin['anexos'].get('lista', []):
            # Título del anexo en negrita
            doc.add_paragraph(anexo.get('titulo', '')).runs[0].bold = True
            
            # Nota del anexo (si existe)
            if 'nota' in anexo:
                doc.add_paragraph(anexo['nota']).paragraph_format.space_after = Pt(12)
            else:
                doc.add_paragraph("")

def agregar_numeracion_paginas(doc):
    try:
        for section in doc.sections:
            footer = section.footer
            p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT; p.clear(); run = p.add_run()
            fldChar1 = OxmlElement('w:fldChar'); fldChar1.set(qn('w:fldCharType'), 'begin')
            instrText = OxmlElement('w:instrText'); instrText.set(qn('xml:space'), 'preserve'); instrText.text = "PAGE"
            fldChar2 = OxmlElement('w:fldChar'); fldChar2.set(qn('w:fldCharType'), 'end')
            run._r.append(fldChar1); run._r.append(instrText); run._r.append(fldChar2)
    except: pass

def generar_documento_core(ruta_json, ruta_salida):
    data = cargar_contenido(ruta_json)
    doc = Document()
    configurar_formato_unac(doc)
    crear_caratula_dinamica(doc, data)
    generar_pagina_respeto(doc, data)
    agregar_preliminares_dinamico(doc, data)
    agregar_cuerpo_dinamico(doc, data)
    agregar_finales_dinamico(doc, data)
    agregar_numeracion_paginas(doc)
    doc.save(ruta_salida)
    print(f"[OK] Generado: {ruta_salida}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        try: generar_documento_core(sys.argv[1], sys.argv[2])
        except Exception as e: print(f"[ERROR] {str(e)}"); sys.exit(1)
```

---

## app/universities/unac/provider.py
**Tama?o:** 3953
**SHA256:** cd695dcb037455287cb6189932bade747f6e45470a8ef55f2a084b3595638178
**Tipo:** python

```python
from pathlib import Path
import json

from app.core.loaders import get_data_dir

class UNACProvider:
    code = "unac"
    display_name = "UNAC"
    name = display_name

    def get_data_dir(self) -> Path:
        return get_data_dir(self.code)

    def get_generator_for_category(self, category: str) -> Path:
        base_dir = Path(__file__).resolve().parent / "centro_formatos"
        category = (category or "").strip().lower()
        mapping = {
            "informe": "generador_informe_tesis.py",
            "maestria": "generador_maestria.py",
            "proyecto": "generador_proyecto_tesis.py",
        }
        if category not in mapping:
            raise ValueError(f"generator not available for category {category}")
        return base_dir / mapping[category]

    def _load_format_from_json(self, json_path: Path, tipo: str, enfoque: str) -> dict:
        """Carga información de un JSON y la transforma para mostrar como formato."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Mapeo de tipos a etiquetas legibles
            tipo_labels = {
                "informe": "Informe de Tesis",
                "proyecto": "Proyecto de Tesis",
                "maestria": "Tesis de Maestría"
            }
            
            # Mapeo de enfoques
            enfoque_label = "Cualitativo" if enfoque.lower() == "cual" else "Cuantitativo"
            
            # Mapeo de tipos para filtrado
            tipo_filtro = {
                "informe": "Inv. Formativa",
                "proyecto": "Tesis",
                "maestria": "Suficiencia"
            }
            
            return {
                "id": f"unac-{tipo}-{enfoque}",
                "uni": "UNAC",
                "uni_code": "unac",
                "tipo": tipo_filtro.get(tipo, "Otros"),
                "titulo": f"{tipo_labels.get(tipo, tipo)} - {enfoque_label}",
                "facultad": "Centro de Formatos UNAC",
                "escuela": "Dirección Académica",
                "estado": "VIGENTE",
                "version": data.get("version", "1.0.0"),
                "fecha": "2026-01-17",
                "resumen": data.get("descripcion", f"Plantilla oficial de {tipo_labels.get(tipo, tipo)} con enfoque {enfoque_label}"),
                "tipo_formato": tipo,
                "enfoque": enfoque,
            }
        except Exception as e:
            print(f"[WARN] Error cargando {json_path}: {e}")
            return None

    def list_formatos(self):
        """Lee los 6 archivos JSON de los subdirectorios de app/data/unac/"""
        formatos = []
        data_dir = get_data_dir(self.code)
        
        # Estructura esperada: app/data/unac/{tipo}/{archivo}.json
        tipos_estructura = {
            "informe": ["cual", "cuant"],
            "maestria": ["cual", "cuant"],
            "proyecto": ["cual", "cuant"],
        }
        
        for tipo, enfoques in tipos_estructura.items():
            tipo_dir = data_dir / tipo
            
            if not tipo_dir.exists():
                continue
                
            for enfoque in enfoques:
                json_file = tipo_dir / f"unac_{tipo}_{enfoque}.json"
                
                if json_file.exists():
                    formato = self._load_format_from_json(json_file, tipo, enfoque)
                    if formato:
                        formatos.append(formato)
        
        return formatos

    def list_alerts(self):
        path = get_data_dir(self.code) / "alerts.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def get_formato(self, format_id: str):
        for f in self.list_formatos():
            if f.get("id") == format_id:
                return f
        return None


PROVIDER = UNACProvider()

```

---

## app/universities/uni/provider.py
**Tama?o:** 979
**SHA256:** 2b0402907c494ad7d3ac288fabd448dc02115344e1d9940a1cf28491a516073f
**Tipo:** python

```python
from pathlib import Path
import json

from app.core.loaders import get_data_dir

class UNIProvider:
    code = "uni"
    display_name = "UNI"
    name = display_name

    def get_data_dir(self) -> Path:
        return get_data_dir(self.code)

    def get_generator_for_category(self, category: str):
        category = (category or "").strip().lower()
        raise ValueError(f"generator not available for category {category}")

    def list_formatos(self):
        path = get_data_dir(self.code) / "formatos.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def list_alerts(self):
        path = get_data_dir(self.code) / "alerts.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def get_formato(self, format_id: str):
        for f in self.list_formatos():
            if f.get("id") == format_id:
                return f
        return None


PROVIDER = UNIProvider()

```

---

## console.log('Estructura
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** other

```

```

---

## data/seed/alerts.sample.json
**Tama?o:** 538
**SHA256:** 0c7587495717687d9ac4a89c4c4ece0b415708046c2200bd2771f3c1ae561031
**Tipo:** json

```json
[
  {
    "id": "apa7-update",
    "titulo": "Actualización Normas APA 7",
    "cuerpo": "A partir del ciclo 2024-1, todos los trabajos deben adherirse a la 7ma edición.",
    "cuando": "Hace 2 horas",
    "nivel": "IMPORTANTE",
    "relacionado_id": "unac-fiee-plan-tesis"
  },
  {
    "id": "mantenimiento",
    "titulo": "Mantenimiento Programado",
    "cuerpo": "La plataforma no estará disponible este domingo de 02:00 AM a 04:00 AM.",
    "cuando": "Ayer",
    "nivel": "INFO",
    "relacionado_id": null
  }
]

```

---

## data/seed/formatos.sample.json
**Tama?o:** 1519
**SHA256:** 78efe9470db0bbf59f699db479eef4f2e2ad067b37a635c978950a11887911b9
**Tipo:** json

```json
[
  {
    "id": "unac-fiee-plan-tesis",
    "uni": "UNAC",
    "tipo": "Tesis",
    "titulo": "Estructura Plan de Tesis FIEE",
    "facultad": "Ingeniería Eléctrica y Electrónica",
    "escuela": "Ing. Sistemas",
    "estado": "VIGENTE",
    "version": "2.4",
    "fecha": "2024-05-12",
    "resumen": "Documento oficial que detalla la estructura capitular requerida para el plan de tesis.",
    "archivos": [
      {
        "tipo": "DOCX",
        "nombre": "plan_tesis_fiee.docx"
      }
    ],
    "historial": [
      {
        "version": "2.4",
        "fecha": "2024-05-12",
        "estado": "VIGENTE",
        "nota": "Ajuste de márgenes y logo."
      },
      {
        "version": "2.3",
        "fecha": "2024-02-10",
        "estado": "ANTERIOR",
        "nota": "Corrección ortográfica."
      }
    ]
  },
  {
    "id": "uni-civil-suficiencia",
    "uni": "UNI",
    "tipo": "Suficiencia",
    "titulo": "Formato Informe de Suficiencia",
    "facultad": "Ingeniería Civil",
    "escuela": "Modalidad profesional",
    "estado": "VIGENTE",
    "version": "1.1",
    "fecha": "2024-01-10",
    "resumen": "Formato para titulación por modalidad profesional.",
    "archivos": [
      {
        "tipo": "PDF",
        "nombre": "informe_suficiencia.pdf"
      }
    ],
    "historial": [
      {
        "version": "1.1",
        "fecha": "2024-01-10",
        "estado": "VIGENTE",
        "nota": "Ajustes de portada."
      }
    ]
  }
]

```

---

## docs/_after_legacy_only_cleanup/hashes.json
**Tama?o:** 4780
**SHA256:** dab3f1cf0aa8a3ae3a115c9ebf060649cddde6e954afeee9d05d76dd44075475
**Tipo:** json

```json
{
  "UNAC_informe_cual.docx": {
    "word/document.xml": "d234b05b7fc87bb544025a55845ca3349e83ed57daa36764c04fd52720876262",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/_rels/document.xml.rels": "e101ebe4076bc3d4946833690e6de385032c17649c27041fc8b6dd617d3e36a7",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_informe_cuant.docx": {
    "word/document.xml": "6ba0cbe2fcb3734a7ef34087bcba26b14fdf36fe44ca2e2c2cd1dfe93cae2aa1",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/_rels/document.xml.rels": "e101ebe4076bc3d4946833690e6de385032c17649c27041fc8b6dd617d3e36a7",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_maestria_cual.docx": {
    "word/document.xml": "83abe43ce6d7d5417879780b8ff6f2525150e7f4f805cebaa9c1ebabec733ee1",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/_rels/document.xml.rels": "d892506582ee43128f5e3f2394d6b33226ed364b7caeb1e90d3b0e6c477e85bf",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_maestria_cuant.docx": {
    "word/document.xml": "38403e7358f0fec3d8e0951404a88b27ce3ace468c1873cc86ff845295711ea8",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/_rels/document.xml.rels": "d892506582ee43128f5e3f2394d6b33226ed364b7caeb1e90d3b0e6c477e85bf",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_proyecto_cual.docx": {
    "word/document.xml": "0b214b9f25707b166ecc96a0af60eb83d3764b22fda32f7c55ca926e4a7ebfd3",
    "word/styles.xml": "cbfb5529a485f7fd21c9182d3e085c1a0bd873a4656484d21eae82f975aa7ad7",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "51a0d348fe85965c66e4748a03c3c0d055d78455514f03cb121c334af7d73689",
    "word/_rels/document.xml.rels": "52f49521e6a1a0cc4c89e6f55b680980a66d3ea96a3128f8819aa47a6fd5175d",
    "word/footer1.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_proyecto_cuant.docx": {
    "word/document.xml": "862b5ac7223c1677860c2cdf172e1b3fdbf88605cdd4501034218e47c36f9edc",
    "word/styles.xml": "cbfb5529a485f7fd21c9182d3e085c1a0bd873a4656484d21eae82f975aa7ad7",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "51a0d348fe85965c66e4748a03c3c0d055d78455514f03cb121c334af7d73689",
    "word/_rels/document.xml.rels": "52f49521e6a1a0cc4c89e6f55b680980a66d3ea96a3128f8819aa47a6fd5175d",
    "word/footer1.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  }
}
```

---

## docs/_after_multi_universidad/hashes.json
**Tama?o:** 4780
**SHA256:** dab3f1cf0aa8a3ae3a115c9ebf060649cddde6e954afeee9d05d76dd44075475
**Tipo:** json

```json
{
  "UNAC_informe_cual.docx": {
    "word/document.xml": "d234b05b7fc87bb544025a55845ca3349e83ed57daa36764c04fd52720876262",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/_rels/document.xml.rels": "e101ebe4076bc3d4946833690e6de385032c17649c27041fc8b6dd617d3e36a7",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_informe_cuant.docx": {
    "word/document.xml": "6ba0cbe2fcb3734a7ef34087bcba26b14fdf36fe44ca2e2c2cd1dfe93cae2aa1",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/_rels/document.xml.rels": "e101ebe4076bc3d4946833690e6de385032c17649c27041fc8b6dd617d3e36a7",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_maestria_cual.docx": {
    "word/document.xml": "83abe43ce6d7d5417879780b8ff6f2525150e7f4f805cebaa9c1ebabec733ee1",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/_rels/document.xml.rels": "d892506582ee43128f5e3f2394d6b33226ed364b7caeb1e90d3b0e6c477e85bf",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_maestria_cuant.docx": {
    "word/document.xml": "38403e7358f0fec3d8e0951404a88b27ce3ace468c1873cc86ff845295711ea8",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/_rels/document.xml.rels": "d892506582ee43128f5e3f2394d6b33226ed364b7caeb1e90d3b0e6c477e85bf",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_proyecto_cual.docx": {
    "word/document.xml": "0b214b9f25707b166ecc96a0af60eb83d3764b22fda32f7c55ca926e4a7ebfd3",
    "word/styles.xml": "cbfb5529a485f7fd21c9182d3e085c1a0bd873a4656484d21eae82f975aa7ad7",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "51a0d348fe85965c66e4748a03c3c0d055d78455514f03cb121c334af7d73689",
    "word/_rels/document.xml.rels": "52f49521e6a1a0cc4c89e6f55b680980a66d3ea96a3128f8819aa47a6fd5175d",
    "word/footer1.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_proyecto_cuant.docx": {
    "word/document.xml": "862b5ac7223c1677860c2cdf172e1b3fdbf88605cdd4501034218e47c36f9edc",
    "word/styles.xml": "cbfb5529a485f7fd21c9182d3e085c1a0bd873a4656484d21eae82f975aa7ad7",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/settings.xml": "51a0d348fe85965c66e4748a03c3c0d055d78455514f03cb121c334af7d73689",
    "word/_rels/document.xml.rels": "52f49521e6a1a0cc4c89e6f55b680980a66d3ea96a3128f8819aa47a6fd5175d",
    "word/footer1.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  }
}
```

---

## docs/_baseline_legacy_only_cleanup/hashes.json
**Tama?o:** 4780
**SHA256:** bcc604562c94ed335c52cee8cbf92ad2458cff3a014d6f21719d50f946ebce53
**Tipo:** json

```json
{
  "UNAC_informe_cual.docx": {
    "word/document.xml": "d234b05b7fc87bb544025a55845ca3349e83ed57daa36764c04fd52720876262",
    "word/_rels/document.xml.rels": "e101ebe4076bc3d4946833690e6de385032c17649c27041fc8b6dd617d3e36a7",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_informe_cuant.docx": {
    "word/document.xml": "6ba0cbe2fcb3734a7ef34087bcba26b14fdf36fe44ca2e2c2cd1dfe93cae2aa1",
    "word/_rels/document.xml.rels": "e101ebe4076bc3d4946833690e6de385032c17649c27041fc8b6dd617d3e36a7",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_maestria_cual.docx": {
    "word/document.xml": "83abe43ce6d7d5417879780b8ff6f2525150e7f4f805cebaa9c1ebabec733ee1",
    "word/_rels/document.xml.rels": "d892506582ee43128f5e3f2394d6b33226ed364b7caeb1e90d3b0e6c477e85bf",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_maestria_cuant.docx": {
    "word/document.xml": "38403e7358f0fec3d8e0951404a88b27ce3ace468c1873cc86ff845295711ea8",
    "word/_rels/document.xml.rels": "d892506582ee43128f5e3f2394d6b33226ed364b7caeb1e90d3b0e6c477e85bf",
    "word/styles.xml": "389f10e4902828063b39c193011c2123e2e8a8cd36ef0f035d9245d332aec44a",
    "word/settings.xml": "065cc17f7b5a87a7fdde4ef407061b9c61e56df8e53c858f94f0d7b1d9153a0b",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/footer1.xml": "cc831c46cac03c968fc5b2d8e0ce3179d17a559dd54fa4e4fba3f7c2680cc344",
    "word/footer2.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer3.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c",
    "word/footer4.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_proyecto_cual.docx": {
    "word/document.xml": "0b214b9f25707b166ecc96a0af60eb83d3764b22fda32f7c55ca926e4a7ebfd3",
    "word/_rels/document.xml.rels": "52f49521e6a1a0cc4c89e6f55b680980a66d3ea96a3128f8819aa47a6fd5175d",
    "word/styles.xml": "cbfb5529a485f7fd21c9182d3e085c1a0bd873a4656484d21eae82f975aa7ad7",
    "word/settings.xml": "51a0d348fe85965c66e4748a03c3c0d055d78455514f03cb121c334af7d73689",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/footer1.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  },
  "UNAC_proyecto_cuant.docx": {
    "word/document.xml": "862b5ac7223c1677860c2cdf172e1b3fdbf88605cdd4501034218e47c36f9edc",
    "word/_rels/document.xml.rels": "52f49521e6a1a0cc4c89e6f55b680980a66d3ea96a3128f8819aa47a6fd5175d",
    "word/styles.xml": "cbfb5529a485f7fd21c9182d3e085c1a0bd873a4656484d21eae82f975aa7ad7",
    "word/settings.xml": "51a0d348fe85965c66e4748a03c3c0d055d78455514f03cb121c334af7d73689",
    "word/numbering.xml": "70976f19cbcd896e51890859fe6ecb3467a5a7ad0c040160fedc5a1993cb09ce",
    "word/footer1.xml": "b43cf378f96a3128c4d18c21b739781dd27fb58b272601dd6c8a6f385d042b3c"
  }
}
```

---

## docs/CONTRIBUTING.md
**Tama?o:** 730
**SHA256:** 9c77a388af3851dbdac9ef7b44e4d8ba0cd24587a204caaf84e63dfd7d0f7c22
**Tipo:** doc

```markdown
# Guía rápida para contribuir

## Flujo recomendado (equipo)
1) Actualiza tu repo:
```bash
git checkout main
git pull
```

2) Crea tu rama por módulo:
```bash
git checkout -b feature/<modulo>
```

3) Trabaja solo en tus archivos (ideal):
- `app/modules/<modulo>/...`
- `app/templates/pages/<pagina>.html`

4) Commit y PR:
```bash
git add .
git commit -m "Implementa base de <modulo>"
git push -u origin feature/<modulo>
```

## Nombres de ramas (ejemplos)
- `feature/catalog`
- `feature/detail`
- `feature/alerts`
- `feature/admin`
- `chore/refactor-templates`

## Estándar de commits
- `feat: ...` nueva función
- `fix: ...` bug
- `chore: ...` mantenimiento
- `docs: ...` documentación

```

---

## docs/GUIA_ESCALABILIDAD_UNIVERSIDADES.md
**Tama?o:** 2464
**SHA256:** 967da7a841b354b91bed761e1e898bb2e240a9a599519e2ebe15ee990d0d516d
**Tipo:** doc

```markdown
# Guia de escalabilidad multi-universidad

Esta guia describe como agregar universidades y formatos sin tocar el core ni los modulos.

## 1) Agregar una universidad nueva

1. Crear carpeta en `app/universities/<codigo>/`.
2. Implementar `app/universities/<codigo>/provider.py` y exponer `PROVIDER` (o `get_provider()`).
3. Cumplir el contrato de `app/universities/contracts.py`:
   - `code`: slug ASCII (ej: `unac`, `uni`).
   - `display_name`: nombre visible (puede tener tildes).
   - `get_data_dir()`: debe retornar `app/data/<code>`.
   - `get_generator_for_category(category)`: retornar `Path` del generador por categoria
     (o una lista de comandos), o lanzar error si no existe.

Ejemplo minimo:

```python
from pathlib import Path
from app.core.loaders import get_data_dir

class XYZProvider:
    code = "xyz"
    display_name = "Universidad XYZ"

    def get_data_dir(self) -> Path:
        return get_data_dir(self.code)

    def get_generator_for_category(self, category: str) -> Path:
        base = Path(__file__).resolve().parent / "centro_formatos"
        mapping = {
            "informe": "generador_informe_tesis.py",
            "maestria": "generador_maestria.py",
            "proyecto": "generador_proyecto_tesis.py",
        }
        if category not in mapping:
            raise ValueError(f"generator not available for category {category}")
        return base / mapping[category]

PROVIDER = XYZProvider()
```

El registry detecta automaticamente `provider.py` sin imports estaticos.

## 2) Agregar un formato nuevo (solo JSON)

Crear un archivo JSON en:

```
app/data/<uni>/<categoria>/
```

Ejemplos:

```
app/data/unac/informe/unac_informe_cual.json
app/data/unac/maestria/unac_maestria_cuant.json
```

No se requiere cambiar JS ni Python. El discovery lo detecta automaticamente.

## 3) Convenciones de nombres

- IDs y slugs: ASCII y en minuscula.
- Titulos visibles: pueden incluir tildes (ej: "Maestria").
- Categoria: nombre de la carpeta inmediata (ej: `informe`, `proyecto`, `maestria`).
- Enfoque: se deriva del nombre del archivo (cual/cuant/general).
- `format_id` global: se normaliza como `<uni>-<categoria>-<enfoque>` o se deriva del filename
  (siempre unico).

## 4) Generadores DOCX

- Se mantienen por categoria (no por formato).
- El core llama al generador segun `get_generator_for_category(category)`.
- Si una universidad no tiene generador, debe lanzar:
  `generator not available for category <categoria>`.


```

---

## docs/REPORTE_LEGACY_ONLY_CLEANUP.md
**Tama?o:** 4474
**SHA256:** 2cf77fdf512bffdb2ce3bb4bc54b7546d5db1b99e99cd633536699c1203d2e8c
**Tipo:** doc

```markdown
﻿# 1) Qué se eliminó (lista completa “spec”)
- app/static/js/format-viewer.js: removidas las rutas de render “spec” (`isSpecFormat`, `buildStructureFromSpec`, `findChapterInSpec`, `getCoverFromSpec`) y las ramas condicionales que las usaban en carátula/índice/capítulos.
- app/static/js/format-viewer.js: eliminado el hidratado de requisitos exclusivo de spec (capítulos desde `data.content.chapters`).
- app/core/loaders.py: eliminado el filtro por carpeta `_spec_backup` (no hay backups spec; discovery queda 100% legacy).
- Búsqueda de `schema_version`, `page_setup`, `legacy_to_spec`, `spec_to_legacy`, `preliminaries`, `isSpecFormat`: sin resultados en código; coincidencias restantes son texto “específicos” en JSONs (no relacionadas a schema).

# 2) Cambios por archivo (qué, por qué)
- app/static/js/format-viewer.js: simplificado a flujo legacy único (carátula/preliminares/cuerpo/finales), removidas funciones spec y duplicados de hidratación; mantiene UI y previews sin cambiar estructura visual.
- app/core/loaders.py: se quitó el filtro `_spec_backup` para eliminar toda referencia “spec” en discovery.
- app/main.py: middleware que fuerza `charset=utf-8` para `text/*`, `application/json` y `application/javascript`, asegurando decodificación correcta de acentos en UI.
- docs/_after_legacy_only_cleanup/*.docx: generación post-limpieza para comparación.
- docs/_after_legacy_only_cleanup/hashes.json: hashes SHA256 de XML internos clave para verificación de igualdad.

# 3) Evidencia de que todo es legacy (ejemplos de JSON keys)
Top-level keys reales por archivo (legacy):
- app/data/unac/informe/unac_informe_cual.json: `caratula`, `preliminares`, `cuerpo`, `finales`, `matriz_consistencia`, `version`, `descripcion`.
- app/data/unac/informe/unac_informe_cuant.json: `caratula`, `preliminares`, `cuerpo`, `finales`, `matriz_consistencia`, `version`, `descripcion`.
- app/data/unac/proyecto/unac_proyecto_cual.json: `configuracion`, `caratula`, `pagina_respeto`, `informacion_basica`, `preliminares`, `cuerpo`, `finales`, `matriz_consistencia`.
- app/data/unac/proyecto/unac_proyecto_cuant.json: `configuracion`, `caratula`, `pagina_respeto`, `informacion_basica`, `preliminares`, `cuerpo`, `finales`, `matriz_consistencia`.
- app/data/unac/maestria/unac_maestria_cual.json: `caratula`, `preliminares`, `cuerpo`, `finales`, `version`, `descripcion`, `informacion_basica`.
- app/data/unac/maestria/unac_maestria_cuant.json: `caratula`, `preliminares`, `cuerpo`, `finales`, `version`, `descripcion`, `informacion_basica`.

No se encontraron claves `schema_version`, `page_setup`, `preliminaries` (spec) en los JSON legacy.

# 4) Fix encoding “Maestr??a” (origen y corrección)
- Origen probable: respuestas de recursos de texto sin `charset`, lo que puede hacer que el navegador interprete UTF-8 como otra codificación (acentos corruptos en UI).
- Corrección aplicada: middleware en app/main.py que fuerza `charset=utf-8` para HTML/JS/JSON.
- Verificación de soporte UTF-8: templates ya incluyen `<meta charset="UTF-8">` y lectura de JSON usa `encoding="utf-8"` en loaders/servicios.

# 5) Verificación DOCX (tabla baseline vs after con OK/DIFF)
Archivos comparados: `word/document.xml`, `word/styles.xml`, `word/numbering.xml`, `word/settings.xml`, `word/_rels/document.xml.rels`, `word/header*.xml`, `word/footer*.xml`.

| Documento | Baseline | After | Resultado |
| --- | --- | --- | --- |
| UNAC_informe_cual.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_informe_cuant.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_proyecto_cual.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_proyecto_cuant.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_maestria_cual.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |
| UNAC_maestria_cuant.docx | docs/_baseline_legacy_only_cleanup/hashes.json | docs/_after_legacy_only_cleanup/hashes.json | OK |

# 6) Checklist final
- [x] Eliminada toda lógica “spec” en frontend y discovery.
- [x] Backend opera solo con schema legacy.
- [x] Encoding UTF-8 garantizado en respuestas HTML/JS/JSON.
- [x] DOCX (6 formatos) idénticos a baseline (hashes OK).

```

---

## r.json())
**Tama?o:** 0
**SHA256:** e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
**Tipo:** other

```

```

---

## README.md
**Tama?o:** 1166
**SHA256:** 29232be1a3cd30fcb433d21c823c6900946c4a73c4a80f80a4f765537e4964ea
**Tipo:** doc

```markdown
# Formatoteca

Este repositorio es una estructura base en **Python + FastAPI + Jinja2** para una “biblioteca de formatos de tesis”.
La idea es que cada colaborador tome un **módulo** (Catálogo, Detalle, Alertas, etc.) y lo complete mediante Pull Requests.

## Ejecutar (local)
# Windows: 
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
# Visual Code:
pip install -r requirements.txt
python uvicorn app.main:app --reload

Luego abre:
- Home: http://127.0.0.1:8000/
- Catálogo: http://127.0.0.1:8000/catalog
- Alertas: http://127.0.0.1:8000/alerts

## Estructura
- `app/modules/home/` -> Inicio
- `app/modules/catalog/` -> Catálogo + filtros (placeholder)
- `app/modules/formats/` -> Detalle + versiones (placeholder)
- `app/modules/alerts/` -> Notificaciones (placeholder)
- `app/modules/admin/` -> Panel Admin (placeholder)
- `app/templates/` -> HTML (Jinja). Cada pantalla está en `templates/pages/`.
- `data/seed/` -> JSON de ejemplo (para que la UI tenga contenido sin BD).

## Reglas
- No hacer push directo a `main`.
  
## Mockup original
Está guardado en `ui/mockup/index.html` como referencia visual.

```

---

## REFACTORING_SUMMARY.md
**Tama?o:** 7135
**SHA256:** 5683f7e00106533e804d7bc395f4670b32ab82d4917fd08315f3078a8bdc539f
**Tipo:** doc

```markdown
# Refactorización Arquitectónica - Separación de Responsabilidades

## 📋 Resumen de cambios

Se ha refactorizado la arquitectura de la aplicación para seguir correctamente el patrón **MVC (Model-View-Controller)** con separación de responsabilidades entre **Router** (orquestación HTTP) y **Service** (lógica de negocio).

---

## ✅ Archivos creados

### 1. `app/core/loaders.py` (NUEVO)
**Responsabilidad**: Funciones compartidas de acceso a datos

```python
- load_json_file(file_path) → Carga y valida archivos JSON
- get_data_dir() → Retorna ruta a directorio de datos
```

**Por qué**: 
- Elimina duplicación de código
- Centraliza la lógica de lectura de archivos
- Ambos módulos (catalog, formats) ahora usan la misma función

---

## 🔄 Archivos refactorizados

### 2. `app/modules/catalog/router.py`
**ANTES**: Router contenía lógica de negocio (`_load_format_from_json`, `_get_formatos_unac`)
**AHORA**: Router solo orquesta HTTP

```python
@router.get("/catalog")
async def get_catalog(request):
    formatos = service.get_all_formatos()  # Delegado al service
    return templates.TemplateResponse(...)
```

**Cambios**:
- ❌ Eliminadas funciones `_load_format_from_json()` y `_get_formatos_unac()`
- ✅ Llamada a `service.get_all_formatos()`
- ✅ Router solo maneja HTTP, no lógica

---

### 3. `app/modules/catalog/service.py`
**ANTES**: Service contenía solo lógica de generación de documentos
**AHORA**: Service contiene toda la lógica de negocio del módulo

```python
def get_all_formatos() -> List[Dict]:
    """Carga los 6 formatos desde JSONs"""
    # Lee todos los JSONs en app/data/unac/
    # Transforma datos
    # Retorna lista de formatos
```

**Cambios**:
- ✅ Nueva función `get_all_formatos()` - Carga y transforma datos
- ✅ Importa de `app.core.loaders` en lugar de reimplementar
- ❌ Eliminadas funciones `_load_format_from_json()` y `_get_formatos_unac()`
- ✅ Mantiene `generate_document()` para generación de documentos

---

### 4. `app/modules/formats/router.py`
**ANTES**: Router contenía lógica de búsqueda (`_load_format_from_json`, `_get_formato`)
**AHORA**: Router solo orquesta HTTP

```python
@router.get("/{format_id}")
async def get_format_detail(format_id: str, request):
    formato = service.get_formato(format_id)  # Delegado al service
    return templates.TemplateResponse(...)
```

**Cambios**:
- ❌ Eliminadas funciones `_load_format_from_json()` y `_get_formato()`
- ✅ Llamada a `service.get_formato(format_id)`
- ✅ Router solo maneja HTTP, no lógica

---

### 5. `app/modules/formats/service.py`
**ANTES**: Service no se usaba (función `get_formato()` nunca era llamada)
**AHORA**: Service contiene la lógica completa

```python
def get_formato(format_id: str) -> Dict:
    """
    Busca un formato específico por ID
    Ejemplo: "unac-proyecto-cual"
    """
    # Parsea el ID
    # Lee el JSON específico
    # Transforma y retorna datos
```

**Cambios**:
- ✅ Implementación completa de `get_formato()`
- ✅ Usa `load_json_file()` y `get_data_dir()` del core
- ✅ Manejo de errores con excepciones

---

## 🎯 Diagrama de flujo - ANTES vs DESPUÉS

### ❌ ANTES (Incorrecto)
```
Cliente HTTP
    ↓
Router (contiene lógica)
    ├─ Abre archivos
    ├─ Lee JSONs
    ├─ Transforma datos
    └─ Retorna a vista
    
Service (no se usa)
    ├─ get_formato() nunca llamado
    └─ Código duplicado aquí
```

### ✅ DESPUÉS (Correcto)
```
Cliente HTTP
    ↓
Router (solo orquesta)
    ↓
Service (contiene lógica)
    ├─ Parsea parámetros
    ├─ Llama core.loaders
    ├─ Transforma datos
    └─ Retorna resultado
    ↓
Core Loaders (código compartido)
    ├─ load_json_file()
    └─ get_data_dir()
```

---

## 📊 Comparativa de Responsabilidades

| Capa | ANTES | DESPUÉS |
|------|-------|---------|
| **Router** | HTTP + Lógica | ✅ Solo HTTP |
| **Service** | Parcial/No usado | ✅ Toda la lógica |
| **Core** | No existía | ✅ Funciones compartidas |
| **Duplicación** | Sí (40+ líneas en 2 routers) | ✅ No (código centralizado) |

---

## 🔧 Cómo funciona ahora

### Flujo de Catalog (Obtener 6 formatos)
```python
# Router recibe GET /catalog
router.get("/catalog"):
    formatos = service.get_all_formatos()  # Llama service
    return template.render(formatos)

# Service contiene la lógica
service.get_all_formatos():
    para cada tipo (informe, maestria, proyecto):
        para cada enfoque (cual, cuant):
            data = loaders.load_json_file()  # Carga JSON
            formatos.append(transformar(data))
    return formatos

# Loaders son compartidos
loaders.load_json_file(path):
    return json.load(path)  # Centralizado
```

### Flujo de Formats (Obtener 1 formato específico)
```python
# Router recibe GET /formatos/unac-proyecto-cual
router.get("/{format_id}"):
    formato = service.get_formato(format_id)  # Llama service
    return template.render(formato)

# Service contiene la lógica
service.get_formato(format_id):
    tipo, enfoque = parsear_id(format_id)
    data = loaders.load_json_file(path)  # Carga JSON
    return transformar(data)

# Loaders son compartidos
loaders.load_json_file(path):
    return json.load(path)  # Mismo código
```

---

## 🚀 Beneficios

| Beneficio | Descripción |
|-----------|-------------|
| **DRY (Don't Repeat Yourself)** | Eliminada duplicación de código en loaders |
| **Mantenibilidad** | Cambios en lógica solo se hacen en un lugar (service) |
| **Testabilidad** | Service puede testearse sin HTTP |
| **Escalabilidad** | Nuevos módulos pueden reutilizar core.loaders |
| **Separación de Responsabilidades** | Router ≠ Service ≠ Data Access |
| **Errores claros** | Service lanza excepciones, Router las maneja |

---

## ✨ Código Limpio

**Antes**:
- 40+ líneas de `_load_format_from_json()` en `catalog/router.py`
- 40+ líneas de `_load_format_from_json()` en `formats/router.py`
- `_get_formato()` en `formats/router.py` sin usar `formats/service.py`
- Total: ~120 líneas duplicadas

**Después**:
- 12 líneas en `app/core/loaders.py` (compartido)
- Cada router: 2-3 llamadas a service
- Total: ~25 líneas de código único

---

## 📝 Nota sobre migración

Los archivos fueron refactorizados pero el comportamiento HTTP es idéntico:
- `/catalog` sigue mostrando 6 formatos
- `/formatos/{format_id}` sigue mostrando detalle
- Los datos JSONs siguen en `app/data/unac/`

---

## 🎓 Lecciones de arquitectura

Esta refactorización demuestra:

1. **Separación de capas**: Router (HTTP), Service (Negocio), Core (Datos)
2. **DRY Principle**: Una sola fuente de verdad para cada lógica
3. **Inyección de dependencias**: Router depende de Service
4. **Manejo de errores**: Service lanza excepciones, Router las traduce
5. **Reutilización de código**: `core.loaders` usado por ambos módulos


```

---

## requirements.txt
**Tama?o:** 93
**SHA256:** ef034cf964fa295545eeaac2248d1abdae698f23a85b8ebb35792ba1809d982d
**Tipo:** doc

```text
fastapi==0.115.0
uvicorn[standard]==0.30.6
jinja2==3.1.4
pydantic
python-docx
docx2pdf

```

---

## test_data.py
**Tama?o:** 1757
**SHA256:** 8e498ee6e8a115df887b6a4f303e0ea18e8d2eba0a89a5b13a0f4f637bad7403
**Tipo:** python

```python
#!/usr/bin/env python
"""Test script to verify catalog data loading."""
import sys
from pathlib import Path
from app.modules.catalog.service import get_all_formatos
from app.modules.formats.service import get_formato

def test_catalog():
    """Test catalog service."""
    print("=" * 60)
    print("Testing Catalog Service")
    print("=" * 60)
    
    try:
        formatos = get_all_formatos()
        print(f"✓ Loaded {len(formatos)} formatos")
        
        for i, f in enumerate(formatos, 1):
            print(f"\n{i}. {f['titulo']}")
            print(f"   ID: {f['id']}")
            print(f"   Tipo: {f['tipo']}")
            print(f"   Estado: {f['estado']}")
            print(f"   Versión: {f['version']}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_formats():
    """Test formats service."""
    print("\n" + "=" * 60)
    print("Testing Formats Service")
    print("=" * 60)
    
    test_ids = [
        "unac-informe-cual",
        "unac-proyecto-cuant",
        "unac-maestria-cual"
    ]
    
    for format_id in test_ids:
        try:
            formato = get_formato(format_id)
            print(f"✓ {format_id}")
            print(f"  Título: {formato['titulo']}")
            print(f"  Versión: {formato['version']}")
        except Exception as e:
            print(f"✗ {format_id}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = test_catalog() and test_formats()
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Tests failed!")
        sys.exit(1)

```

---

## ui/mockup/index.html
**Tama?o:** 70
**SHA256:** a91b323ef77d5cfecefb00739418089904c8a86e91ff2c938e6fc6265bc8d804
**Tipo:** html

```html
<!-- Mockup original: pega aquí tu HTML completo de referencia. -->

```

---

## ui/mockup/README.txt
**Tama?o:** 90
**SHA256:** eccb1387dc35dadd9a03892666ccd979dc5066621674c93ccf538e2bcffe24ff
**Tipo:** doc

```text
Pega aquí tu mockup original (index.html) si deseas conservarlo como referencia visual.

```

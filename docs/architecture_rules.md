# Reglas de Arquitectura: Motor de Renderizado (GicaTesis)

Este documento define las reglas de oro para mantener el motor de GicaTesis robusto y compatible con los datos provenientes de GicaGen.

## 1. Regla de Identidad Inamovible (Identity Preservation)
**La clave `_meta` en la raíz del JSON NUNCA debe ser eliminada durante el preprocesamiento.**
- **Razón**: El `Normalizer` utiliza `_meta.id` para decidir qué renderizador institucional invocar (ej: UNAC vs San Marcos). Si se elimina, el motor usa un renderizador genérico que no tiene los fallbacks ni la lógica específica, haciendo que el documento se vea incompleto.
- **Implementación**: La función `exclude_instruction_keys` en `preprocessor.py` NO debe incluir `_meta` ni `version` en su lista de exclusión.

## 2. Patrón de Renderizado Proactivo (Flexible Search)
Los renderizadores de bloques institucionales (Carátula, Información Básica) no deben depender de una única ruta de datos fija.
- **Implementación**: Usar el patrón `_find_val(key, default)` que busca de forma secuencial en:
    1. El bloque específico (ej: `caratula`).
    2. La raíz del objeto `data`.
    3. El diccionario `values`.
- **Ventaja**: Esto permite absorber cambios en la estructura de GicaGen sin romper el renderizado del documento.

## 3. Regla de Redundancia de Metadatos
El `preprocessor.py` debe inyectar metadatos críticos de forma redundante tanto en secciones específicas como en la raíz del objeto global.
- **Campos críticos**: Autores, Asesores, Título, Línea de Investigación, Año y Lugar.

## 4. Inyección de IA Estructural
Las secciones especiales como "Información Básica" deben soportar un campo `_ai_content` que renderiza contenido plano generado por IA sin necesidad de que el usuario lo mapee manualmente en cada placeholder.

## 5. Regla de Comunicación Ejecutiva (Reporting)
Para informes de avance y resúmenes de actividad dirigidos a stakeholders:
- **Formato**: Entregar siempre la información en **exactamente 3 puntos**.
- **Lenguaje**: Usar **lenguaje no técnico**, enfocado en el valor de negocio o progreso del trabajo, evitando términos internos de programación.
- **Contexto**: Los resúmenes deben estar listos para ser copiados directamente en un **informe de trabajo**.

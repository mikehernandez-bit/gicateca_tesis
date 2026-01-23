# REPORTE_REFERENCIAS_CONTENIDO_Y_FORMATO_FINAL

Fecha: 2026-01-23

## 1) Archivos modificados

- `app/data/references/apa7.json`
- `app/data/references/ieee.json`
- `app/data/references/iso690.json`
- `app/data/references/vancouver.json`
- `app/data/unac/references.json`
- `app/data/uni/references.json`
- `app/static/js/references.js`
- `app/static/css/extra.css`
- `docs/REPORTE_REFERENCIAS_CONTENIDO_Y_FORMATO_FINAL.md`

## 2) Captura textual de ejemplos clave

APA 7 (lista con sangria francesa + doble espacio):
- “García, J. A., & Quispe, M. R. (2022). *Metodología de investigación aplicada*. Editorial Andina.”
- “López, M., & Rojas, P. (2022). Gestión del mantenimiento en plantas industriales. *Revista Peruana de Ingeniería*, 18(2), 33–48. https://doi.org/10.1234/rpi.2022.018”

IEEE (numerado alineado):
- [1] “J. A. García and M. R. Quispe, *Metodología de investigación aplicada*, 2nd ed. Editorial Andina, 2022.”
- [2] “L. Pérez, “Estrategias de análisis cuantitativo,” *Revista Peruana de Ingeniería*, vol. 18, no. 2, pp. 33–48, 2022, doi: 10.1234/rpi.2022.018.”

ISO 690 (autor-fecha + numérico):
- Autor-fecha: “García, J. A.; Quispe, M. R. 2022. *Metodología de investigación aplicada*. Editorial Andina.”
- Numérico: [1] “GARCÍA, J. A.; QUISPE, M. R. *Metodología de investigación aplicada*. Editorial Andina, 2022.”

Vancouver (numerado alineado):
- [1] “Ramos JA, Castillo MR. Adherencia terapéutica en pacientes crónicos. Rev Peru Salud. 2021;15(2):55-63.”
- [2] “García JA. Metodología de investigación clínica. 3a ed. Lima: Editorial Médica; 2020.”

## 3) Checklist de validación

- [x] Cards con descripciones concretas y preview corto.
- [x] APA 7 con sangría francesa + doble espacio (clase `.ref-apa7`).
- [x] IEEE/Vancouver con numeración alineada `[n]` (clases `.ref-numeric`, `.ref-row`, `.ref-num`).
- [x] ISO 690 muestra variante autor-fecha y variante numérica.
- [x] Renderer genérico por `item.tipo` (sin hardcode por norma).


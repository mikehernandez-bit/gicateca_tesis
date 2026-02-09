# Troubleshooting

## Problema 1: Formato no aparece en catálogo

### Síntomas
- El formato existe en `app/data/{uni}/{categoria}/` pero no se muestra en `/catalog`.

### Causas Posibles
1. **El archivo tiene keywords de referencias.**
2. **El archivo está en una carpeta ignorada.**
3. **El JSON tiene errores de sintaxis.**

### Qué Revisar

1. **Verificar nombre del archivo:**
   - NO debe contener: `references`, `referencias`, `bibliografia`.
   - **Fuente:** `app/core/loaders.py` L71-80

2. **Verificar carpeta:**
   - NO debe estar dentro de `references/` o `referencias/`.
   - NO debe comenzar con `_` o `__`.
   - **Fuente:** `app/core/loaders.py` L145-162

3. **Verificar JSON:**
   ```bash
   py -m json.tool app/data/unac/informe/archivo.json
   ```

4. **Verificar logs del servidor:**
   - Buscar "Warning: Could not load..."

---

## Problema 2: PDF no genera / Word COM falla

### Síntomas
- Error 500 al acceder a `/formatos/{id}/pdf`.
- Mensaje "No se pudo generar la vista previa".

### Causas Posibles
1. **Word no está instalado.**
2. **Word está colgado.**
3. **Error HRESULT -2147220995.**
4. **Timeout excedido.**

### Qué Revisar

1. **Verificar que Word esté instalado:**
   - Abrir Word manualmente.
   - Cerrar y reintentar.

2. **Verificar procesos de Word:**
   ```powershell
   Get-Process WINWORD
   ```
   Si hay procesos colgados:
   ```powershell
   Stop-Process -Name WINWORD -Force
   ```

3. **Revisar logs del servidor:**
   - Buscar "PDF conversion error" o "HRESULT".
   - **Fuente:** `app/core/pdf_converter.py` L123-128

4. **Aumentar timeout (si es documento grande):**
   ```bash
   set PDF_CONVERSION_TIMEOUT=300
   py -m uvicorn app.main:app --reload
   ```

---

## Problema 3: Vista previa de carátula se ve diferente a Word/PDF

### Síntomas
- El modal de carátula muestra datos diferentes al PDF.
- El logo no aparece o es incorrecto.
- Los campos están vacíos o tienen valores por defecto.

### Causas Posibles
0. **El modal de carátula no está unificado o el script no carga en orden.**
1. **El JSON no tiene la sección `caratula`.**
2. **Los campos tienen nombres diferentes a los esperados.**
3. **El logo no existe o la ruta es incorrecta.**
4. **Hay cache del navegador.**

### Qué Revisar

1. **Verificar estructura del JSON:**
   ```bash
   curl http://localhost:8000/formatos/{format_id}/data
   ```
   Buscar la sección `"caratula": {...}`.

2. **Verificar que el modal unificado esté incluido:**
   - `catalog.html` y `detail.html` deben incluir `components/cover_modal.html`.
   - `cover-preview.js` debe cargarse **antes** de `catalog.js` / `format-viewer.js`.
   - En consola: `window.GicaCover` debe existir.

3. **Verificar campos esperados:**
   - `universidad`, `facultad`, `escuela`
   - `titulo_placeholder` o `titulo`
   - `frase_grado`, `grado_objetivo`
   - `autor`, `asesor`
   - `pais` o `lugar_fecha`, `fecha`
   - **Fuente:** `app/static/js/cover-preview.js`

4. **Verificar logo:**
   - Prioridad: `data.configuracion.ruta_logo`
   - Fallback: `/static/assets/LogoUNAC.png` o `/static/assets/LogoUNI.png`
   - **Fuente:** `app/static/js/cover-preview.js`

5. **Limpiar cache del navegador:**
   - Ctrl+Shift+R (hard refresh).

**Archivos involucrados**
- `app/templates/components/cover_modal.html`
- `app/static/js/cover-preview.js`
- `app/templates/pages/catalog.html`
- `app/templates/pages/detail.html`

**Cómo probar**
1) Abrir `/catalog` → modo Carátulas → “Ver Carátula”.  
2) Abrir `/formatos/{id}` → “Carátula Institucional”.  
3) Confirmar que ambos modales muestran los mismos datos y logo.

---

## Problema 4: Mojibake (caracteres corruptos)

### Síntomas
- Texto como "é" en lugar de "é".
- El sistema muestra advertencias "[WARN] Posible mojibake...".

### Causas Posibles
- El archivo JSON fue guardado con encoding incorrecto.

### Qué Revisar

1. **Ejecutar script de detección:**
   ```bash
   py scripts/check_mojibake.py
   ```
   **Fuente:** `scripts/check_mojibake.py`

2. **Corregir encoding:**
   ```bash
   py scripts/fix_to_utf8.py
   ```
   **Fuente:** `scripts/fix_to_utf8.py`

3. **Verificar advertencias en logs:**
   - Buscar "[WARN] Posible mojibake".
   - **Fuente:** `app/core/loaders.py` L123-133

---

## Problema 5: Referencias no aparecen

### Síntomas
- La página `/referencias` no muestra normas.
- La API `/api/referencias` retorna lista vacía.

### Qué Revisar

1. **Verificar que existan archivos en `app/data/references/`:**
   - apa7.json, ieee.json, iso690.json, vancouver.json

2. **Verificar `references_config.json` de la universidad:**
   - El campo `enabled` debe incluir los IDs de las normas.
   - **Fuente:** `app/data/unac/references_config.json` L4

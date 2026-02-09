# Guía de Estilo y Encoding

> OBLIGATORIO: Reglas para mantener la integridad del repositorio y evitar problemas de encoding (mojibake).

## 1. Encoding

- **Todos los archivos DEBEN guardarse en UTF-8.**
- Evitar BOM (Byte Order Mark) si es posible.

## 2. Caracteres Prohibidos

- **Flechas Unicode:** No usar. **Usar ASCII:** `->`, `<-`
- **Emojis:** No usar. **Usar etiquetas:** `[X]`, `[OK]`
- **Box Drawing:** No usar. **Usar ASCII:** `+--`

### Ejemplo de Árboles

✅ **Correcto (ASCII Seguro):**
```
Carpeta/
+-- Archivo
`-- Otro
```

## 3. Validación

Ejecutar antes de commit:

```bash
python scripts/check_encoding.py
python scripts/check_mojibake.py
```

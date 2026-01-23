# Guia para agregar un formato

## Reglas clave

- No se toca JS ni Python.
- Se agrega solo un JSON en `app/data/<uni>/<categoria>/`.
- El discovery lo indexa automaticamente.

## Ejemplo

```
app/data/unac/informe/unac_informe_cual.json
app/data/unac/maestria/unac_maestria_cuant.json
```

## Convenciones de nombre

- `categoria` = carpeta inmediata (`informe`, `proyecto`, `maestria`).
- `enfoque` se deriva del nombre del archivo (`cual`, `cuant`, `general`).
- IDs visibles pueden llevar tildes; slugs deben ser ASCII.

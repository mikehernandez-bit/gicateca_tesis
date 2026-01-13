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

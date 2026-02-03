"""
Archivo: app/core/validation/repo_checks.py
Verificaciones a nivel repositorio: colisiones, providers, assets.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

from app.core.validation.issue import Issue, Severity


def check_id_collisions(
    format_files: List[Tuple[Path, Dict]]
) -> List[Issue]:
    """
    Verifica que no haya IDs duplicados.
    
    Args:
        format_files: Lista de tuplas (path, format_data).
    
    Returns:
        Issues de colisión.
    """
    issues: List[Issue] = []
    seen: Dict[str, Path] = {}
    
    for path, data in format_files:
        meta = data.get("_meta") or {}
        meta_id = meta.get("id", "")
        if not meta_id:
            continue
        
        if meta_id in seen:
            issues.append(Issue(
                severity=Severity.ERROR,
                code="ID_COLLISION",
                message=f"ID duplicado: {meta_id}. También en: {seen[meta_id]}",
                file=str(path)
            ))
        else:
            seen[meta_id] = path
    
    return issues


def check_providers_registered(
    uni_folders: List[str],
    registered_codes: Set[str]
) -> List[Issue]:
    """
    Verifica que cada carpeta de universidad tenga provider registrado.
    
    Args:
        uni_folders: Lista de códigos de carpetas en app/data/.
        registered_codes: Set de códigos en registry.
    
    Returns:
        Issues de providers no registrados.
    """
    issues: List[Issue] = []
    
    for uni_code in uni_folders:
        # Ignorar carpetas especiales
        if uni_code in ("references", "schemas", "__pycache__"):
            continue
        
        if uni_code not in registered_codes:
            issues.append(Issue(
                severity=Severity.WARN,
                code="PROVIDER_MISSING",
                message=f"Carpeta '{uni_code}' sin provider registrado",
                file=f"app/data/{uni_code}"
            ))
    
    return issues


def check_assets_exist(
    app_root: Path,
    required_assets: List[str] = None
) -> List[Issue]:
    """
    Verifica que existan assets requeridos.
    
    Args:
        app_root: Ruta raíz de app/.
        required_assets: Lista de rutas relativas a verificar.
    
    Returns:
        Issues de assets faltantes.
    """
    issues: List[Issue] = []
    
    if required_assets is None:
        required_assets = [
            "static/assets/LogoGeneric.png"
        ]
    
    for asset in required_assets:
        asset_path = app_root / asset
        if not asset_path.exists():
            issues.append(Issue(
                severity=Severity.ERROR,
                code="ASSET_MISSING",
                message=f"Asset requerido no existe: {asset}",
                file=str(asset_path)
            ))
    
    return issues


def run_all_repo_checks(app_root: Path) -> List[Issue]:
    """
    Ejecuta todas las verificaciones de repositorio.
    
    Args:
        app_root: Ruta raíz de app/.
    
    Returns:
        Lista combinada de issues.
    """
    issues: List[Issue] = []
    data_dir = app_root / "data"
    
    # 1. Cargar todos los formatos
    format_files: List[Tuple[Path, Dict]] = []
    uni_folders: List[str] = []
    
    for child in data_dir.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith(("_", ".")):
            continue
        if child.name in ("schemas",):
            continue
        
        uni_folders.append(child.name)
        
        # Cargar JSONs de formatos
        for json_file in child.glob("*.json"):
            if json_file.name in ("alerts.json", "references_config.json", "formatos.json"):
                continue
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                format_files.append((json_file, data))
            except Exception as e:
                issues.append(Issue(
                    severity=Severity.ERROR,
                    code="JSON_INVALID",
                    message=f"JSON inválido: {e}",
                    file=str(json_file)
                ))
    
    # 2. Verificar colisiones de ID
    issues.extend(check_id_collisions(format_files))
    
    # 3. Verificar providers registrados
    try:
        from app.core.registry import list_universities
        registered = set(list_universities())
        issues.extend(check_providers_registered(uni_folders, registered))
    except Exception as e:
        issues.append(Issue(
            severity=Severity.WARN,
            code="REGISTRY_ERROR",
            message=f"No se pudo leer registry: {e}",
            file="app/core/registry.py"
        ))
    
    # 4. Verificar assets
    issues.extend(check_assets_exist(app_root))
    
    return issues

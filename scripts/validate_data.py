#!/usr/bin/env python
"""
Script: scripts/validate_data.py
Valida la integridad de los datos en app/data/.

Uso:
    python scripts/validate_data.py [opciones]

Opciones:
    --strict    Warnings también cuentan como fallo
    --uni CODE  Validar solo una universidad
    --path DIR  Validar solo un directorio

Exit codes:
    0: Sin errores
    1: Errores encontrados
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Agregar raíz del proyecto al path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.validation.issue import Issue, Severity
from app.core.validation.format_validation import validate_format_schema, validate_format_rules
from app.core.validation.references_validation import (
    validate_references_config_schema,
    validate_references_rules,
)
from app.core.validation.repo_checks import run_all_repo_checks


def collect_format_issues(
    data_dir: Path,
    uni_filter: Optional[str] = None
) -> List[Issue]:
    """Valida todos los formatos en app/data/."""
    issues: List[Issue] = []
    
    for uni_folder in sorted(data_dir.iterdir()):
        if not uni_folder.is_dir():
            continue
        if uni_folder.name.startswith(("_", ".")):
            continue
        if uni_folder.name in ("schemas", "references"):
            continue
        
        uni_code = uni_folder.name
        
        # Filtro por universidad
        if uni_filter and uni_code != uni_filter:
            continue
        
        # Validar JSONs de formatos
        for json_file in sorted(uni_folder.glob("*.json")):
            # Ignorar archivos especiales
            if json_file.name in ("alerts.json", "references_config.json", "formatos.json"):
                continue
            
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                issues.append(Issue(
                    severity=Severity.ERROR,
                    code="JSON_PARSE_ERROR",
                    message=str(e),
                    file=str(json_file)
                ))
                continue
            except Exception as e:
                issues.append(Issue(
                    severity=Severity.ERROR,
                    code="FILE_READ_ERROR",
                    message=str(e),
                    file=str(json_file)
                ))
                continue
            
            # Validar schema
            issues.extend(validate_format_schema(data, str(json_file)))
            
            # Validar reglas
            issues.extend(validate_format_rules(data, uni_code, str(json_file)))
        
        # Validar references_config
        refs_file = uni_folder / "references_config.json"
        if refs_file.exists():
            try:
                refs_data = json.loads(refs_file.read_text(encoding="utf-8"))
                issues.extend(validate_references_config_schema(refs_data, str(refs_file)))
                issues.extend(validate_references_rules(refs_data, str(refs_file)))
            except Exception as e:
                issues.append(Issue(
                    severity=Severity.ERROR,
                    code="REFS_READ_ERROR",
                    message=str(e),
                    file=str(refs_file)
                ))
    
    return issues


def print_issues(issues: List[Issue]) -> None:
    """Imprime issues agrupados por severidad."""
    errors = [i for i in issues if i.is_error()]
    warnings = [i for i in issues if not i.is_error()]
    
    if errors:
        print("\n🔴 ERRORES:")
        for issue in errors:
            print(f"  {issue}")
    
    if warnings:
        print("\n🟡 WARNINGS:")
        for issue in warnings:
            print(f"  {issue}")


def main():
    parser = argparse.ArgumentParser(description="Valida datos de GicaTesis")
    parser.add_argument("--strict", action="store_true", help="Warnings también fallan")
    parser.add_argument("--uni", type=str, help="Filtrar por universidad")
    parser.add_argument("--path", type=str, help="Directorio alternativo")
    args = parser.parse_args()
    
    # Determinar directorio de datos
    if args.path:
        data_dir = Path(args.path)
    else:
        data_dir = ROOT / "app" / "data"
    
    if not data_dir.exists():
        print(f"❌ Directorio no existe: {data_dir}")
        sys.exit(1)
    
    print(f"📁 Validando: {data_dir}")
    
    # Recopilar issues de formatos
    issues = collect_format_issues(data_dir, args.uni)
    
    # Ejecutar repo checks (solo si no hay filtro de uni)
    if not args.uni:
        app_root = ROOT / "app"
        issues.extend(run_all_repo_checks(app_root))
    
    # Mostrar resultados
    print_issues(issues)
    
    errors = sum(1 for i in issues if i.is_error())
    warnings = sum(1 for i in issues if not i.is_error())
    
    print(f"\n📊 Resumen: {errors} errores, {warnings} warnings")
    
    # Determinar exit code
    if errors > 0:
        print("❌ FAIL")
        sys.exit(1)
    
    if args.strict and warnings > 0:
        print("❌ FAIL (modo strict)")
        sys.exit(1)
    
    print("✅ OK")
    sys.exit(0)


if __name__ == "__main__":
    main()

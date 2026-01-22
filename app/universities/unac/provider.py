from pathlib import Path
import json

from app.core.loaders import get_data_dir

class UNACProvider:
    code = "unac"
    name = "UNAC"

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
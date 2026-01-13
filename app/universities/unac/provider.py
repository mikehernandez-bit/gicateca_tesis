from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]  # carpeta del proyecto

class UNACProvider:
    code = "unac"
    name = "UNAC"

    def list_formatos(self):
        path = ROOT / "data" / "unac" / "formatos.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def list_alerts(self):
        path = ROOT / "data" / "unac" / "alerts.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def get_formato(self, format_id: str):
        for f in self.list_formatos():
            if f.get("id") == format_id:
                return f
        return None
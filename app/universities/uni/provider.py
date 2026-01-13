from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]

class UNIProvider:
    code = "uni"
    name = "UNI"

    def list_formatos(self):
        path = ROOT / "data" / "uni" / "formatos.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def list_alerts(self):
        path = ROOT / "data" / "uni" / "alerts.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def get_formato(self, format_id: str):
        for f in self.list_formatos():
            if f.get("id") == format_id:
                return f
        return None

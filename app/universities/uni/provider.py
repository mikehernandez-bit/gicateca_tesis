from pathlib import Path
import json

from app.core.loaders import get_data_dir

class UNIProvider:
    code = "uni"
    name = "UNI"

    def list_formatos(self):
        path = get_data_dir(self.code) / "formatos.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def list_alerts(self):
        path = get_data_dir(self.code) / "alerts.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def get_formato(self, format_id: str):
        for f in self.list_formatos():
            if f.get("id") == format_id:
                return f
        return None

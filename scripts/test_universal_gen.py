import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.universities.shared.universal_generator import generate_document_unified

def test():
    json_path = BASE_DIR / "app/data/unac/informe/unac_informe_cual.json"
    output_path = BASE_DIR / "test_universal.docx"
    
    print(f"Generando documento desde: {json_path}")
    generate_document_unified(str(json_path), str(output_path))
    print(f"Documento generado en: {output_path}")

if __name__ == "__main__":
    test()

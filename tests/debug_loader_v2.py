
import sys
import os
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.core.loaders import load_format_by_id

try:
    format_id = "uni-proyecto-standard"
    print(f"Loading format: {format_id}")
    data = load_format_by_id(format_id)
    print("Success!")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

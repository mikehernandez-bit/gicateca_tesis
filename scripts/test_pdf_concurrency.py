"""
Prueba manual: dispara solicitudes concurrentes al endpoint PDF.
Uso:
  python scripts/test_pdf_concurrency.py http://127.0.0.1:8000 formatos/unac-informe-cual
"""
from __future__ import annotations

import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch(url: str) -> tuple[int, int]:
    start = time.time()
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
        return resp.status, int((time.time() - start) * 1000), len(data)


def main() -> int:
    if len(sys.argv) < 3:
        print("Uso: python scripts/test_pdf_concurrency.py <base_url> <format_id>")
        return 1

    base = sys.argv[1].rstrip("/")
    format_id = sys.argv[2].strip("/")
    url = f"{base}/{format_id}/pdf"

    total = 10
    results = []
    print(f"Lanzando {total} requests concurrentes a: {url}")

    with ThreadPoolExecutor(max_workers=total) as executor:
        futures = [executor.submit(fetch, url) for _ in range(total)]
        for future in as_completed(futures):
            results.append(future.result())

    for idx, (status, ms, size) in enumerate(results, start=1):
        print(f"[{idx}] status={status} time_ms={ms} size={size}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


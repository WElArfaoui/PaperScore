#!/usr/bin/env python3
"""
build_journal_db.py
===================
Descarga datos de revistas desde OpenAlex (API gratuita y abierta)
y genera extension/journal_data.json listo para usar en la extensión.

OpenAlex cubre más de 40.000 revistas con métricas de impacto.
Los cuartiles se calculan a partir del ranking de citas dentro de cada área.

Uso:
  python3 build_journal_db.py            → descarga desde OpenAlex (recomendado)
  python3 build_journal_db.py scimago archivo.csv  → usa un CSV local de Scimago
  python3 build_journal_db.py jcr archivo.csv      → usa un CSV de JCR (Clarivate)
"""

import json
import csv
import sys
import os
import urllib.request
import urllib.parse
import time

OPENALEX_URL = "https://api.openalex.org/sources"
OUTPUT_FILE  = os.path.join(os.path.dirname(__file__), "extension", "journal_data.json")
EMAIL        = "paperscore@github.com"   # requerido por OpenAlex para uso "polite"


def fetch_openalex() -> list[dict]:
    """
    Descarga revistas 'core' desde la API de OpenAlex (~34.000 revistas).
    Asigna cuartil Q1-Q4 según ranking de citedness dentro de cada área.
    """
    journals_raw = []
    cursor = "*"

    print("Descargando revistas desde OpenAlex (API gratuita)...")

    while cursor:
        params = urllib.parse.urlencode({
            "filter":   "type:journal,is_core:true",
            "per-page": 200,
            "cursor":   cursor,
            "select":   "id,display_name,abbreviated_title,topics,summary_stats",
            "mailto":   EMAIL,
        })
        url = f"{OPENALEX_URL}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": f"PaperScore/1.0 (mailto:{EMAIL})"})

        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        results = data.get("results", [])
        if not results:
            break

        if not journals_raw:
            total = data["meta"]["count"]
            print(f"  Total: {total:,} revistas")

        journals_raw.extend(results)
        print(f"  {len(journals_raw):,} descargadas...", end="\r")

        cursor = data["meta"].get("next_cursor")
        time.sleep(0.05)

    print(f"\n  Descarga completa: {len(journals_raw):,} revistas")
    return _assign_quartiles(journals_raw)


def _assign_quartiles(raw: list[dict]) -> list[dict]:
    """
    Agrupa las revistas por área temática y asigna Q1-Q4 según
    su posición relativa en citedness dentro del grupo.
    """
    # Agrupar por área principal (primer topic)
    by_area: dict[str, list] = {}
    for j in raw:
        topics = j.get("topics") or []
        area = topics[0]["field"]["display_name"] if topics else "General"
        by_area.setdefault(area, []).append(j)

    journals_out = []
    for area, group in by_area.items():
        # Ordenar por citedness descendente (campo dentro de summary_stats)
        group.sort(key=lambda x: (x.get("summary_stats") or {}).get("2yr_mean_citedness") or 0, reverse=True)
        n = len(group)
        for i, j in enumerate(group):
            pct = i / n   # 0 = mejor, 1 = peor
            if   pct < 0.25: quartile = "Q1"
            elif pct < 0.50: quartile = "Q2"
            elif pct < 0.75: quartile = "Q3"
            else:            quartile = "Q4"

            citedness = (j.get("summary_stats") or {}).get("2yr_mean_citedness") or 0
            journals_out.append({
                "name":     j.get("display_name", "").strip(),
                "abbr":     j.get("abbreviated_title") or j.get("display_name", "").strip(),
                "jif":      round(citedness, 3),
                "quartile": quartile,
                "category": area,
            })

    return journals_out


def parse_jcr_csv(filepath: str) -> list[dict]:
    """
    Parsea un CSV de JCR (Clarivate).
    Adapta los nombres de columna según tu exportación.
    """
    journals = []
    with open(filepath, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                journals.append({
                    "name": row.get("Journal name", "").strip(),
                    "abbr": row.get("Abbreviation", "").strip(),
                    "jif":  float(row.get("2023 JIF", 0) or 0),
                    "jif5y": float(row.get("5-Year JIF", 0) or 0),
                    "quartile": row.get("JIF Quartile", "").strip(),
                    "category": row.get("Category", "").strip(),
                    "rank": row.get("Rank in Category", "").strip(),
                })
            except (ValueError, KeyError):
                continue
    return journals


def parse_scimago_csv(filepath: str) -> list[dict]:
    """
    Parsea un CSV de Scimago (SJR).
    Mapea cuartil SJR al formato Q1-Q4.
    """
    journals = []
    with open(filepath, encoding="utf-8-sig", errors="replace") as f:
        # Scimago usa ; como separador
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            # Scimago puede tener múltiples categorías separadas por ";"
            # dentro de las columnas — tomamos la primera
            quartile_raw = row.get("SJR Best Quartile", "").strip()
            quartile = quartile_raw if quartile_raw in ("Q1","Q2","Q3","Q4") else None
            try:
                sjr = float(row.get("SJR", "0").replace(",", ".") or 0)
            except ValueError:
                sjr = 0.0
            journals.append({
                "name": row.get("Title", "").strip(),
                "abbr": row.get("Abbreviation", row.get("Title", "")).strip(),
                "jif":  sjr,           # SJR ≠ JIF, pero útil como proxy
                "jif5y": None,
                "quartile": quartile,
                "category": row.get("Categories", "").split(";")[0].strip(),
                "rank": None,
                "source": "scimago",
            })
    return journals


def sample_data() -> list[dict]:
    """Datos de muestra para probar la extensión sin CSV real."""
    return [
        {"name": "Nature", "abbr": "Nature", "jif": 64.8, "jif5y": 67.1, "quartile": "Q1", "category": "Multidisciplinary Sciences", "rank": "1/74"},
        {"name": "Science", "abbr": "Science", "jif": 56.9, "jif5y": 59.2, "quartile": "Q1", "category": "Multidisciplinary Sciences", "rank": "2/74"},
        {"name": "The Lancet", "abbr": "Lancet", "jif": 98.4, "jif5y": 89.5, "quartile": "Q1", "category": "Medicine, General & Internal", "rank": "1/165"},
        {"name": "New England Journal of Medicine", "abbr": "N Engl J Med", "jif": 158.5, "jif5y": 141.2, "quartile": "Q1", "category": "Medicine, General & Internal", "rank": "1/165"},
        {"name": "JAMA", "abbr": "JAMA", "jif": 120.7, "jif5y": 112.3, "quartile": "Q1", "category": "Medicine, General & Internal", "rank": "2/165"},
        {"name": "BMJ", "abbr": "BMJ", "jif": 93.6, "jif5y": 85.4, "quartile": "Q1", "category": "Medicine, General & Internal", "rank": "3/165"},
        {"name": "PLOS ONE", "abbr": "PLoS One", "jif": 3.7, "jif5y": 4.1, "quartile": "Q2", "category": "Multidisciplinary Sciences", "rank": "18/74"},
        {"name": "Bioinformatics", "abbr": "Bioinformatics", "jif": 5.8, "jif5y": 6.2, "quartile": "Q1", "category": "Mathematical & Computational Biology", "rank": "3/61"},
        {"name": "Journal of Informetrics", "abbr": "J Informetr", "jif": 7.1, "jif5y": 7.8, "quartile": "Q1", "category": "Information Science & Library Science", "rank": "2/97"},
        {"name": "Scientometrics", "abbr": "Scientometrics", "jif": 3.5, "jif5y": 3.9, "quartile": "Q2", "category": "Information Science & Library Science", "rank": "18/97"},
    ]


def main():
    tmp_file = None

    if len(sys.argv) == 3:
        source, filepath = sys.argv[1], sys.argv[2]
        if source == "jcr":
            journals = parse_jcr_csv(filepath)
        elif source == "scimago":
            journals = parse_scimago_csv(filepath)
        else:
            print(f"Fuente desconocida: {source}. Usa 'jcr' o 'scimago'")
            sys.exit(1)
        print(f"Procesadas {len(journals)} revistas desde {filepath}")

    elif len(sys.argv) == 1:
        # Sin argumentos → descarga desde OpenAlex automáticamente
        journals = fetch_openalex()
        print(f"Procesadas {len(journals)} revistas desde OpenAlex")

    else:
        print(__doc__)
        sys.exit(1)

    # Eliminar entradas vacías o sin nombre
    journals = [j for j in journals if j.get("name")]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(journals, f, ensure_ascii=False, indent=2)

    print(f"✓ Guardado en: {OUTPUT_FILE}")
    print(f"  Total: {len(journals)} revistas")

    # Limpiar archivo temporal si se descargó
    if tmp_file and os.path.exists(tmp_file):
        os.remove(tmp_file)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
build_journal_db.py
===================
Genera journal_data.json a partir de un CSV exportado de JCR / Scimago.

OPCIÓN A - JCR (Clarivate, requiere acceso institucional):
  Exportar desde: https://jcr.clarivate.com/
  Columnas necesarias: Journal name, Abbreviation, 2023 JIF, JIF Quartile, Category

OPCIÓN B - Scimago (GRATUITO):
  Descargar de: https://www.scimagojr.com/journalrank.php
  Exportar como CSV
  Columnas: Title, Issn, SJR, H index, Total Docs, Quartile

OPCIÓN C - Datos de ejemplo (para pruebas, incluidos abajo)
"""

import json
import csv
import sys
import os

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "extension", "journal_data.json")


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
    if len(sys.argv) == 3:
        source = sys.argv[1]   # "jcr" o "scimago"
        filepath = sys.argv[2]

        if source == "jcr":
            journals = parse_jcr_csv(filepath)
        elif source == "scimago":
            journals = parse_scimago_csv(filepath)
        else:
            print(f"Fuente desconocida: {source}. Usa 'jcr' o 'scimago'")
            sys.exit(1)

        print(f"Procesadas {len(journals)} revistas desde {filepath}")
    else:
        print("Uso: python build_journal_db.py [jcr|scimago] <archivo.csv>")
        print("Sin argumentos: se generan datos de muestra.\n")
        journals = sample_data()
        print(f"Generando {len(journals)} revistas de ejemplo...")

    # Eliminar entradas vacías o sin nombre
    journals = [j for j in journals if j.get("name")]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(journals, f, ensure_ascii=False, indent=2)

    print(f"✓ Guardado en: {OUTPUT_FILE}")
    print(f"  Total: {len(journals)} revistas")


if __name__ == "__main__":
    main()

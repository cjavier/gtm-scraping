#!/usr/bin/env python3
"""
serper_search.py — Wrapper de Serper.dev para búsquedas en Google.

Por defecto guarda automáticamente en la DB:
  - La búsqueda en la tabla busquedas (log)
  - Las empresas encontradas en la tabla empresas (filtrando directorios y duplicados)

Uso:
    python scripts/serper_search.py "constructoras en Monterrey" --num 20 --country mx --lang es
    python scripts/serper_search.py "empresas de acero Mexico" --json
    python scripts/serper_search.py "despachos CDMX" --no-save   # sin guardar en DB
"""

import argparse
import json
import os
import sys
import time

import httpx
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup: permite importar db_utils desde cualquier directorio
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SCRIPT_DIR)

# Cargar .env desde la raíz del proyecto
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

SERPER_API_URL = "https://google.serper.dev/search"


# ---------------------------------------------------------------------------
# Llamada a la API
# ---------------------------------------------------------------------------

def call_serper(query: str, num: int, country: str, lang: str) -> dict:
    """Llama a la API de Serper.dev y retorna el JSON completo."""
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        print("ERROR: SERPER_API_KEY no está configurada en .env", file=sys.stderr)
        sys.exit(1)

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "gl": country,
        "hl": lang,
        "num": num,
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(SERPER_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"ERROR HTTP {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"ERROR de conexión: {e}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Extracción de resultados
# ---------------------------------------------------------------------------

def extract_results(data: dict) -> dict:
    """Extrae campos relevantes del response de Serper."""
    results = {
        "organic": [],
        "knowledgeGraph": None,
        "peopleAlsoAsk": [],
        "searchParameters": data.get("searchParameters", {}),
    }

    # Resultados orgánicos
    for item in data.get("organic", []):
        results["organic"].append({
            "position": item.get("position"),
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "displayedLink": item.get("displayedLink", ""),
        })

    # Knowledge Graph
    kg = data.get("knowledgeGraph")
    if kg:
        results["knowledgeGraph"] = {
            "title": kg.get("title", ""),
            "type": kg.get("type", ""),
            "description": kg.get("description", ""),
            "website": kg.get("website", ""),
            "phone": kg.get("phone", ""),
            "address": kg.get("address", ""),
        }

    # People Also Ask
    for item in data.get("peopleAlsoAsk", []):
        results["peopleAlsoAsk"].append({
            "question": item.get("question", ""),
            "snippet": item.get("snippet", ""),
            "link": item.get("link", ""),
        })

    return results


# ---------------------------------------------------------------------------
# Formateo para salida legible (modo default — para Claude Code)
# ---------------------------------------------------------------------------

def print_readable(results: dict, query: str) -> None:
    """Imprime resultados en formato legible para Claude Code."""
    params = results.get("searchParameters", {})
    organic = results.get("organic", [])
    kg = results.get("knowledgeGraph")
    paa = results.get("peopleAlsoAsk", [])

    print("=" * 70)
    print(f"BÚSQUEDA: {query}")
    print(f"País: {params.get('gl', 'mx')} | Idioma: {params.get('hl', 'es')} | Resultados: {len(organic)}")
    print("=" * 70)

    # Knowledge Graph
    if kg and (kg.get("title") or kg.get("description")):
        print("\n--- KNOWLEDGE GRAPH ---")
        if kg.get("title"):
            print(f"Nombre:      {kg['title']}")
        if kg.get("type"):
            print(f"Tipo:        {kg['type']}")
        if kg.get("description"):
            print(f"Descripción: {kg['description']}")
        if kg.get("website"):
            print(f"Sitio web:   {kg['website']}")
        if kg.get("phone"):
            print(f"Teléfono:    {kg['phone']}")
        if kg.get("address"):
            print(f"Dirección:   {kg['address']}")
        print()

    # Resultados orgánicos
    print(f"\n--- RESULTADOS ORGÁNICOS ({len(organic)}) ---\n")
    for item in organic:
        print(f"[{item['position']}] {item['title']}")
        print(f"    URL:     {item['link']}")
        if item.get("snippet"):
            snippet = item["snippet"].replace("\n", " ")
            print(f"    Snippet: {snippet}")
        print()

    # People Also Ask
    if paa:
        print(f"\n--- PERSONAS TAMBIÉN PREGUNTAN ({len(paa)}) ---\n")
        for item in paa:
            print(f"  - {item['question']}")
            if item.get("link"):
                print(f"    {item['link']}")
        print()

    print("=" * 70)
    print(f"Total resultados orgánicos: {len(organic)}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Búsqueda en Google usando Serper.dev API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/serper_search.py "constructoras en Monterrey" --num 20
  python scripts/serper_search.py "empresas acero Mexico" --country mx --lang es --save
  python scripts/serper_search.py "despachos contables CDMX" --json
        """,
    )
    parser.add_argument(
        "query",
        help="Query de búsqueda",
    )
    parser.add_argument(
        "--num",
        type=int,
        default=10,
        metavar="N",
        help="Número de resultados a obtener (default: 10)",
    )
    parser.add_argument(
        "--country",
        default="mx",
        metavar="CODE",
        help="Código de país para localización (default: mx)",
    )
    parser.add_argument(
        "--lang",
        default="es",
        metavar="CODE",
        help="Código de idioma (default: es)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="NO guardar resultados en la base de datos (por defecto SÍ se guardan)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Imprimir resultados como JSON (en lugar de formato legible)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    start_time = time.time()

    # Llamar a la API
    raw_data = call_serper(
        query=args.query,
        num=args.num,
        country=args.country,
        lang=args.lang,
    )

    elapsed = time.time() - start_time

    # Extraer resultados estructurados
    results = extract_results(raw_data)
    num_results = len(results["organic"])

    # Salida
    if args.output_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_readable(results, args.query)
        print(f"\n(Tiempo de respuesta: {elapsed:.2f}s)")

    # Guardar en DB por defecto (a menos que se use --no-save)
    if not args.no_save:
        try:
            import db_utils

            # 1. Guardar empresas encontradas en SERP
            serp_result = db_utils.insert_empresas_from_serp(
                organic_results=results["organic"],
                query=args.query,
            )
            guardados = len(serp_result["inserted"])

            # 2. Loggear la búsqueda
            busqueda_id = db_utils.log_busqueda(
                query=args.query,
                herramienta="serper",
                resultados=num_results,
                guardados=guardados,
            )

            if not args.output_json:
                print(f"\n[DB] Búsqueda registrada (ID: {busqueda_id})")
                print(f"[DB] Empresas guardadas: {guardados} nuevas, "
                      f"{serp_result['skipped_duplicates']} duplicadas, "
                      f"{serp_result['skipped_directories']} directorios filtrados")

        except ImportError:
            print(
                "\n[WARN] No se pudo importar db_utils. "
                "Asegúrate de que scripts/db_utils.py existe.",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"\n[WARN] Error guardando en DB: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

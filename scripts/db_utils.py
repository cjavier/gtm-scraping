#!/usr/bin/env python3
"""
db_utils.py — Database utilities for the scraping project.

Importable functions:
    get_db_path()
    get_connection()
    insert_empresa(data)
    search_empresas(query, field)
    update_empresa(id, data)
    set_status(id, status)
    export_csv(filepath, filtro)
    export_json(filepath, filtro)
    log_busqueda(query, herramienta, resultados)
    log_scraping(url, herramienta, exito, tiempo, error)
    get_stats()
    url_exists(url)

CLI usage:
    python db_utils.py --stats
    python db_utils.py --search "Acme" --field nombre
    python db_utils.py --insert '{"nombre": "Empresa SA", "ciudad": "CDMX"}'
    python db_utils.py --update 5 '{"email": "nuevo@empresa.com"}'
    python db_utils.py --set-status 5 contactado
    python db_utils.py --add-note 5 "Llamar la próxima semana"
    python db_utils.py --export-csv output/empresas.csv
    python db_utils.py --export-json output/empresas.json
    python db_utils.py --check-url https://empresa.com
    python db_utils.py --find-duplicates
    python db_utils.py --incomplete
    python db_utils.py --log-search "agencias CDMX" google 15
    python db_utils.py --log-scrape https://empresa.com playwright 1
"""

import sqlite3
import os
import json
import csv
import argparse
import sys
from datetime import datetime


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def get_db_path() -> str:
    """Return absolute path to the SQLite database file."""
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(scripts_dir)
    return os.path.join(project_root, "db", "empresas.db")


def get_schema_path() -> str:
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(scripts_dir)
    return os.path.join(project_root, "db", "schema.sql")


# ---------------------------------------------------------------------------
# Connection & initialisation
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Open and return a connection to the database, creating it if needed."""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    # Auto-initialise schema if tables do not exist yet
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='empresas'"
    )
    if cursor.fetchone() is None:
        schema_path = get_schema_path()
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as fh:
                conn.executescript(fh.read())
            conn.commit()

    return conn


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

EMPRESA_FIELDS = {
    "nombre", "sitio_web", "telefono", "email", "direccion", "ciudad",
    "estado", "pais", "industria", "sub_industria", "descripcion",
    "servicios", "empleados_estimado", "redes_sociales", "fuente",
    "query_origen", "url_scrapeada", "notas", "status",
    "contacto_nombre", "contacto_cargo", "contacto_email", "contacto_telefono",
    "contacto_linkedin", "cliente_id",
}

CLIENTE_FIELDS = {
    "nombre", "descripcion", "industria_objetivo", "color",
}


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def _build_where_clause(filtro: dict):
    """Convert a filtro dict to a (where_sql, params) tuple."""
    if not filtro:
        return "", []
    clauses = []
    params = []
    for key, value in filtro.items():
        if key in EMPRESA_FIELDS:
            clauses.append(f"{key} LIKE ?")
            params.append(f"%{value}%")
    if not clauses:
        return "", []
    return "WHERE " + " AND ".join(clauses), params


# ---------------------------------------------------------------------------
# Core CRUD functions
# ---------------------------------------------------------------------------

def insert_empresa(data: dict) -> int:
    """
    Insert a new empresa record.

    Args:
        data: dict with any subset of empresa columns.

    Returns:
        The new row id, or -1 on error.
    """
    if "nombre" not in data or not data["nombre"]:
        raise ValueError("El campo 'nombre' es obligatorio.")

    valid = {k: v for k, v in data.items() if k in EMPRESA_FIELDS}
    columns = ", ".join(valid.keys())
    placeholders = ", ".join(["?"] * len(valid))
    values = list(valid.values())

    with get_connection() as conn:
        cursor = conn.execute(
            f"INSERT INTO empresas ({columns}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        return cursor.lastrowid


def search_empresas(query: str, field: str = "nombre") -> list:
    """
    Search empresas by a single field using LIKE.

    Args:
        query: search string.
        field: column name to search in (default: 'nombre').

    Returns:
        List of dicts.
    """
    if field not in EMPRESA_FIELDS and field != "id":
        raise ValueError(f"Campo inválido: {field}")

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM empresas WHERE {field} LIKE ?",
            (f"%{query}%",),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def update_empresa(id: int, data: dict) -> bool:
    """
    Update fields of an existing empresa.

    Args:
        id:   empresa primary key.
        data: dict of fields to update.

    Returns:
        True if a row was modified, False otherwise.
    """
    valid = {k: v for k, v in data.items() if k in EMPRESA_FIELDS}
    if not valid:
        raise ValueError("No se proporcionaron campos válidos para actualizar.")

    valid["fecha_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join([f"{k} = ?" for k in valid.keys()])
    values = list(valid.values()) + [id]

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE empresas SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        return cursor.rowcount > 0


def set_status(id: int, status: str) -> bool:
    """
    Change the status of an empresa.

    Args:
        id:     empresa primary key.
        status: new status string.

    Returns:
        True if a row was updated.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE empresas SET status = ?, fecha_actualizacion = datetime('now') WHERE id = ?",
            (status, id),
        )
        conn.commit()
        return cursor.rowcount > 0


def add_note(id: int, note: str) -> bool:
    """
    Append a timestamped note to an empresa's notas field.

    Args:
        id:   empresa primary key.
        note: text to append.

    Returns:
        True if a row was updated.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT notas FROM empresas WHERE id = ?", (id,)
        ).fetchone()
        if row is None:
            return False
        existing = row["notas"] or ""
        separator = "\n" if existing else ""
        new_notas = f"{existing}{separator}[{timestamp}] {note}"
        cursor = conn.execute(
            "UPDATE empresas SET notas = ?, fecha_actualizacion = datetime('now') WHERE id = ?",
            (new_notas, id),
        )
        conn.commit()
        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------

def export_csv(filepath: str, filtro: dict = None) -> int:
    """
    Export empresas to a CSV file.

    Args:
        filepath: destination path.
        filtro:   optional dict of field->value filters.

    Returns:
        Number of rows exported.
    """
    where_sql, params = _build_where_clause(filtro or {})
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM empresas {where_sql} ORDER BY fecha_descubrimiento DESC",
            params,
        ).fetchall()

    if not rows:
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    return len(rows)


def export_json(filepath: str, filtro: dict = None) -> int:
    """
    Export empresas to a JSON file.

    Args:
        filepath: destination path.
        filtro:   optional dict of field->value filters.

    Returns:
        Number of rows exported.
    """
    where_sql, params = _build_where_clause(filtro or {})
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM empresas {where_sql} ORDER BY fecha_descubrimiento DESC",
            params,
        ).fetchall()

    data = [dict(r) for r in rows]
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    return len(data)


# ---------------------------------------------------------------------------
# Logging functions
# ---------------------------------------------------------------------------

def log_busqueda(query: str, herramienta: str, resultados: int, guardados: int = 0, notas: str = None) -> int:
    """
    Log a completed search.

    Returns:
        New busquedas row id.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO busquedas (query, herramienta, resultados_encontrados, resultados_guardados, notas) VALUES (?, ?, ?, ?, ?)",
            (query, herramienta, resultados, guardados, notas),
        )
        conn.commit()
        return cursor.lastrowid


def log_scraping(
    url: str,
    herramienta: str,
    exito: bool,
    tiempo: float = 0.0,
    datos_extraidos: int = 0,
    error: str = None,
) -> int:
    """
    Log a scraping attempt.

    Returns:
        New scraping_log row id.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO scraping_log (url, herramienta, exito, tiempo_segundos, datos_extraidos, error) VALUES (?, ?, ?, ?, ?, ?)",
            (url, herramienta, 1 if exito else 0, tiempo, datos_extraidos, error),
        )
        conn.commit()
        return cursor.lastrowid


# ---------------------------------------------------------------------------
# Query / analytics functions
# ---------------------------------------------------------------------------

def get_stats() -> dict:
    """
    Return a dict with general database statistics.
    """
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]
        con_email = conn.execute(
            "SELECT COUNT(*) FROM empresas WHERE email IS NOT NULL AND email != ''"
        ).fetchone()[0]
        con_tel = conn.execute(
            "SELECT COUNT(*) FROM empresas WHERE telefono IS NOT NULL AND telefono != ''"
        ).fetchone()[0]

        por_ciudad = [
            dict(r)
            for r in conn.execute(
                "SELECT ciudad, COUNT(*) as total FROM empresas GROUP BY ciudad ORDER BY total DESC LIMIT 15"
            ).fetchall()
        ]
        por_status = [
            dict(r)
            for r in conn.execute(
                "SELECT status, COUNT(*) as total FROM empresas GROUP BY status ORDER BY total DESC"
            ).fetchall()
        ]
        por_industria = [
            dict(r)
            for r in conn.execute(
                "SELECT industria, COUNT(*) as total FROM empresas GROUP BY industria ORDER BY total DESC LIMIT 15"
            ).fetchall()
        ]
        total_busquedas = conn.execute("SELECT COUNT(*) FROM busquedas").fetchone()[0]
        total_scrapes = conn.execute("SELECT COUNT(*) FROM scraping_log").fetchone()[0]

    return {
        "total_empresas": total,
        "con_email": con_email,
        "con_telefono": con_tel,
        "por_ciudad": por_ciudad,
        "por_status": por_status,
        "por_industria": por_industria,
        "total_busquedas_log": total_busquedas,
        "total_scrapes_log": total_scrapes,
    }


def url_exists(url: str) -> bool:
    """Return True if the URL already appears in empresas.url_scrapeada or sitio_web."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM empresas WHERE url_scrapeada = ? OR sitio_web = ? LIMIT 1",
            (url, url),
        ).fetchone()
        return row is not None


# ---------------------------------------------------------------------------
# SERP → DB auto-save
# ---------------------------------------------------------------------------

# Dominios de directorios genéricos que NO son empresas reales
DIRECTORY_DOMAINS = {
    "doctoralia.com.mx", "topdoctors.mx", "topdoctors.com.mx",
    "psico.mx", "yelp.com", "yelp.com.mx", "yellowpages.com",
    "seccionamarilla.com.mx", "paginasamarillas.com.mx",
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "youtube.com", "tiktok.com",
    "wikipedia.org", "es.wikipedia.org",
    "google.com", "google.com.mx", "maps.google.com",
    "tripadvisor.com", "tripadvisor.com.mx",
    "indeed.com", "indeed.com.mx", "glassdoor.com",
    "gobierno.mx", "gob.mx",
}


def _is_directory_url(url: str) -> bool:
    """Return True if the URL belongs to a known directory/aggregator domain."""
    from urllib.parse import urlparse
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
        return domain in DIRECTORY_DOMAINS
    except Exception:
        return False


def insert_empresas_from_serp(
    organic_results: list,
    query: str,
    ciudad: str = None,
    estado: str = None,
    industria: str = None,
    cliente_id: int = None,
) -> dict:
    """
    Insert empresas from SERP organic results into the DB.

    Filters out directory/aggregator URLs, checks for duplicates,
    and inserts new empresas with the data available from SERP.

    Args:
        organic_results: list of dicts with keys: title, link, snippet.
        query: the search query used (stored as query_origen).
        ciudad: optional city to tag empresas with.
        estado: optional state to tag empresas with.
        industria: optional industry to tag empresas with.

    Returns:
        dict with keys: inserted (list of ids), skipped_duplicates (int),
        skipped_directories (int), total (int).
    """
    inserted = []
    skipped_duplicates = 0
    skipped_directories = 0

    for item in organic_results:
        url = item.get("link", "")
        title = item.get("title", "").strip()
        snippet = item.get("snippet", "").strip()

        if not url or not title:
            continue

        # Skip directory/aggregator URLs
        if _is_directory_url(url):
            skipped_directories += 1
            continue

        # Skip duplicates
        if url_exists(url):
            skipped_duplicates += 1
            continue

        data = {
            "nombre": title,
            "sitio_web": url,
            "descripcion": snippet,
            "fuente": "serp",
            "query_origen": query,
            "status": "nuevo",
        }
        if ciudad:
            data["ciudad"] = ciudad
        if estado:
            data["estado"] = estado
        if industria:
            data["industria"] = industria
        if cliente_id:
            data["cliente_id"] = cliente_id

        try:
            new_id = insert_empresa(data)
            inserted.append(new_id)
        except Exception:
            pass

    return {
        "inserted": inserted,
        "skipped_duplicates": skipped_duplicates,
        "skipped_directories": skipped_directories,
        "total": len(organic_results),
    }


def find_duplicates() -> list:
    """
    Return groups of potentially duplicate empresas based on nombre similarity.
    Uses a simple approach: exact match on lowercased, stripped nombre.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT LOWER(TRIM(nombre)) as nombre_norm, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
            FROM empresas
            GROUP BY nombre_norm
            HAVING cnt > 1
            ORDER BY cnt DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_incomplete() -> list:
    """Return empresas missing email or telefono."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, nombre, ciudad, sitio_web, email, telefono, status
            FROM empresas
            WHERE (email IS NULL OR email = '')
               OR (telefono IS NULL OR telefono = '')
            ORDER BY fecha_descubrimiento DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Cliente CRUD
# ---------------------------------------------------------------------------

def insert_cliente(data: dict) -> int:
    """Insert a new cliente. Returns the new row id."""
    if "nombre" not in data or not data["nombre"]:
        raise ValueError("El campo 'nombre' es obligatorio para el cliente.")
    valid = {k: v for k, v in data.items() if k in CLIENTE_FIELDS}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    valid["fecha_creacion"] = now
    valid["fecha_actualizacion"] = now
    columns = ", ".join(valid.keys())
    placeholders = ", ".join(["?"] * len(valid))
    values = list(valid.values())
    with get_connection() as conn:
        cursor = conn.execute(
            f"INSERT INTO clientes ({columns}) VALUES ({placeholders})", values
        )
        conn.commit()
        return cursor.lastrowid


def get_clientes() -> list:
    """Return all clientes with empresa counts."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.*, COUNT(e.id) as total_empresas
            FROM clientes c
            LEFT JOIN empresas e ON e.cliente_id = c.id
            GROUP BY c.id
            ORDER BY c.nombre
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_cliente(id: int) -> dict:
    """Return a single cliente by id, or None."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM clientes WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None


def update_cliente(id: int, data: dict) -> bool:
    """Update a cliente's fields. Returns True if updated."""
    valid = {k: v for k, v in data.items() if k in CLIENTE_FIELDS}
    if not valid:
        raise ValueError("No se proporcionaron campos válidos.")
    valid["fecha_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join([f"{k} = ?" for k in valid.keys()])
    values = list(valid.values()) + [id]
    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE clientes SET {set_clause} WHERE id = ?", values
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_cliente(id: int) -> bool:
    """Delete a cliente (only if it has no empresas). Returns True if deleted."""
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM empresas WHERE cliente_id = ?", (id,)
        ).fetchone()[0]
        if count > 0:
            raise ValueError(
                f"No se puede eliminar: el cliente tiene {count} empresas asociadas."
            )
        cursor = conn.execute("DELETE FROM clientes WHERE id = ?", (id,))
        conn.commit()
        return cursor.rowcount > 0


def get_empresas_paginated(
    cliente_id: int = None,
    page: int = 1,
    per_page: int = 100,
    search: str = None,
    filtros: dict = None,
    sort_key: str = "nombre",
    sort_dir: str = "asc",
) -> dict:
    """
    Return paginated empresas with server-side filtering and sorting.

    Returns dict with: items, total, page, per_page, total_pages.
    """
    allowed_sort = {
        "nombre", "sitio_web", "email", "ciudad", "estado",
        "industria", "status", "fecha_descubrimiento",
    }
    if sort_key not in allowed_sort:
        sort_key = "nombre"
    if sort_dir not in ("asc", "desc"):
        sort_dir = "asc"

    conditions = []
    params = []

    if cliente_id is not None:
        conditions.append("e.cliente_id = ?")
        params.append(cliente_id)

    if search:
        search_cols = ["e.nombre", "e.sitio_web", "e.email", "e.telefono",
                       "e.ciudad", "e.estado", "e.industria"]
        search_clause = " OR ".join([f"{c} LIKE ?" for c in search_cols])
        conditions.append(f"({search_clause})")
        params.extend([f"%{search}%"] * len(search_cols))

    if filtros:
        for key, val in filtros.items():
            if key in EMPRESA_FIELDS and val:
                conditions.append(f"e.{key} = ?")
                params.append(val)

    where_sql = ""
    if conditions:
        where_sql = "WHERE " + " AND ".join(conditions)

    with get_connection() as conn:
        # Total count
        total = conn.execute(
            f"SELECT COUNT(*) FROM empresas e {where_sql}", params
        ).fetchone()[0]

        # Paginated results
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"SELECT e.* FROM empresas e {where_sql} ORDER BY e.{sort_key} COLLATE NOCASE {sort_dir} LIMIT ? OFFSET ?",
            params + [per_page, offset],
        ).fetchall()

    total_pages = max(1, -(-total // per_page))  # ceil division
    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def get_filter_options(cliente_id: int = None) -> dict:
    """Return unique values for filterable columns, optionally scoped to a cliente."""
    filterable = ["ciudad", "estado", "industria", "status"]
    where = "WHERE cliente_id = ?" if cliente_id else ""
    params = [cliente_id] if cliente_id else []
    opts = {}
    with get_connection() as conn:
        for col in filterable:
            rows = conn.execute(
                f"SELECT DISTINCT {col} FROM empresas {where} AND {col} IS NOT NULL AND {col} != '' ORDER BY {col} COLLATE NOCASE"
                if where else
                f"SELECT DISTINCT {col} FROM empresas WHERE {col} IS NOT NULL AND {col} != '' ORDER BY {col} COLLATE NOCASE",
                params,
            ).fetchall()
            opts[col] = [r[0] for r in rows]
    return opts


def get_cliente_stats(cliente_id: int) -> dict:
    """Return stats for a specific cliente."""
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM empresas WHERE cliente_id = ?", (cliente_id,)
        ).fetchone()[0]
        con_email = conn.execute(
            "SELECT COUNT(*) FROM empresas WHERE cliente_id = ? AND email IS NOT NULL AND email != ''",
            (cliente_id,),
        ).fetchone()[0]
        con_tel = conn.execute(
            "SELECT COUNT(*) FROM empresas WHERE cliente_id = ? AND telefono IS NOT NULL AND telefono != ''",
            (cliente_id,),
        ).fetchone()[0]
        por_status = [
            dict(r) for r in conn.execute(
                "SELECT status, COUNT(*) as total FROM empresas WHERE cliente_id = ? GROUP BY status ORDER BY total DESC",
                (cliente_id,),
            ).fetchall()
        ]
    return {
        "total_empresas": total,
        "con_email": con_email,
        "con_telefono": con_tel,
        "por_status": por_status,
    }


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _print_stats(stats: dict):
    print("=" * 50)
    print("ESTADÍSTICAS GENERALES")
    print("=" * 50)
    print(f"  Total empresas   : {stats['total_empresas']}")
    print(f"  Con email        : {stats['con_email']}")
    print(f"  Con teléfono     : {stats['con_telefono']}")
    print(f"  Búsquedas log    : {stats['total_busquedas_log']}")
    print(f"  Scrapes log      : {stats['total_scrapes_log']}")

    if stats["por_status"]:
        print("\nPOR STATUS:")
        for row in stats["por_status"]:
            print(f"  {row['status'] or '(sin status)':20s} {row['total']}")

    if stats["por_ciudad"]:
        print("\nPOR CIUDAD (top 15):")
        for row in stats["por_ciudad"]:
            print(f"  {row['ciudad'] or '(sin ciudad)':25s} {row['total']}")

    if stats["por_industria"]:
        print("\nPOR INDUSTRIA (top 15):")
        for row in stats["por_industria"]:
            print(f"  {row['industria'] or '(sin industria)':30s} {row['total']}")

    print("=" * 50)


def _print_empresas(rows: list, title: str = "RESULTADOS"):
    print(f"\n{title} ({len(rows)} encontrados)")
    print("-" * 60)
    for e in rows:
        print(
            f"[{e.get('id', '?')}] {e.get('nombre', '')} | "
            f"{e.get('ciudad', '')} | "
            f"{e.get('email', '')} | "
            f"{e.get('telefono', '')} | "
            f"{e.get('status', '')}"
        )
    print("-" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Utilidades de base de datos para el proyecto de scraping.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas generales")
    parser.add_argument("--search", metavar="QUERY", help="Buscar empresas por campo")
    parser.add_argument("--field", metavar="FIELD", default="nombre",
                        help="Campo en el que buscar (default: nombre)")
    parser.add_argument("--insert", metavar="JSON_STRING", help="Insertar empresa desde JSON")
    parser.add_argument("--update", nargs=2, metavar=("ID", "JSON_STRING"),
                        help="Actualizar empresa: --update ID '{...}'")
    parser.add_argument("--set-status", nargs=2, metavar=("ID", "STATUS"),
                        help="Cambiar status de una empresa")
    parser.add_argument("--add-note", nargs=2, metavar=("ID", "NOTE"),
                        help="Agregar nota a una empresa")
    parser.add_argument("--export-csv", metavar="FILEPATH", help="Exportar a CSV")
    parser.add_argument("--export-json", metavar="FILEPATH", help="Exportar a JSON")
    parser.add_argument("--filter", metavar="JSON_STRING",
                        help="Filtro JSON para --export-csv / --export-json")
    parser.add_argument("--check-url", metavar="URL", help="Verificar si URL ya existe en la DB")
    parser.add_argument("--find-duplicates", action="store_true",
                        help="Encontrar posibles empresas duplicadas")
    parser.add_argument("--incomplete", action="store_true",
                        help="Listar empresas sin email o teléfono")
    parser.add_argument("--log-search", nargs=3, metavar=("QUERY", "TOOL", "NUM_RESULTS"),
                        help="Registrar una búsqueda realizada")
    parser.add_argument("--log-scrape", nargs=3, metavar=("URL", "TOOL", "SUCCESS"),
                        help="Registrar un intento de scraping (SUCCESS=1 o 0)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # --stats
    if args.stats:
        stats = get_stats()
        _print_stats(stats)

    # --search QUERY [--field FIELD]
    if args.search:
        try:
            results = search_empresas(args.search, args.field)
            _print_empresas(results, title=f"BÚSQUEDA '{args.search}' en '{args.field}'")
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    # --insert JSON_STRING
    if args.insert:
        try:
            data = json.loads(args.insert)
            new_id = insert_empresa(data)
            print(f"OK: Empresa insertada con id={new_id}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"ERROR al insertar: {e}", file=sys.stderr)
            sys.exit(1)

    # --update ID JSON_STRING
    if args.update:
        empresa_id, json_str = args.update
        try:
            data = json.loads(json_str)
            ok = update_empresa(int(empresa_id), data)
            if ok:
                print(f"OK: Empresa id={empresa_id} actualizada.")
            else:
                print(f"AVISO: No se encontró empresa con id={empresa_id}.")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"ERROR al actualizar: {e}", file=sys.stderr)
            sys.exit(1)

    # --set-status ID STATUS
    if args.set_status:
        empresa_id, status = args.set_status
        ok = set_status(int(empresa_id), status)
        if ok:
            print(f"OK: Status de id={empresa_id} cambiado a '{status}'.")
        else:
            print(f"AVISO: No se encontró empresa con id={empresa_id}.")

    # --add-note ID NOTE
    if args.add_note:
        empresa_id, note = args.add_note
        ok = add_note(int(empresa_id), note)
        if ok:
            print(f"OK: Nota agregada a id={empresa_id}.")
        else:
            print(f"AVISO: No se encontró empresa con id={empresa_id}.")

    # --export-csv FILEPATH [--filter JSON]
    if args.export_csv:
        filtro = None
        if args.filter:
            try:
                filtro = json.loads(args.filter)
            except json.JSONDecodeError as e:
                print(f"ERROR en --filter JSON: {e}", file=sys.stderr)
                sys.exit(1)
        count = export_csv(args.export_csv, filtro)
        print(f"OK: {count} empresas exportadas a '{args.export_csv}'.")

    # --export-json FILEPATH [--filter JSON]
    if args.export_json:
        filtro = None
        if args.filter:
            try:
                filtro = json.loads(args.filter)
            except json.JSONDecodeError as e:
                print(f"ERROR en --filter JSON: {e}", file=sys.stderr)
                sys.exit(1)
        count = export_json(args.export_json, filtro)
        print(f"OK: {count} empresas exportadas a '{args.export_json}'.")

    # --check-url URL
    if args.check_url:
        exists = url_exists(args.check_url)
        if exists:
            print(f"EXISTE: La URL '{args.check_url}' ya está en la base de datos.")
        else:
            print(f"NUEVA: La URL '{args.check_url}' no está en la base de datos.")

    # --find-duplicates
    if args.find_duplicates:
        dupes = find_duplicates()
        if not dupes:
            print("No se encontraron duplicados potenciales.")
        else:
            print(f"\nDUPLICADOS POTENCIALES ({len(dupes)} grupos):")
            print("-" * 60)
            for d in dupes:
                print(f"  Nombre: {d['nombre_norm']} | Apariciones: {d['cnt']} | IDs: {d['ids']}")
            print("-" * 60)

    # --incomplete
    if args.incomplete:
        rows = get_incomplete()
        if not rows:
            print("Todas las empresas tienen email y teléfono.")
        else:
            print(f"\nEMPRESAS INCOMPLETAS ({len(rows)}):")
            print("-" * 70)
            for e in rows:
                missing = []
                if not e.get("email"):
                    missing.append("email")
                if not e.get("telefono"):
                    missing.append("telefono")
                print(
                    f"  [{e['id']}] {e['nombre'][:35]:35s} | {e.get('ciudad', ''):15s} | falta: {', '.join(missing)}"
                )
            print("-" * 70)

    # --log-search QUERY TOOL NUM_RESULTS
    if args.log_search:
        query, tool, num = args.log_search
        try:
            row_id = log_busqueda(query, tool, int(num))
            print(f"OK: Búsqueda registrada (id={row_id}).")
        except ValueError as e:
            print(f"ERROR en --log-search: {e}", file=sys.stderr)
            sys.exit(1)

    # --log-scrape URL TOOL SUCCESS
    if args.log_scrape:
        url, tool, success_str = args.log_scrape
        exito = success_str.strip() in ("1", "true", "True", "yes")
        row_id = log_scraping(url, tool, exito)
        print(f"OK: Scrape registrado (id={row_id}, exito={exito}).")


if __name__ == "__main__":
    main()

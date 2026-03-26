#!/usr/bin/env python3
"""
api_server.py — Flask API server for the scraping viewer.

Serves paginated empresa data per client, with server-side filtering/sorting.

Usage:
    python scripts/api_server.py [--port 8080]

Endpoints:
    GET  /api/clientes                  — List all clients
    POST /api/clientes                  — Create a client
    GET  /api/clientes/<id>             — Get client details + stats
    PUT  /api/clientes/<id>             — Update a client
    DELETE /api/clientes/<id>           — Delete a client (if no empresas)
    GET  /api/clientes/<id>/empresas    — Paginated empresas for a client
    GET  /api/clientes/<id>/filters     — Filter options for a client
    GET  /api/clientes/<id>/export-csv  — Export CSV for a client
    GET  /api/empresas/sin-cliente      — Empresas without a client assigned
    POST /api/empresas/asignar-cliente  — Assign empresas to a client
    GET  /                              — Serves the viewer
"""

import os
import sys
import csv
import io
import argparse

# Add scripts dir to path so we can import db_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory, Response
import db_utils

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder=None)


# ---------------------------------------------------------------------------
# Viewer routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(os.path.join(PROJECT_ROOT, "viewer"), "index.html")


@app.route("/viewer/<path:filename>")
def viewer_static(filename):
    return send_from_directory(os.path.join(PROJECT_ROOT, "viewer"), filename)


# ---------------------------------------------------------------------------
# API: Clientes
# ---------------------------------------------------------------------------

@app.route("/api/clientes", methods=["GET"])
def list_clientes():
    clientes = db_utils.get_clientes()
    return jsonify(clientes)


@app.route("/api/clientes", methods=["POST"])
def create_cliente():
    data = request.get_json(force=True)
    try:
        new_id = db_utils.insert_cliente(data)
        cliente = db_utils.get_cliente(new_id)
        return jsonify(cliente), 201
    except (ValueError, Exception) as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/clientes/<int:id>", methods=["GET"])
def get_cliente(id):
    cliente = db_utils.get_cliente(id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404
    stats = db_utils.get_cliente_stats(id)
    cliente["stats"] = stats
    return jsonify(cliente)


@app.route("/api/clientes/<int:id>", methods=["PUT"])
def update_cliente(id):
    data = request.get_json(force=True)
    try:
        ok = db_utils.update_cliente(id, data)
        if not ok:
            return jsonify({"error": "Cliente no encontrado"}), 404
        return jsonify(db_utils.get_cliente(id))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/clientes/<int:id>", methods=["DELETE"])
def delete_cliente(id):
    try:
        ok = db_utils.delete_cliente(id)
        if not ok:
            return jsonify({"error": "Cliente no encontrado"}), 404
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------------
# API: Empresas (paginated, per client)
# ---------------------------------------------------------------------------

@app.route("/api/clientes/<int:id>/empresas", methods=["GET"])
def get_empresas(id):
    cliente = db_utils.get_cliente(id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    per_page = min(per_page, 500)  # cap
    search = request.args.get("search", "").strip()
    sort_key = request.args.get("sort", "nombre")
    sort_dir = request.args.get("dir", "asc")

    # Collect column filters
    filtros = {}
    for key in ("ciudad", "estado", "industria", "status"):
        val = request.args.get(key)
        if val:
            filtros[key] = val

    result = db_utils.get_empresas_paginated(
        cliente_id=id,
        page=page,
        per_page=per_page,
        search=search or None,
        filtros=filtros or None,
        sort_key=sort_key,
        sort_dir=sort_dir,
    )
    return jsonify(result)


@app.route("/api/clientes/<int:id>/filters", methods=["GET"])
def get_filters(id):
    opts = db_utils.get_filter_options(cliente_id=id)
    return jsonify(opts)


@app.route("/api/clientes/<int:id>/export-csv", methods=["GET"])
def export_csv(id):
    cliente = db_utils.get_cliente(id)
    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    # Get all empresas for this client (no pagination)
    result = db_utils.get_empresas_paginated(
        cliente_id=id, page=1, per_page=999999
    )
    rows = result["items"]
    if not rows:
        return Response("Sin datos", mimetype="text/plain")

    output = io.StringIO()
    output.write("\ufeff")  # BOM for Excel
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    safe_name = cliente["nombre"].replace(" ", "_").replace("/", "-")
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=empresas_{safe_name}.csv"
        },
    )


# ---------------------------------------------------------------------------
# API: Empresas sin cliente asignado
# ---------------------------------------------------------------------------

@app.route("/api/empresas/sin-cliente", methods=["GET"])
def empresas_sin_cliente():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    per_page = min(per_page, 500)

    with db_utils.get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM empresas WHERE cliente_id IS NULL"
        ).fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            "SELECT * FROM empresas WHERE cliente_id IS NULL ORDER BY nombre COLLATE NOCASE LIMIT ? OFFSET ?",
            (per_page, offset),
        ).fetchall()

    total_pages = max(1, -(-total // per_page))
    return jsonify({
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    })


@app.route("/api/empresas/asignar-cliente", methods=["POST"])
def asignar_cliente():
    """Assign empresas to a client. Body: { cliente_id: int, empresa_ids: [int] }"""
    data = request.get_json(force=True)
    cliente_id = data.get("cliente_id")
    empresa_ids = data.get("empresa_ids", [])

    if not cliente_id or not empresa_ids:
        return jsonify({"error": "Se requiere cliente_id y empresa_ids"}), 400

    with db_utils.get_connection() as conn:
        placeholders = ",".join(["?"] * len(empresa_ids))
        conn.execute(
            f"UPDATE empresas SET cliente_id = ? WHERE id IN ({placeholders})",
            [cliente_id] + empresa_ids,
        )
        conn.commit()

    return jsonify({"ok": True, "updated": len(empresa_ids)})


# ---------------------------------------------------------------------------
# API: Update empresa (for inline editing)
# ---------------------------------------------------------------------------

@app.route("/api/empresas/<int:id>", methods=["PUT"])
def update_empresa(id):
    data = request.get_json(force=True)
    try:
        ok = db_utils.update_empresa(id, data)
        if not ok:
            return jsonify({"error": "Empresa no encontrada"}), 404
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API server para el viewer de empresas")
    parser.add_argument("--port", type=int, default=8080, help="Puerto (default: 8080)")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    args = parser.parse_args()

    print(f"Servidor iniciado en http://{args.host}:{args.port}")
    print(f"Viewer disponible en http://{args.host}:{args.port}/")
    app.run(host=args.host, port=args.port, debug=True)

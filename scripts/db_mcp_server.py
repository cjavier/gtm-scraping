"""
MCP server for client and empresa management using FastMCP.

Provides tools for:
- CRUD de clientes
- Asignar empresas a clientes
- Consultar empresas por cliente
- Stats y filtros
"""
import json
import sys
import os
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import FastMCP
import db_utils

mcp = FastMCP("gtm-db")


# ─── Clientes ───────────────────────────────────────────────────────────────

@mcp.tool()
def crear_cliente(nombre: str, descripcion: str = "", industria_objetivo: str = "", color: str = "#3b82f6") -> str:
    """Crear un nuevo cliente. Cada cliente agrupa un conjunto de empresas scrapeadas.

    Args:
        nombre: Nombre del cliente (obligatorio, debe ser unico).
        descripcion: Descripcion breve del cliente o proyecto.
        industria_objetivo: Industria o sector al que se enfoca este cliente.
        color: Color hex para identificar al cliente en el viewer (ej: #3b82f6).
    """
    try:
        new_id = db_utils.insert_cliente({
            "nombre": nombre,
            "descripcion": descripcion,
            "industria_objetivo": industria_objetivo,
            "color": color,
        })
        cliente = db_utils.get_cliente(new_id)
        return json.dumps({"ok": True, "cliente": cliente}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


@mcp.tool()
def listar_clientes() -> str:
    """Listar todos los clientes con su conteo de empresas.
    Usar esto para saber que clientes existen y cuantas empresas tiene cada uno."""
    clientes = db_utils.get_clientes()
    return json.dumps(clientes, ensure_ascii=False)


@mcp.tool()
def ver_cliente(cliente_id: int) -> str:
    """Ver detalle de un cliente incluyendo estadisticas de sus empresas.

    Args:
        cliente_id: ID del cliente.
    """
    cliente = db_utils.get_cliente(cliente_id)
    if not cliente:
        return json.dumps({"error": "Cliente no encontrado"})
    stats = db_utils.get_cliente_stats(cliente_id)
    cliente["stats"] = stats
    return json.dumps(cliente, ensure_ascii=False)


@mcp.tool()
def actualizar_cliente(cliente_id: int, nombre: str = None, descripcion: str = None, industria_objetivo: str = None, color: str = None) -> str:
    """Actualizar datos de un cliente existente.

    Args:
        cliente_id: ID del cliente a actualizar.
        nombre: Nuevo nombre (opcional).
        descripcion: Nueva descripcion (opcional).
        industria_objetivo: Nueva industria objetivo (opcional).
        color: Nuevo color hex (opcional).
    """
    data = {}
    if nombre is not None: data["nombre"] = nombre
    if descripcion is not None: data["descripcion"] = descripcion
    if industria_objetivo is not None: data["industria_objetivo"] = industria_objetivo
    if color is not None: data["color"] = color

    if not data:
        return json.dumps({"error": "No se proporcionaron campos para actualizar"})

    try:
        ok = db_utils.update_cliente(cliente_id, data)
        if not ok:
            return json.dumps({"error": "Cliente no encontrado"})
        return json.dumps({"ok": True, "cliente": db_utils.get_cliente(cliente_id)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


@mcp.tool()
def eliminar_cliente(cliente_id: int) -> str:
    """Eliminar un cliente. Solo funciona si el cliente no tiene empresas asociadas.

    Args:
        cliente_id: ID del cliente a eliminar.
    """
    try:
        ok = db_utils.delete_cliente(cliente_id)
        if not ok:
            return json.dumps({"error": "Cliente no encontrado"})
        return json.dumps({"ok": True})
    except ValueError as e:
        return json.dumps({"ok": False, "error": str(e)})


# ─── Empresas por cliente ───────────────────────────────────────────────────

@mcp.tool()
def buscar_empresas_cliente(
    cliente_id: int,
    busqueda: str = "",
    ciudad: str = "",
    estado: str = "",
    industria: str = "",
    status: str = "",
    pagina: int = 1,
    por_pagina: int = 50,
) -> str:
    """Buscar empresas de un cliente con filtros y paginacion.

    Args:
        cliente_id: ID del cliente.
        busqueda: Texto libre para buscar en nombre, sitio_web, email, telefono, ciudad, estado, industria.
        ciudad: Filtrar por ciudad exacta.
        estado: Filtrar por estado exacto.
        industria: Filtrar por industria exacta.
        status: Filtrar por status (nuevo, verificado, descartado, contactado).
        pagina: Numero de pagina (default 1).
        por_pagina: Registros por pagina (default 50, max 500).
    """
    filtros = {}
    if ciudad: filtros["ciudad"] = ciudad
    if estado: filtros["estado"] = estado
    if industria: filtros["industria"] = industria
    if status: filtros["status"] = status

    result = db_utils.get_empresas_paginated(
        cliente_id=cliente_id,
        page=pagina,
        per_page=min(por_pagina, 500),
        search=busqueda or None,
        filtros=filtros or None,
    )
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def filtros_disponibles(cliente_id: int) -> str:
    """Obtener los valores unicos disponibles para filtrar empresas de un cliente.
    Retorna listas de ciudades, estados, industrias y status existentes.

    Args:
        cliente_id: ID del cliente.
    """
    opts = db_utils.get_filter_options(cliente_id=cliente_id)
    return json.dumps(opts, ensure_ascii=False)


# ─── Asignacion de empresas ────────────────────────────────────────────────

@mcp.tool()
def asignar_empresas_a_cliente(cliente_id: int, empresa_ids: list[int]) -> str:
    """Asignar una o varias empresas a un cliente.

    Args:
        cliente_id: ID del cliente destino.
        empresa_ids: Lista de IDs de empresas a asignar.
    """
    if not empresa_ids:
        return json.dumps({"error": "Se requiere al menos un empresa_id"})

    cliente = db_utils.get_cliente(cliente_id)
    if not cliente:
        return json.dumps({"error": "Cliente no encontrado"})

    with db_utils.get_connection() as conn:
        placeholders = ",".join(["?"] * len(empresa_ids))
        conn.execute(
            f"UPDATE empresas SET cliente_id = ? WHERE id IN ({placeholders})",
            [cliente_id] + list(empresa_ids),
        )
        conn.commit()

    return json.dumps({"ok": True, "asignadas": len(empresa_ids), "cliente": cliente["nombre"]}, ensure_ascii=False)


@mcp.tool()
def empresas_sin_cliente(pagina: int = 1, por_pagina: int = 50) -> str:
    """Listar empresas que no tienen cliente asignado.
    Util para saber que empresas faltan por asignar despues de un scraping.

    Args:
        pagina: Numero de pagina (default 1).
        por_pagina: Registros por pagina (default 50).
    """
    with db_utils.get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM empresas WHERE cliente_id IS NULL"
        ).fetchone()[0]
        offset = (pagina - 1) * por_pagina
        rows = conn.execute(
            "SELECT id, nombre, sitio_web, ciudad, estado, industria, status FROM empresas WHERE cliente_id IS NULL ORDER BY nombre COLLATE NOCASE LIMIT ? OFFSET ?",
            (por_pagina, offset),
        ).fetchall()

    total_pages = max(1, -(-total // por_pagina))
    return json.dumps({
        "items": [dict(r) for r in rows],
        "total": total,
        "pagina": pagina,
        "total_paginas": total_pages,
    }, ensure_ascii=False)


# ─── Stats ──────────────────────────────────────────────────────────────────

@mcp.tool()
def stats_cliente(cliente_id: int) -> str:
    """Obtener estadisticas de un cliente: total empresas, con email, con telefono, por status.

    Args:
        cliente_id: ID del cliente.
    """
    cliente = db_utils.get_cliente(cliente_id)
    if not cliente:
        return json.dumps({"error": "Cliente no encontrado"})
    stats = db_utils.get_cliente_stats(cliente_id)
    stats["cliente"] = cliente["nombre"]
    return json.dumps(stats, ensure_ascii=False)


@mcp.tool()
def stats_generales() -> str:
    """Obtener estadisticas generales de toda la base de datos, incluyendo conteo por cliente."""
    stats = db_utils.get_stats()
    clientes = db_utils.get_clientes()
    stats["clientes"] = [{"id": c["id"], "nombre": c["nombre"], "total_empresas": c["total_empresas"]} for c in clientes]

    with db_utils.get_connection() as conn:
        sin_cliente = conn.execute("SELECT COUNT(*) FROM empresas WHERE cliente_id IS NULL").fetchone()[0]
    stats["empresas_sin_cliente"] = sin_cliente

    return json.dumps(stats, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")

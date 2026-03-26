# Skill: Gestión de Base de Datos

## Cuándo usar este skill
Cuando el usuario quiere consultar, modificar, exportar o analizar los datos almacenados.

## Gestión de clientes (MCP gtm-db)
- Crear cliente: MCP `crear_cliente`(nombre, descripcion, industria_objetivo, color)
- Listar clientes: MCP `listar_clientes`
- Ver detalle + stats: MCP `ver_cliente`(cliente_id)
- Editar cliente: MCP `actualizar_cliente`(cliente_id, ...)
- Eliminar cliente: MCP `eliminar_cliente`(cliente_id) — solo si no tiene empresas

## Consultas por cliente (MCP gtm-db)
- Buscar empresas: MCP `buscar_empresas_cliente`(cliente_id, busqueda, ciudad, estado, industria, status, pagina)
- Ver filtros disponibles: MCP `filtros_disponibles`(cliente_id)
- Stats del cliente: MCP `stats_cliente`(cliente_id)
- Stats generales: MCP `stats_generales`

## Asignación de empresas
- Ver sin asignar: MCP `empresas_sin_cliente`(pagina)
- Asignar a cliente: MCP `asignar_empresas_a_cliente`(cliente_id, empresa_ids)

## Consultas CLI (para operaciones que no cubra el MCP)
- "¿Cuántas empresas tenemos?" → python scripts/db_utils.py --stats
- "Muéstrame las de Monterrey" → python scripts/db_utils.py --search "Monterrey" --field ciudad
- "Exporta todo a CSV" → python scripts/db_utils.py --export-csv output/empresas.csv

## Actualización de datos
- Para actualizar un campo: python scripts/db_utils.py --update [ID] '{"campo": "valor"}'
- Para cambiar status: python scripts/db_utils.py --set-status [ID] verificado
- Para agregar nota: python scripts/db_utils.py --add-note [ID] "nota aquí"

## Viewer web
1. Iniciar: python scripts/api_server.py --port 8080
2. Abrir: http://localhost:8080
3. Navegar: seleccionar cliente → ver empresas paginadas → filtrar/buscar/editar inline
4. Exportar CSV por cliente desde el viewer

**Ya no es necesario exportar JSON manualmente** — el viewer ahora lee directo de la DB via API.

## Mantenimiento
- Detectar duplicados: python scripts/db_utils.py --find-duplicates
- Empresas sin datos completos: python scripts/db_utils.py --incomplete
- Empresas sin cliente: MCP `empresas_sin_cliente`
- Backup: cp db/empresas.db db/empresas_backup_$(date +%Y%m%d).db

# Proyecto: Sistema de Scraping de Empresas

## Descripcion
Sistema multi-cliente para investigar y construir bases de datos de empresas
mexicanas usando busqueda SERP y scraping de sitios web.

## Ambiente
- Python virtual environment en ./venv (activar con source venv/bin/activate)
- Variables de ambiente en .env
- Base de datos SQLite en db/empresas.db
- MCP servers configurados: Crawl4AI (local), Firecrawl (API), GTM-DB (gestion de clientes y empresas)

## Skills disponibles
Lee los skills en ./skills/ antes de ejecutar tareas:
- skills/serp-research.md → Para busquedas en Google
- skills/site-scraper.md → Para scrapear sitios individuales
- skills/data-extraction.md → Para estructurar datos de markdown
- skills/db-management.md → Para consultar y gestionar la DB

## Arquitectura del sistema

### Modelo de datos
El sistema organiza los datos por **clientes**. Cada cliente representa un
proyecto o cuenta para la cual se investigan empresas.

- **clientes**: id, nombre, descripcion, industria_objetivo, color
- **empresas**: cada empresa tiene un `cliente_id` que la asocia a un cliente
- **busquedas** y **scraping_log**: logs de actividad (no tienen cliente_id)

### Flujo de trabajo tipico
1. Crear un cliente (via MCP `crear_cliente` o via el viewer)
2. Buscar empresas con SERP pasando el `cliente_id`
3. Scrapear sitios para enriquecer datos
4. Revisar y filtrar en el viewer (http://localhost:8080)
5. Exportar CSV por cliente

### Componentes
- **scripts/db_utils.py** — Funciones de base de datos (CRUD empresas y clientes)
- **scripts/api_server.py** — API Flask + viewer (levantar con `python scripts/api_server.py`)
- **scripts/db_mcp_server.py** — MCP server para gestion de clientes y empresas
- **scripts/serper_search.py** — Busquedas en Google via Serper.dev
- **scripts/crawl4ai_scraper.py** — Scraping de sitios web
- **scripts/crawl4ai_server.py** — MCP server de Crawl4AI
- **viewer/index.html** — Interfaz web (servida por api_server.py)

## MCP Server: gtm-db

El MCP server `gtm-db` expone estas herramientas para gestionar clientes y empresas:

### Gestion de clientes
- **crear_cliente**(nombre, descripcion, industria_objetivo, color) — Crear un nuevo cliente
- **listar_clientes**() — Ver todos los clientes con conteo de empresas
- **ver_cliente**(cliente_id) — Detalle de un cliente con stats
- **actualizar_cliente**(cliente_id, nombre, descripcion, ...) — Editar un cliente
- **eliminar_cliente**(cliente_id) — Eliminar cliente (solo si no tiene empresas)

### Consulta de empresas
- **buscar_empresas_cliente**(cliente_id, busqueda, ciudad, estado, industria, status, pagina) — Buscar empresas con filtros y paginacion
- **filtros_disponibles**(cliente_id) — Valores unicos para filtrar (ciudades, estados, etc.)

### Asignacion
- **asignar_empresas_a_cliente**(cliente_id, empresa_ids) — Asignar empresas a un cliente
- **empresas_sin_cliente**(pagina) — Ver empresas sin cliente asignado

### Estadisticas
- **stats_cliente**(cliente_id) — Stats de un cliente especifico
- **stats_generales**() — Stats de toda la DB incluyendo conteo por cliente

## Reglas de operacion

### Clientes
- **SIEMPRE** verificar o preguntar a que cliente corresponde el trabajo antes de buscar/scrapear
- Al hacer busquedas SERP o scraping, pasar el `cliente_id` para que se asocie automaticamente
- Si hay empresas sin cliente, informar al usuario y sugerir asignarlas
- Usar `listar_clientes` del MCP para verificar clientes existentes antes de crear uno nuevo

### Jerarquia de herramientas SERP
1. Para <20 busquedas: Sugerir Chrome al usuario
2. Para >20 busquedas: Usar Serper.dev (scripts/serper_search.py)
3. Si Serper falla: Usar firecrawl_search (MCP)

### Jerarquia de herramientas Scraping
1. Primario: Crawl4AI (scripts/crawl4ai_scraper.py o MCP crawl4ai)
2. Si falla: Pilot (scripts/pilot_scraper.py) — navegador real headed con stealth
3. Si falla: Firecrawl scrape (MCP firecrawl)
4. Si todos fallan: Sugerir Chrome manual al usuario

### Siempre antes de scrapear
- Verificar si la URL ya existe en la DB para evitar duplicados
- Preferir scrapear /contacto, /nosotros, /servicios ademas del home

### Siempre despues de scrapear
- Insertar datos en la DB con el `cliente_id` correcto
- Loggear el resultado (exito/fallo, herramienta, tiempo)
- Informar al usuario que datos se obtuvieron y cuales faltan

### Idioma
- Los queries a Google deben ser en espanol
- La localizacion debe ser Mexico (gl=mx, hl=es)
- La interfaz y comunicacion con el usuario es en espanol

### Base de datos
- Todas las operaciones de DB usan scripts/db_utils.py
- No modificar el schema sin consultarlo primero
- Siempre usar parametros preparados (nunca string interpolation en SQL)
- Hacer backup antes de operaciones masivas

## Viewer web

El viewer es una aplicacion React servida por Flask con paginacion server-side.

### Como iniciar
```bash
source venv/bin/activate
python scripts/api_server.py --port 8080
# Abrir http://localhost:8080
```

### Paginas
- **/** — Landing con grid de tarjetas de clientes. Crear, editar y eliminar clientes.
- **#/cliente/{id}** — Tabla de empresas del cliente con:
  - Paginacion server-side (100 por pagina)
  - Filtros por ciudad, estado, industria, status
  - Busqueda global con debounce
  - Sorting por columnas
  - Edicion inline (doble clic) que persiste en DB
  - Export CSV
- **#/sin-cliente** — Empresas sin asignar, con seleccion multiple y asignacion masiva

### API endpoints (Flask)
- `GET /api/clientes` — Listar clientes
- `POST /api/clientes` — Crear cliente (body JSON)
- `GET /api/clientes/<id>` — Detalle + stats
- `PUT /api/clientes/<id>` — Actualizar cliente
- `DELETE /api/clientes/<id>` — Eliminar cliente
- `GET /api/clientes/<id>/empresas?page=&search=&ciudad=&sort=&dir=` — Empresas paginadas
- `GET /api/clientes/<id>/filters` — Opciones de filtro
- `GET /api/clientes/<id>/export-csv` — Descarga CSV
- `GET /api/empresas/sin-cliente?page=` — Empresas sin cliente
- `POST /api/empresas/asignar-cliente` — Asignar empresas (body: {cliente_id, empresa_ids})
- `PUT /api/empresas/<id>` — Editar empresa inline

## Comandos rapidos
- Iniciar viewer + API: `python scripts/api_server.py --port 8080`
- Buscar en Google: `python scripts/serper_search.py "[query]" --num 20 --country mx`
- Scrapear sitio: `python scripts/crawl4ai_scraper.py "[URL]" --extract-contacts`
- Scrapear (fallback navegador): `python scripts/pilot_scraper.py "[URL]" --full --pages /contacto /nosotros`
- Stats de la DB: `python scripts/db_utils.py --stats`
- Exportar CSV: `python scripts/db_utils.py --export-csv output/empresas.csv`
- Exportar JSON: `python scripts/db_utils.py --export-json output/empresas.json`

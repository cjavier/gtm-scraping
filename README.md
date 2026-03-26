# GTM Scraping

Sistema multi-cliente para investigar y construir bases de datos de empresas usando Claude Code como orquestador. Combina busqueda SERP, scraping web y un viewer local con paginacion server-side.

Pensado para equipos de ventas B2B, agencias de generacion de leads o cualquier operacion GTM (Go-To-Market) que necesite construir listas de prospectos a partir de busquedas en Google y scraping de sitios web.

## Como funciona

```
                        Claude Code (orquestador)
                       /          |              \
              MCP crawl4ai    MCP firecrawl    MCP gtm-db
              (scraping)      (fallback)       (clientes + DB)
                       \          |              /
                        SQLite (empresas.db)
                               |
                        Flask API + Viewer
                        http://localhost:8080
```

1. **Creas un cliente** desde el viewer o via MCP
2. **Buscas empresas** en Google con Serper.dev — se guardan automaticamente en la DB asociadas al cliente
3. **Scrapeas sitios** con Crawl4AI para enriquecer datos (telefono, email, contactos, redes sociales)
4. **Revisas y exportas** desde el viewer web con filtros, busqueda y paginacion

Claude Code orquesta todo el flujo usando las herramientas MCP y los skills definidos en el proyecto. Tu le dices "busca constructoras en Monterrey para el cliente X" y el hace el resto.

## Que incluye

| Componente | Descripcion |
|---|---|
| `scripts/serper_search.py` | Busqueda en Google via Serper.dev con auto-guardado en DB |
| `scripts/crawl4ai_scraper.py` | Scraping de sitios web con extraccion de contactos (regex para formatos mexicanos) |
| `scripts/db_utils.py` | CRUD completo: empresas, clientes, busquedas, logs, exports |
| `scripts/api_server.py` | API Flask con paginacion server-side + sirve el viewer |
| `scripts/db_mcp_server.py` | MCP server con 11 herramientas para gestion de clientes y empresas |
| `scripts/crawl4ai_server.py` | MCP server para crawling de paginas web |
| `viewer/index.html` | App React con grid de clientes, tabla de empresas, edicion inline |
| `skills/*.md` | Instrucciones para Claude Code sobre como ejecutar cada tarea |

## Requisitos

- **Python 3.9+**
- **Node.js 18+**
- **Claude Code** (CLI de Anthropic) — para orquestar las herramientas MCP
- **API key de Serper.dev** — para busquedas en Google ([serper.dev](https://serper.dev), 2,500 busquedas gratis)
- **API key de Firecrawl** (opcional) — scraping de fallback ([firecrawl.dev](https://firecrawl.dev), 500 creditos gratis)

## Instalacion

```bash
# Clonar el repositorio
git clone https://github.com/cjavier/gtm-scraping.git
cd gtm-scraping

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias Python
pip install -r requirements.txt

# Instalar Playwright (navegador headless para Crawl4AI)
playwright install chromium

# Instalar dependencias Node (Firecrawl MCP)
npm install

# Configurar variables de ambiente
cp .env.example .env
# Editar .env con tus API keys
```

La base de datos SQLite se crea automaticamente en `db/empresas.db` la primera vez que se ejecuta cualquier script.

## Configuracion de MCP

Claude Code necesita rutas absolutas para los MCP servers. Copia el template y reemplaza las rutas:

```bash
cp .mcp.json.example .mcp.json
```

Edita `.mcp.json` y reemplaza `/RUTA/A/TU/PROYECTO` con la ruta absoluta donde clonaste el repo. Por ejemplo, si clonaste en `/Users/tu-usuario/gtm-scraping`:

```json
{
  "mcpServers": {
    "crawl4ai": {
      "command": "/Users/tu-usuario/gtm-scraping/venv/bin/python",
      "args": ["/Users/tu-usuario/gtm-scraping/scripts/crawl4ai_server.py"]
    },
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": { "FIRECRAWL_API_KEY": "${FIRECRAWL_API_KEY}" }
    },
    "gtm-db": {
      "command": "/Users/tu-usuario/gtm-scraping/venv/bin/python",
      "args": ["/Users/tu-usuario/gtm-scraping/scripts/db_mcp_server.py"]
    }
  }
}
```

> **Nota:** `.mcp.json` esta en `.gitignore` porque contiene rutas locales. Cada usuario genera el suyo a partir de `.mcp.json.example`.

## Uso

### Iniciar el viewer

```bash
source venv/bin/activate
python scripts/api_server.py --port 8080
```

Abre http://localhost:8080. Desde ahi puedes:
- Crear y gestionar clientes
- Ver empresas por cliente con filtros y paginacion
- Editar datos inline (doble clic en cualquier celda)
- Exportar CSV por cliente
- Asignar empresas sin cliente

### Usar con Claude Code

Abre Claude Code en el directorio del proyecto. Los MCP servers se cargan automaticamente.

**Crear un cliente:**
> "Crea un cliente llamado Acme Corp, industria construccion"

**Buscar empresas:**
> "Busca constructoras en Monterrey para Acme Corp, 20 resultados"

**Scrapear un sitio:**
> "Scrapea https://constructora-ejemplo.com y extrae los datos de contacto para Acme Corp"

**Consultar datos:**
> "Cuantas empresas tiene Acme Corp? Cuantas tienen email?"

Claude Code usa los skills en `skills/` para saber que herramienta usar en cada paso y sigue la jerarquia de fallback automaticamente.

### CLI directo (sin Claude Code)

```bash
# Buscar en Google (guarda automaticamente en DB)
python scripts/serper_search.py "agencias de marketing CDMX" --num 20

# Scrapear un sitio
python scripts/crawl4ai_scraper.py "https://ejemplo.com" --extract-contacts --save

# Ver estadisticas
python scripts/db_utils.py --stats

# Buscar en la DB
python scripts/db_utils.py --search "Monterrey" --field ciudad

# Exportar
python scripts/db_utils.py --export-csv output/empresas.csv
python scripts/db_utils.py --export-json output/empresas.json
```

## Herramientas MCP disponibles

### gtm-db (gestion de clientes y datos)

| Herramienta | Descripcion |
|---|---|
| `crear_cliente` | Crear un nuevo cliente con nombre, descripcion, industria y color |
| `listar_clientes` | Ver todos los clientes con conteo de empresas |
| `ver_cliente` | Detalle de un cliente con estadisticas |
| `actualizar_cliente` | Editar datos de un cliente |
| `eliminar_cliente` | Eliminar un cliente (solo si no tiene empresas) |
| `buscar_empresas_cliente` | Buscar empresas con filtros y paginacion server-side |
| `filtros_disponibles` | Valores unicos para filtrar (ciudades, estados, industrias) |
| `asignar_empresas_a_cliente` | Asignar empresas existentes a un cliente |
| `empresas_sin_cliente` | Ver empresas sin cliente asignado |
| `stats_cliente` | Estadisticas de un cliente especifico |
| `stats_generales` | Estadisticas de toda la base de datos |

### crawl4ai (scraping web)

| Herramienta | Descripcion |
|---|---|
| `crawl_webpage` | Scrapear una pagina y devolver markdown |
| `crawl_website` | Scrapear multiples paginas de un sitio |

## Modelo de datos

```
clientes 1───N empresas
                  │
                  ├── datos de la empresa (nombre, sitio, telefono, email, direccion...)
                  ├── clasificacion (industria, ciudad, estado, status)
                  ├── contacto principal (nombre, cargo, email, telefono)
                  └── metadata (fuente, query de origen, notas, fechas)
```

**Status de empresas:** `nuevo` → `verificado` → `contactado` / `descartado`

La base de datos tambien registra logs de busquedas y scraping para tracking.

## Estructura del proyecto

```
gtm-scraping/
├── scripts/
│   ├── api_server.py          # Flask API + viewer (python scripts/api_server.py)
│   ├── db_utils.py            # Funciones de base de datos
│   ├── db_mcp_server.py       # MCP server: clientes y empresas
│   ├── crawl4ai_server.py     # MCP server: scraping
│   ├── crawl4ai_scraper.py    # CLI: scraping con extraccion de contactos
│   └── serper_search.py       # CLI: busqueda en Google
├── db/
│   ├── schema.sql             # Schema de la base de datos
│   └── queries.sql            # Queries SQL de referencia
├── viewer/
│   └── index.html             # App React (servida por api_server.py)
├── skills/
│   ├── serp-research.md       # Instrucciones para busqueda SERP
│   ├── site-scraper.md        # Instrucciones para scraping
│   ├── data-extraction.md     # Instrucciones para extraccion de datos
│   └── db-management.md       # Instrucciones para gestion de DB
├── output/                    # Exports CSV/JSON (gitignored)
├── .mcp.json.example          # Template de configuracion MCP (copiar a .mcp.json)
├── .env.example               # Template de variables de ambiente
├── requirements.txt           # Dependencias Python
├── package.json               # Dependencia Node (firecrawl-mcp)
└── CLAUDE.md                  # Instrucciones operativas para Claude Code
```

## API del viewer

El viewer corre sobre Flask y expone estos endpoints:

```
GET    /api/clientes                         Lista de clientes
POST   /api/clientes                         Crear cliente
GET    /api/clientes/:id                     Detalle + stats
PUT    /api/clientes/:id                     Actualizar cliente
DELETE /api/clientes/:id                     Eliminar cliente
GET    /api/clientes/:id/empresas            Empresas paginadas (?page=&search=&ciudad=&sort=&dir=)
GET    /api/clientes/:id/filters             Opciones de filtro
GET    /api/clientes/:id/export-csv          Descarga CSV
GET    /api/empresas/sin-cliente             Empresas sin asignar
POST   /api/empresas/asignar-cliente         Asignacion masiva
PUT    /api/empresas/:id                     Edicion inline
```

## Jerarquia de fallback

El sistema tiene fallbacks automaticos para cada operacion:

**Busqueda SERP:**
1. Chrome (volumen bajo, < 20 busquedas)
2. Serper.dev (volumen alto, automatizado)
3. Firecrawl search (si Serper falla)

**Scraping:**
1. Crawl4AI (primario, headless Chromium)
2. Firecrawl (fallback API)
3. Chrome manual (ultimo recurso)

## Licencia

MIT

# GTM Scraping

**El proceso de prospección que hoy hacen tus vendedores manualmente — pero 100% orquestado por inteligencia artificial.**

Piensa en cómo funciona hoy: alguien de tu equipo abre Google, busca empresas de su mercado, entra a cada sitio web, copia teléfonos y emails en un Excel, y repite eso cientos de veces. Es lento, tedioso y se pierden datos.

GTM Scraping automatiza todo ese flujo. Le dices a la IA qué tipo de empresas necesitas, en qué ciudad o industria, y ella busca en Google, entra a cada sitio web, extrae los datos de contacto y te los organiza en una base de datos lista para tu equipo de ventas.

## El problema que resuelve

Si vendes B2B, sabes que el primer paso es siempre el mismo: **encontrar a quién venderle**. Construir esa lista de prospectos es un trabajo manual que consume horas, especialmente si operas en un nicho donde no existe un directorio listo para comprar.

Con esta herramienta:

- **Si los datos de tu mercado existen en algún lugar de internet, esta aplicación los va a encontrar por ti.** No importa qué tan segmentado sea tu nicho — si las empresas tienen sitio web, las encuentra.
- **Mapea tu Total Addressable Market de verdad.** No estimas con promedios de industria — construyes la lista real, empresa por empresa, con datos reales.
- **Corre 100% local.** Tus datos de prospectos no pasan por servicios de terceros. Todo queda en tu máquina.
- **Cuesta casi nada.** Las herramientas que usa son en su mayoría locales y gratuitas. Las APIs externas tienen tiers gratuitos generosos (2,500 búsquedas, 500 scrapes).
- **Soporta múltiples clientes.** Si eres agencia o manejas varias cuentas, cada cliente tiene su propio espacio con datos separados.

## Cómo funciona

Le hablas a Claude Code en lenguaje natural. Él decide qué herramientas usar, en qué orden, y maneja los errores solo.

```
Tú:   "Busca clínicas de neuropsicología en Mérida para el cliente NeuroVentas"

IA:   1. Crea el cliente NeuroVentas (si no existe)
      2. Busca en Google "clínicas neuropsicología Mérida"
      3. Guarda las 18 empresas encontradas en la base de datos
      4. Entra a cada sitio web y extrae teléfono, email, dirección, servicios
      5. Busca al fundador o director en cada sitio
      6. Te reporta: "18 empresas encontradas, 14 con email, 11 con teléfono directo"
```

Después abres el viewer en tu navegador, filtras, revisas y exportas el CSV listo para tu CRM.

### La IA toma decisiones por ti

El sistema tiene múltiples herramientas y elige la mejor según la situación:

**Para buscar empresas:**
- Si son pocas búsquedas, usa el navegador directamente
- Si son muchas, usa la API de Serper.dev (2,500 búsquedas gratis)
- Si esa API falla, cambia automáticamente a Firecrawl

**Para entrar a sitios web:**
- Primero intenta con Crawl4AI (gratuito, corre local en tu máquina)
- Si el sitio lo bloquea, cambia a Firecrawl (API con 500 créditos gratis)
- Si ambos fallan, te pide que abras el sitio manualmente en Chrome

No tienes que saber cuál herramienta usar. La IA evalúa, decide y si algo falla, cambia de estrategia sola.

## Qué datos extrae

De cada empresa:
- Nombre, sitio web, teléfono, email
- Dirección, ciudad, estado
- Industria, servicios, descripción
- Redes sociales (Facebook, LinkedIn, Instagram)

Del contacto principal (fundador, director, dueño):
- Nombre completo y cargo
- Email y teléfono directo
- Perfil de LinkedIn

Todos los datos se guardan organizados por cliente, listos para exportar a CSV o conectar con tu CRM.

## El viewer

Una interfaz web local donde ves todo lo que la IA encontró:

- **Pantalla de clientes** — cada cliente es una tarjeta con su conteo de empresas
- **Tabla de empresas** — con filtros por ciudad, estado, industria y status
- **Búsqueda instantánea** — encuentra cualquier empresa en milisegundos
- **Edición inline** — doble clic en cualquier celda para corregir datos
- **Export CSV** — un clic para descargar la lista filtrada

Corre en `http://localhost:8080` y carga rápido aunque tengas miles de registros (paginación server-side).

---

## Instalación

### Requisitos

- **Python 3.9+** y **Node.js 18+**
- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** (CLI de Anthropic)
- **API key de [Serper.dev](https://serper.dev)** — para búsquedas en Google (2,500 gratis)
- **API key de [Firecrawl](https://firecrawl.dev)** (opcional) — scraping de fallback (500 créditos gratis)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/cjavier/gtm-scraping.git
cd gtm-scraping

# 2. Crear entorno Python e instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 3. Instalar dependencia Node
npm install

# 4. Configurar tus API keys
cp .env.example .env
# Editar .env con tus keys de Serper.dev y Firecrawl
```

### Configurar MCP para Claude Code

Claude Code se conecta a las herramientas del proyecto via MCP. Copia el template y reemplaza las rutas con la ubicación de tu proyecto:

```bash
cp .mcp.json.example .mcp.json
```

Edita `.mcp.json` y cambia `/RUTA/A/TU/PROYECTO` por la ruta real. Ejemplo:

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

La base de datos se crea automáticamente la primera vez que ejecutas cualquier comando.

---

## Uso

### Con Claude Code (recomendado)

Abre Claude Code en el directorio del proyecto. Las herramientas se cargan automáticamente.

**Crear un cliente:**
> "Crea un cliente llamado Acme Corp, industria construcción"

**Buscar empresas:**
> "Busca constructoras en Monterrey para Acme Corp, 20 resultados"

**Scrapear un sitio:**
> "Scrapea constructora-ejemplo.com y extrae los datos de contacto para Acme Corp"

**Consultar datos:**
> "¿Cuántas empresas tiene Acme Corp? ¿Cuántas tienen email?"

**Scrapear en lote:**
> "Scrapea todas las empresas de Acme Corp que todavía no tienen teléfono"

### Viewer web

```bash
source venv/bin/activate
python scripts/api_server.py --port 8080
# Abrir http://localhost:8080
```

### CLI directo

También puedes usar los scripts directamente sin Claude Code:

```bash
# Buscar en Google (guarda automáticamente)
python scripts/serper_search.py "agencias de marketing CDMX" --num 20

# Scrapear un sitio
python scripts/crawl4ai_scraper.py "https://ejemplo.com" --extract-contacts --save

# Ver estadísticas
python scripts/db_utils.py --stats

# Exportar
python scripts/db_utils.py --export-csv output/empresas.csv
```

---

## Arquitectura

Para quienes quieran entender o extender el sistema:

```
gtm-scraping/
├── scripts/
│   ├── api_server.py          # API Flask + sirve el viewer web
│   ├── db_utils.py            # Funciones de base de datos (CRUD, exports, stats)
│   ├── db_mcp_server.py       # MCP: 11 herramientas de gestión de clientes y datos
│   ├── crawl4ai_server.py     # MCP: scraping de páginas web
│   ├── crawl4ai_scraper.py    # CLI: scraping con extracción de contactos
│   └── serper_search.py       # CLI: búsqueda en Google via Serper.dev
├── db/
│   └── schema.sql             # Esquema de la base de datos
├── viewer/
│   └── index.html             # Interfaz web (React + Tailwind)
├── skills/                    # Instrucciones que Claude Code sigue para cada tarea
├── .mcp.json.example          # Template de configuración MCP
├── .env.example               # Template de variables de ambiente
├── requirements.txt           # Dependencias Python
└── CLAUDE.md                  # Reglas operativas para Claude Code
```

### Modelo de datos

```
clientes 1───N empresas
                  ├── datos empresa (nombre, sitio, teléfono, email, dirección, servicios)
                  ├── clasificación (industria, ciudad, estado, status)
                  ├── contacto principal (nombre, cargo, email, teléfono, LinkedIn)
                  └── trazabilidad (fuente, query de origen, fecha, notas)
```

**Ciclo de vida:** `nuevo` → `verificado` → `contactado` / `descartado`

### Herramientas MCP (gtm-db)

| Herramienta | Qué hace |
|---|---|
| `crear_cliente` | Crear un nuevo cliente |
| `listar_clientes` | Ver todos los clientes con conteo de empresas |
| `ver_cliente` | Detalle y estadísticas de un cliente |
| `actualizar_cliente` / `eliminar_cliente` | Editar o borrar un cliente |
| `buscar_empresas_cliente` | Buscar empresas con filtros y paginación |
| `asignar_empresas_a_cliente` | Mover empresas a un cliente |
| `empresas_sin_cliente` | Ver empresas pendientes de asignar |
| `stats_cliente` / `stats_generales` | Métricas de datos recolectados |

### API del viewer

```
GET/POST   /api/clientes              Listar / crear clientes
GET/PUT/DEL /api/clientes/:id         Ver / editar / borrar cliente
GET        /api/clientes/:id/empresas  Empresas paginadas con filtros
GET        /api/clientes/:id/export-csv Descarga CSV
POST       /api/empresas/asignar-cliente Asignación masiva
PUT        /api/empresas/:id           Edición inline
```

## Licencia

MIT

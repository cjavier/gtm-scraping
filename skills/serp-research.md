# Skill: Investigación SERP

## Cuándo usar este skill
Cuando el usuario quiere buscar empresas, negocios o información en Google.

## Decisión de herramienta

### Usar Chrome (sugerir al usuario)
- Volumen bajo: menos de 20 búsquedas
- El usuario quiere explorar resultados visualmente
- Necesita interacción con los resultados (navegar, explorar)
- Di: "Para esta búsqueda te sugiero usar Claude for Chrome directamente en tu navegador. Busca [query] y yo puedo ayudarte a procesar los resultados después."

### Usar Serper.dev (automático)
- Volumen medio-alto: más de 20 búsquedas
- Necesita datos estructurados programáticamente
- Es parte de un pipeline automatizado
- Ejecutar: python scripts/serper_search.py "[query]" --num [N] --country mx --lang es

### Fallback a Firecrawl search
- Serper.dev falla o se acabaron los créditos gratuitos
- Usar la tool firecrawl_search del MCP server

## Parámetros importantes para México
- Country: mx
- Language: es
- Para búsquedas locales, incluir la ciudad en el query: "constructoras en Monterrey"
- Para búsquedas nacionales: "empresas de construcción México"

## Cliente obligatorio
**ANTES de buscar, siempre identificar el cliente:**
1. Preguntar al usuario: "¿Para qué cliente es esta búsqueda?"
2. Si no existe, crearlo con el MCP `crear_cliente`
3. Pasar el `cliente_id` para que las empresas se asocien al cliente correcto

## Guardado automático en DB
El script serper_search.py guarda automáticamente en la DB:
- La búsqueda en la tabla `busquedas` (log)
- Las empresas encontradas en la tabla `empresas`, filtrando:
  - Directorios genéricos (Doctoralia, TopDoctors, Yelp, etc.)
  - URLs que ya existan en la DB (duplicados)
- Los datos iniciales guardados son: nombre (del title), sitio_web (URL), descripcion (snippet), fuente="serp", query_origen
- El `cliente_id` se asocia si se pasa como parámetro

No necesitas guardar manualmente. Si NO quieres guardar, usa `--no-save`.

## Post-búsqueda
1. Revisar las empresas guardadas en la DB (usar MCP `buscar_empresas_cliente` para verificar)
2. Si las empresas no tienen `cliente_id`, asignarlas con MCP `asignar_empresas_a_cliente`
3. Proceder a scraping con el skill site-scraper para obtener datos completos (contacto, servicios, etc.)
4. Actualizar los registros en la DB con la información obtenida del scraping

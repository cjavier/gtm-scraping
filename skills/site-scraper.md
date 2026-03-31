# Skill: Scraping de Sitios Individuales

## Cuándo usar este skill
Cuando se tiene una URL específica y se quiere extraer información de la empresa.

## Herramienta primaria: Crawl4AI
Ejecutar:
python scripts/crawl4ai_scraper.py "[URL]" --extract-contacts

Si devuelve éxito, procesar los datos extraídos e insertar en DB.

## Fallback 1: Pilot (navegador real)
Si Crawl4AI falla (timeout, bloqueo, error de parsing):
python scripts/pilot_scraper.py "[URL]" --extract-contacts --pages /contacto /nosotros

Pilot usa Playwright en modo headed (navegador visible) con stealth patches
para evitar bloqueos anti-bot. Soporta scrapear múltiples páginas en una sesión.

Opciones útiles:
- `--pages /contacto /nosotros /equipo` — scrapear rutas adicionales
- `--full` — extraer contactos + mostrar markdown
- `--headless` — modo invisible (menos robusto pero más rápido)
- `--save` — guardar en DB automáticamente

## Fallback 2: Firecrawl
Si Pilot también falla:
- Usar la tool firecrawl_scrape del MCP server
- Pasar la URL y solicitar formato markdown
- Extraer datos manualmente del markdown devuelto

## Fallback final: Chrome manual
Si todos fallan:
- Sugerir al usuario abrir la URL manualmente
- "No pude scrapear [URL] automáticamente. ¿Puedes abrirlo en Chrome para revisarlo?"

## Flujo completo de scraping (3 pasos)

### Paso 1: Scrapear el HOME
- Scrapear la URL principal con include_links=true
- Extraer datos de contacto de la empresa (teléfono, email, dirección, servicios)
- **Analizar el menú de navegación** para identificar páginas relevantes

### Paso 2: Scrapear páginas internas relevantes
Del menú extraído en Paso 1, buscar e identificar links a páginas como:
- Nosotros / Quiénes somos / About / Acerca de
- Equipo / Nuestro equipo / Team / Staff / Especialistas / Profesionales
- Contacto / Contact

**No adivinar URLs** — usar solo los links que aparecen en el menú real del sitio.
Scrapear las páginas que más probablemente contengan nombres de personas.

### Paso 3: Buscar al tomador de decisión en SERP
Si se encontró un nombre de persona en los pasos anteriores, buscar en SERP:
- Query 1: `"[Nombre Persona]" "[Nombre Empresa]"` — para encontrar LinkedIn, notas de prensa, etc.
- Query 2: `"[Nombre Persona]" neuropsicología [ciudad]` — si el query 1 no da resultados útiles

Del SERP:
- Extraer la URL de LinkedIn si aparece (guardar en contacto_linkedin)
- Si aparece un email o teléfono directo en el snippet, guardarlo
- Si un resultado parece tener datos valiosos (entrevista, nota de prensa, perfil), scrapearlo

Si NO se encontró nombre en los pasos 1-2:
- Query: `"[Nombre Empresa]" fundador OR director OR dueño OR CEO [ciudad]`
- Buscar en los resultados un nombre de persona

## Datos a extraer

### De la empresa:
- nombre_empresa (obligatorio)
- sitio_web (la URL que se scrapeó)
- telefono
- email
- direccion
- ciudad
- estado
- servicios (lista)
- descripcion (resumen corto)
- redes_sociales (links a FB, LinkedIn, IG, Twitter)

### De las personas (SIEMPRE buscar):
- contacto_nombre: Nombre completo del fundador / director / dueño
- contacto_cargo: Cargo o rol
- contacto_email: Email personal (si es diferente al de la empresa)
- contacto_telefono: Teléfono directo (si aparece)
- contacto_linkedin: URL del perfil de LinkedIn

Buscar en el contenido scrapeado:
- Títulos como "Dr.", "Dra.", "Lic.", "Mtro.", "Mtra.", "Psic.", "Msc."
- Secciones de "Nuestro equipo", "Fundador", "Director", biografías
- Firmas al pie de página
- Cédulas profesionales

## Cliente obligatorio
**ANTES de scrapear, confirmar el cliente:**
- Usar MCP `listar_clientes` para verificar el cliente activo
- Si la empresa ya existe en la DB, verificar que tenga `cliente_id`
- Al insertar/actualizar, siempre incluir `cliente_id`

## Post-scraping
1. Insertar/actualizar datos en DB con el `cliente_id` correcto
2. Loggear resultado: python scripts/db_utils.py --log-scrape "[URL]" [herramienta] [exito]
3. Si hay datos incompletos, marcar en notas qué falta
4. Si se encontraron personas, guardar en campos contacto_*
5. Verificar con MCP `stats_cliente` que el conteo del cliente se actualizo

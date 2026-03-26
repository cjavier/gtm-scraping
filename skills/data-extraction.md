# Skill: Extracción Estructurada de Datos

## Cuándo usar este skill
Cuando tienes markdown crudo de un sitio y necesitas convertirlo en datos estructurados.

## Proceso
1. Recibir markdown (de Crawl4AI o Firecrawl)
2. Analizar el contenido para identificar:
   - Nombre de la empresa (generalmente en el título o header)
   - Datos de contacto (buscar patrones de teléfono, email)
   - Dirección (buscar patrones de calle, colonia, CP, ciudad)
   - Servicios ofrecidos (buscar listas, secciones de servicios)
   - Descripción (primer párrafo significativo o meta description)
3. Estructurar en JSON
4. Validar datos (formato de teléfono, email válido, etc.)

## Patrones de teléfono México
- 10 dígitos: NNNN-NNN-NNNN o (NNN) NNN-NNNN
- Con lada: +52 NNN NNN NNNN
- Celular: empiezan con zona + 8 dígitos
- Limpiar: quitar espacios, paréntesis, guiones para almacenar consistente

## Patrones de email
- Regex básico para validación
- Ignorar emails genéricos como info@, noreply@, admin@ (pero guardarlos — a veces es el único contacto)

## Validación de datos
Antes de insertar, verificar:
- nombre_empresa no está vacío
- sitio_web es una URL válida
- teléfono tiene formato razonable (8-15 dígitos)
- email tiene @ y dominio
- ciudad es un nombre de ciudad real de México
- **cliente_id está presente** — siempre asociar al cliente correcto

## Inserción en DB
Al estructurar los datos e insertarlos:
- Incluir siempre `cliente_id` en el dict de datos
- Si no sabes el cliente, usar MCP `listar_clientes` para identificarlo
- Verificar duplicados con `url_exists()` antes de insertar

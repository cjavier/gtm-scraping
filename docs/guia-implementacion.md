# Guia de Implementacion — GTM Scraping

## Tu asistente de prospeccion con inteligencia artificial

---

# Que es esta herramienta?

Imagina que contratas a un asistente que busca empresas en Google por ti, entra a cada sitio web, copia los telefonos, emails, direcciones y nombres de los directores, y te lo organiza todo en una tabla lista para que tu equipo de ventas empiece a llamar.

**Eso es exactamente lo que hace esta herramienta**, pero en vez de un asistente humano, lo hace una inteligencia artificial (Claude) que trabaja en tu computadora.

**Lo que hace:**
- Busca empresas en Google segun lo que tu le pidas ("clinicas dentales en Merida", "constructoras en Monterrey")
- Entra a cada sitio web y extrae datos de contacto automaticamente
- Organiza todo en una base de datos por cliente o proyecto
- Te muestra los resultados en una interfaz web donde puedes filtrar, revisar y exportar a CSV/Excel

**Lo que NO hace:**
- No envia emails ni mensajes automaticamente
- No comparte tus datos con nadie — todo vive en tu computadora
- No requiere conocimientos de programacion — le hablas en espanol y el hace el trabajo

---

# Antes de empezar

Vas a necesitar crear cuentas en 3 servicios. Todos son gratuitos:

| Servicio | Para que sirve | Costo |
|---|---|---|
| **Claude Code** (Anthropic) | La inteligencia artificial que opera todo | Plan Pro $20/mes o API con credito |
| **Serper.dev** | Buscar empresas en Google | 2,500 busquedas gratis |
| **Firecrawl** | Leer sitios web (respaldo) | 500 paginas gratis |

Tambien necesitas una computadora **Mac** o **Linux** (Windows funciona con WSL).

---

# Instalacion paso a paso

## Paso 1 — Abre la Terminal

La Terminal es una aplicacion que ya viene en tu computadora. Es donde vas a escribir comandos y hablar con Claude.

**En Mac:**
1. Presiona las teclas `Cmd + Espacio` (se abre Spotlight)
2. Escribe **Terminal**
3. Presiona Enter

Se abrira una ventana negra o blanca con un cursor parpadeante. Eso es la Terminal.

> No te preocupes si nunca la has usado. Solo vas a copiar y pegar los comandos que te damos aqui.

---

## Paso 2 — Instala Claude Code

Claude Code es el programa de inteligencia artificial que va a operar toda la herramienta. Copia y pega este comando en la Terminal y presiona Enter:

```
npm install -g @anthropic-ai/claude-code
```

**Si te sale un error** que dice que `npm` no se encontro, necesitas instalar Node.js primero. Copia y pega esto:

```
curl -fsSL https://fnm.vercel.app/install | bash
```

Cierra la Terminal y vuelve a abrirla. Luego escribe:

```
fnm install 22
```

Ahora si, vuelve a intentar el comando de instalacion de Claude Code:

```
npm install -g @anthropic-ai/claude-code
```

---

## Paso 3 — Inicia sesion en Claude

Escribe en la Terminal:

```
claude
```

La primera vez te pedira que inicies sesion con tu cuenta de Anthropic. Sigue las instrucciones en pantalla — te abrira una pagina web donde creas tu cuenta o inicias sesion.

**Opciones de cuenta:**
- **Claude Pro ($20/mes):** Incluye uso de Claude Code. Es la opcion mas sencilla.
- **API con credito:** Pagas por uso. Mas economico si usas poco.

Una vez que inicies sesion, Claude te saludara en la Terminal. Escribe `exit` para salir por ahora.

---

## Paso 4 — Descarga la herramienta

Ahora vamos a descargar el codigo del proyecto. Copia y pega este comando:

```
git clone https://github.com/cjavier/gtm-scraping.git
```

Esto crea una carpeta llamada `gtm-scraping` en tu computadora. Entra a ella:

```
cd gtm-scraping
```

**Si te sale un error** que dice que `git` no se encontro:
- En Mac, te pedira instalar las "Command Line Tools". Acepta y espera a que termine. Luego repite el comando.

---

## Paso 5 — Deja que Claude instale todo lo demas

Aqui es donde la magia empieza. En vez de instalar dependencias manualmente, le vas a pedir a Claude que lo haga por ti.

Asegurate de estar dentro de la carpeta del proyecto (el paso anterior) y escribe:

```
claude
```

Claude se abrira y leera automaticamente las instrucciones del proyecto. Ahora dile:

```
Instala todas las dependencias del proyecto. Crea el entorno virtual de Python, 
instala los requirements, instala las dependencias de Node, y instala Playwright.
```

Claude ejecutara los comandos necesarios. Te ira pidiendo permiso para ejecutar cada uno — **di que si (y)** a cada uno. Veras algo como:

```
> python3 -m venv venv           ✓
> source venv/bin/activate       ✓
> pip install -r requirements.txt ✓
> playwright install chromium     ✓
> npm install                     ✓
```

Cuando termine, Claude te confirmara que todo esta instalado.

---

## Paso 6 — Crea tu cuenta en Serper.dev

Serper es el servicio que permite buscar empresas en Google de forma automatizada.

1. Abre tu navegador y ve a **https://serper.dev**
2. Haz clic en **"Sign Up"** (Registrarse)
3. Crea tu cuenta con email o con Google
4. Una vez dentro, ve a **"API Key"** en el menu
5. **Copia tu API Key** — es un texto largo que empieza con letras y numeros

> Serper te da **2,500 busquedas gratis**. Cada busqueda ("clinicas dentales Merida") gasta 1 credito y normalmente regresa 10 resultados. Es decir, con la cuenta gratis puedes encontrar hasta **25,000 empresas**.

---

## Paso 7 — Crea tu cuenta en Firecrawl

Firecrawl es el servicio de respaldo para leer sitios web cuando la herramienta principal no puede.

1. Abre tu navegador y ve a **https://firecrawl.dev**
2. Haz clic en **"Sign Up"**
3. Crea tu cuenta
4. En el dashboard, busca tu **API Key**
5. **Copia tu API Key**

> Firecrawl te da **500 creditos gratis**. La herramienta principal (Crawl4AI) es gratuita e ilimitada, asi que Firecrawl solo se usa cuando algun sitio web bloquea la primera opcion. En la practica, tus 500 creditos duran mucho.

---

## Paso 8 — Configura tus API Keys

Vuelve a la Terminal donde tienes Claude abierto (o abrelo de nuevo con `cd gtm-scraping && claude`). Dile:

```
Configura el archivo .env con mis API keys. Mi key de Serper es: XXXXXXX 
y mi key de Firecrawl es: YYYYYYY
```

(Reemplaza XXXXXXX y YYYYYYY con las keys reales que copiaste.)

Claude creara el archivo de configuracion con tus keys.

Tambien dile:

```
Configura el archivo .mcp.json para que las herramientas MCP funcionen correctamente.
```

Claude detectara automaticamente la ruta de tu proyecto y configurara todo.

---

## Paso 9 — Verifica que todo funciona

Dile a Claude:

```
Verifica que todo esta instalado correctamente. Prueba las herramientas 
y dime si hay algun problema.
```

Claude revisara:
- Que Python y las librerias esten instaladas
- Que las API keys funcionen
- Que la base de datos se pueda crear
- Que las herramientas MCP respondan

Si algo falla, Claude te dira exactamente que hacer para arreglarlo.

---

## Paso 10 — Listo! Tu primera busqueda

Ahora si, ya puedes empezar a buscar empresas. Dile a Claude algo como:

```
Crea un cliente llamado "Mi Empresa" con industria "tecnologia". 
Despues busca 20 empresas de desarrollo de software en Guadalajara.
```

Claude va a:
1. Crear el cliente en la base de datos
2. Buscar en Google "empresas desarrollo software Guadalajara"
3. Guardar los resultados
4. Decirte cuantas encontro

---

# Como usar la herramienta dia a dia

## Abrir la herramienta

Cada vez que quieras usar la herramienta:

1. Abre la Terminal
2. Escribe estos dos comandos:

```
cd gtm-scraping
claude
```

Ya estas listo para hablarle a Claude.

---

## Que cosas puedes pedirle?

### Gestionar clientes (proyectos)

Cada "cliente" es un proyecto separado. Si tu negocio es una agencia, cada cliente de tu agencia es un cliente aqui. Si vendes directamente, puedes tener un solo cliente que represente tu pipeline.

| Lo que le dices a Claude | Lo que hace |
|---|---|
| "Crea un cliente llamado Acme, industria construccion" | Crea un nuevo proyecto |
| "Muestrame todos los clientes" | Lista tus proyectos con cuantas empresas tiene cada uno |
| "Dame las estadisticas de Acme" | Te dice cuantas empresas, cuantas con email, telefono, etc. |
| "Cambia el nombre del cliente Acme a Acme Corp" | Edita el cliente |
| "Elimina el cliente Prueba" | Borra el cliente (solo si no tiene empresas) |

### Buscar empresas

| Lo que le dices a Claude | Lo que hace |
|---|---|
| "Busca clinicas dentales en Merida para Acme" | Busca en Google y guarda los resultados |
| "Busca 50 restaurantes italianos en CDMX para Acme" | Busca mas resultados (usa mas creditos de Serper) |
| "Busca empresas de logistica en todo Nuevo Leon para Acme" | Busqueda amplia por estado |
| "Busca competidores de [empresa.com] para Acme" | Busca empresas similares |

### Enriquecer datos (scraping)

Despues de buscar, muchas empresas tendran solo el nombre y el sitio web. El scraping entra a cada sitio web y extrae todos los datos de contacto.

| Lo que le dices a Claude | Lo que hace |
|---|---|
| "Scrapea todas las empresas de Acme que no tienen telefono" | Entra a cada sitio web y extrae datos |
| "Scrapea constructora-ejemplo.com para Acme" | Scrapea un sitio especifico |
| "Enriquece las empresas de Acme que les falta email" | Busca emails en los sitios web |

### Consultar y analizar datos

| Lo que le dices a Claude | Lo que hace |
|---|---|
| "Cuantas empresas tiene Acme?" | Te da el conteo |
| "Cuantas empresas tienen email y telefono?" | Estadisticas de completitud |
| "Muestrame las empresas de Acme en Monterrey" | Filtra por ciudad |
| "Que empresas de Acme no tienen datos de contacto?" | Identifica datos faltantes |

### Exportar datos

| Lo que le dices a Claude | Lo que hace |
|---|---|
| "Exporta las empresas de Acme a CSV" | Genera un archivo CSV (para Excel) |
| "Exporta solo las empresas de Acme que estan en CDMX" | Exporta filtrado |

---

## El Viewer — La interfaz visual

Ademas de hablarle a Claude por texto, tienes una interfaz web donde puedes ver, filtrar y exportar tus datos visualmente.

### Como abrirlo

Dile a Claude:

```
Inicia el viewer web
```

O escribe directamente en la Terminal (sin Claude):

```
cd gtm-scraping
source venv/bin/activate
python scripts/api_server.py --port 8080
```

Luego abre tu navegador y ve a: **http://localhost:8080**

### Que puedes hacer en el viewer

**Pantalla principal:**
- Ves todos tus clientes como tarjetas de colores
- Cada tarjeta muestra cuantas empresas tiene
- Puedes crear, editar y eliminar clientes desde aqui

**Tabla de empresas (haz clic en un cliente):**
- Ves todas las empresas de ese cliente en una tabla
- **Filtrar**: usa los dropdowns de ciudad, estado, industria y status
- **Buscar**: escribe en la barra de busqueda para encontrar cualquier empresa
- **Ordenar**: haz clic en el titulo de cualquier columna para ordenar
- **Editar**: haz doble clic en cualquier celda para corregir o agregar datos
- **Exportar**: haz clic en el boton de exportar CSV para descargar la tabla

**Empresas sin asignar:**
- Si hay empresas que no pertenecen a ningun cliente, aparecen en una seccion especial
- Puedes seleccionar varias y asignarlas a un cliente de un solo clic

---

# Datos que obtiene la herramienta

De cada empresa, la herramienta intenta encontrar:

| Dato | Ejemplo |
|---|---|
| Nombre de la empresa | "Constructora del Norte SA de CV" |
| Sitio web | www.constructoradelnorte.com |
| Telefono | 81 1234 5678 |
| Email | contacto@constructoradelnorte.com |
| Direccion | Av. Constitucion 123, Col. Centro |
| Ciudad | Monterrey |
| Estado | Nuevo Leon |
| Industria | Construccion |
| Servicios | "Construccion residencial, remodelaciones" |
| Redes sociales | Links a Facebook, LinkedIn, Instagram |
| Nombre del director/fundador | "Ing. Roberto Martinez" |
| Cargo | Director General |
| Email directo | roberto@constructoradelnorte.com |
| LinkedIn del contacto | linkedin.com/in/robertomartinez |

No siempre se encuentran todos los datos — depende de que informacion tenga publicada cada empresa en su sitio web.

---

# Ejemplo completo: De cero a lista de prospectos

Supongamos que tienes una agencia de marketing y quieres prospectar clinicas dentales en Merida.

**Paso 1 — Abres Claude:**
```
cd gtm-scraping
claude
```

**Paso 2 — Creas el cliente:**
```
Tu: Crea un cliente llamado "Agencia XYZ - Clinicas Dentales" 
    con industria "salud dental"
```

**Paso 3 — Buscas empresas:**
```
Tu: Busca clinicas dentales en Merida, Yucatan. Quiero al menos 30 resultados.
```
Claude buscara en Google y te reportara algo como:
> "Encontre 34 clinicas dentales. 28 tienen sitio web."

**Paso 4 — Enriqueces los datos:**
```
Tu: Scrapea todas las clinicas que tienen sitio web para obtener 
    telefono, email y datos del dentista principal.
```
Claude entrara a cada sitio web (esto toma unos minutos) y te reportara:
> "Scrapee 28 sitios. 22 con telefono, 18 con email, 15 con nombre del doctor."

**Paso 5 — Revisas en el viewer:**
```
Tu: Inicia el viewer web
```
Abres http://localhost:8080 en tu navegador, haces clic en la tarjeta "Agencia XYZ - Clinicas Dentales", y ves toda la tabla con los datos.

**Paso 6 — Exportas:**
En el viewer, haz clic en **"Exportar CSV"**. Se descarga un archivo que puedes abrir en Excel o subir a tu CRM.

---

# Costos estimados

| Recurso | Costo | Que incluye |
|---|---|---|
| Claude Pro | $20 USD/mes | Uso ilimitado en horario normal |
| Serper.dev (gratis) | $0 | 2,500 busquedas (~25,000 empresas) |
| Firecrawl (gratis) | $0 | 500 paginas de respaldo |
| Crawl4AI | $0 | Ilimitado (corre en tu computadora) |
| **Total** | **$20 USD/mes** | |

Si se te acaban los creditos gratuitos:
- Serper: $50/mes por 50,000 busquedas
- Firecrawl: $16/mes por 3,000 paginas

Para la mayoria de negocios, los tiers gratuitos de Serper y Firecrawl son mas que suficientes.

---

# Soluciones a problemas comunes

### "Claude no reconoce las herramientas del proyecto"
Asegurate de estar dentro de la carpeta `gtm-scraping` cuando abres Claude. Las herramientas se cargan automaticamente solo si estas en el directorio correcto.

```
cd gtm-scraping
claude
```

### "Me dice que no encuentra Python o pip"
Dile a Claude: "Instala Python 3 en mi computadora" y el te guiara.

### "El viewer no abre en mi navegador"
Verifica que el servidor este corriendo. Si cerraste la Terminal donde lo iniciaste, necesitas volver a ejecutar:
```
cd gtm-scraping
source venv/bin/activate
python scripts/api_server.py --port 8080
```

### "Serper me dice que se acabaron mis creditos"
Puedes ver cuantos creditos te quedan en https://serper.dev/dashboard. Si se acabaron, puedes:
1. Crear otra cuenta con otro email
2. Pagar el plan de $50/mes
3. Pedirle a Claude que use Firecrawl para buscar (es mas lento pero funciona)

### "Un sitio web no se pudo scrapear"
Algunos sitios bloquean los scrapers. La herramienta intenta 3 metodos diferentes automaticamente. Si ninguno funciona, Claude te dira y puedes abrir ese sitio manualmente en tu navegador para copiar los datos.

### "Quiero borrar todas las empresas y empezar de cero"
Dile a Claude: "Quiero limpiar la base de datos. Hazme un backup primero y luego borra todas las empresas del cliente X."

---

# Glosario

| Termino | Que significa |
|---|---|
| **Terminal** | La aplicacion donde escribes comandos en tu computadora |
| **Claude Code** | El programa de inteligencia artificial que opera la herramienta |
| **Scraping** | El proceso de entrar a un sitio web y extraer datos automaticamente |
| **SERP** | Los resultados de una busqueda en Google |
| **API Key** | Una "contraseña" que te dan los servicios para usar sus herramientas |
| **MCP** | El protocolo que permite a Claude usar herramientas externas |
| **CSV** | Un formato de archivo que se abre en Excel/Google Sheets |
| **Viewer** | La interfaz visual web donde ves y filtras tus datos |
| **Cliente** | Un proyecto o cuenta dentro de la herramienta (no confundir con "cliente" de tu negocio — aqui es mas como una "carpeta") |
| **Base de datos** | Donde se guardan todas las empresas. Es un archivo en tu computadora |
| **Localhost** | Tu propia computadora funcionando como servidor web (solo tu la ves) |

---

# Resumen rapido

```
CADA VEZ QUE QUIERAS USAR LA HERRAMIENTA:

   1. Abre la Terminal
   2. Escribe: cd gtm-scraping
   3. Escribe: claude
   4. Habla en espanol: "Busca ferreterias en Queretaro para mi cliente X"
   5. Claude hace el trabajo
   6. Revisa los resultados en http://localhost:8080

ESO ES TODO.
```

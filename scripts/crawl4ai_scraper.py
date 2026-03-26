#!/usr/bin/env python3
"""
crawl4ai_scraper.py — Wrapper de Crawl4AI para scraping de sitios web.

Si el scraping falla (timeout, error), sale con código 1 para que
Claude Code sepa que debe hacer fallback a Firecrawl.

Uso:
    python scripts/crawl4ai_scraper.py "https://example.com" --extract-contacts --save
    python scripts/crawl4ai_scraper.py "https://example.com" --full
    python scripts/crawl4ai_scraper.py "https://example.com" --markdown
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SCRIPT_DIR)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


# ---------------------------------------------------------------------------
# Regex patterns para México
# ---------------------------------------------------------------------------

# Teléfono: soporta +52, lada con paréntesis, formatos con espacios/guiones/puntos
PHONE_PATTERN = re.compile(
    r"(?<!\d)"                            # no precedido de dígito
    r"(?:\+?52[\s\-.]?)?"                 # código de país +52 opcional
    r"(?:\(?\d{2,3}\)?[\s\-.]?)?"        # lada 2-3 dígitos opcional
    r"\d{3,4}[\s\-.]?\d{3,4}"            # número local
    r"(?!\d)"                             # no seguido de dígito
)

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Redes sociales — captura la URL completa
SOCIAL_PATTERNS = {
    "facebook": re.compile(
        r"https?://(?:www\.)?facebook\.com/[^\s\"'<>\)]{3,100}", re.IGNORECASE
    ),
    "linkedin": re.compile(
        r"https?://(?:www\.)?linkedin\.com/(?:company|in|pub)/[^\s\"'<>\)]{2,100}",
        re.IGNORECASE,
    ),
    "instagram": re.compile(
        r"https?://(?:www\.)?instagram\.com/[^\s\"'<>\)]{2,100}", re.IGNORECASE
    ),
    "twitter": re.compile(
        r"https?://(?:www\.)?(?:twitter|x)\.com/[^\s\"'<>\)]{2,100}", re.IGNORECASE
    ),
}

# Dirección: patrones comunes en México
ADDRESS_PATTERN = re.compile(
    r"(?:"
    r"(?:Av(?:enida)?|Blvd?|Blvd|Calle|C\.|Col(?:onia)?|Fracc(?:ionamiento)?|"
    r"Paseo|Privada|Priv\.|Calz(?:ada)?)"
    r"\.?\s+\w[\w\s,\.#°]+?"
    r"(?:C\.?P\.?\s*\d{5}|,\s*\w[\w\s]+)"
    r")",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Extracción de contactos desde markdown
# ---------------------------------------------------------------------------

def clean_phone(phone: str) -> str:
    """Elimina caracteres no numéricos excepto + inicial."""
    cleaned = re.sub(r"[^\d+]", "", phone)
    # Quitar +52 para normalizar a 10 dígitos locales
    return cleaned


def is_valid_phone(phone: str) -> bool:
    """Valida que el número tenga entre 8 y 15 dígitos."""
    digits = re.sub(r"\D", "", phone)
    return 8 <= len(digits) <= 15


def extract_contacts_from_markdown(markdown: str, page_title: str = "") -> dict:
    """
    Extrae datos de contacto estructurados desde markdown.
    Retorna un dict con los campos del schema de empresas.
    """
    contacts = {
        "nombre_empresa": "",
        "telefono": [],
        "email": [],
        "direccion": "",
        "redes_sociales": {
            "facebook": "",
            "linkedin": "",
            "instagram": "",
            "twitter": "",
        },
    }

    # Nombre de empresa: usar el título de página como mejor aproximación
    if page_title:
        # Limpiar sufijos comunes: "Empresa | Inicio", "Empresa - Home", etc.
        name = re.split(r"\s*[\|\-–—]\s*", page_title)[0].strip()
        contacts["nombre_empresa"] = name

    # Teléfonos
    raw_phones = PHONE_PATTERN.findall(markdown)
    seen_phones = set()
    for phone in raw_phones:
        phone_stripped = phone.strip()
        if not phone_stripped:
            continue
        if is_valid_phone(phone_stripped):
            normalized = clean_phone(phone_stripped)
            if normalized not in seen_phones and len(normalized) >= 8:
                seen_phones.add(normalized)
                contacts["telefono"].append(phone_stripped)

    # Emails
    raw_emails = EMAIL_PATTERN.findall(markdown)
    seen_emails = set()
    for email in raw_emails:
        email_lower = email.lower()
        if email_lower not in seen_emails:
            seen_emails.add(email_lower)
            contacts["email"].append(email)

    # Redes sociales
    for network, pattern in SOCIAL_PATTERNS.items():
        matches = pattern.findall(markdown)
        if matches:
            # Limpiar URLs: quitar parámetros al final, trailing slashes duplicados
            url = matches[0].rstrip("/").split("?")[0]
            # Filtrar páginas genéricas de Facebook (sharer, etc.)
            if network == "facebook" and any(
                x in url for x in ["sharer", "share", "plugins", "dialog"]
            ):
                if len(matches) > 1:
                    url = matches[1].rstrip("/").split("?")[0]
                else:
                    url = ""
            contacts["redes_sociales"][network] = url

    # Dirección (primer match)
    addr_matches = ADDRESS_PATTERN.findall(markdown)
    if addr_matches:
        contacts["direccion"] = addr_matches[0].strip()

    return contacts


# ---------------------------------------------------------------------------
# Crawler principal (async)
# ---------------------------------------------------------------------------

async def run_crawler(url: str, timeout: int, extract: bool, full: bool) -> dict:
    """
    Ejecuta el crawler y retorna un dict con:
      - success: bool
      - markdown: str (si aplica)
      - contacts: dict (si applica extract/full)
      - title: str
      - error: str (si fallo)
      - elapsed: float
    """
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    except ImportError:
        return {
            "success": False,
            "error": "crawl4ai no está instalado. Ejecuta: pip install crawl4ai",
            "markdown": "",
            "contacts": {},
            "title": "",
            "elapsed": 0.0,
        }

    start = time.time()

    browser_cfg = BrowserConfig(
        headless=True,
        verbose=False,
    )

    run_cfg = CrawlerRunConfig(
        page_timeout=timeout * 1000,  # crawl4ai usa milisegundos
        wait_until="domcontentloaded",
        word_count_threshold=10,
        exclude_external_links=False,
        process_iframes=False,
    )

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)

        elapsed = time.time() - start

        if not result.success:
            error_msg = getattr(result, "error_message", "Crawl failed without details")
            return {
                "success": False,
                "error": error_msg,
                "markdown": "",
                "contacts": {},
                "title": "",
                "elapsed": elapsed,
            }

        markdown = result.markdown or ""
        title = ""

        # Intentar extraer título del HTML o del markdown
        if hasattr(result, "metadata") and result.metadata:
            title = result.metadata.get("title", "") or ""
        if not title and hasattr(result, "html") and result.html:
            title_match = re.search(
                r"<title[^>]*>([^<]+)</title>", result.html, re.IGNORECASE
            )
            if title_match:
                title = title_match.group(1).strip()

        output = {
            "success": True,
            "markdown": markdown,
            "title": title,
            "url": url,
            "elapsed": elapsed,
            "contacts": {},
        }

        if extract or full:
            output["contacts"] = extract_contacts_from_markdown(markdown, title)

        return output

    except asyncio.TimeoutError:
        elapsed = time.time() - start
        return {
            "success": False,
            "error": f"Timeout después de {timeout}s",
            "markdown": "",
            "contacts": {},
            "title": "",
            "elapsed": elapsed,
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "success": False,
            "error": str(e),
            "markdown": "",
            "contacts": {},
            "title": "",
            "elapsed": elapsed,
        }


# ---------------------------------------------------------------------------
# Salida legible para Claude Code
# ---------------------------------------------------------------------------

def print_readable(result: dict, url: str, args: argparse.Namespace) -> None:
    """Imprime resultado en formato legible."""
    print("=" * 70)
    print(f"SCRAPING: {url}")
    print(f"Título:   {result.get('title', 'N/A')}")
    print(f"Tiempo:   {result['elapsed']:.2f}s")
    print(f"Estado:   {'EXITO' if result['success'] else 'FALLO'}")
    print("=" * 70)

    if not result["success"]:
        print(f"\nERROR: {result['error']}")
        print("\n[FALLBACK] Usar Firecrawl MCP como alternativa.")
        return

    contacts = result.get("contacts", {})
    markdown = result.get("markdown", "")

    # Mostrar contactos extraídos
    if contacts:
        print("\n--- DATOS EXTRAÍDOS ---\n")
        if contacts.get("nombre_empresa"):
            print(f"Empresa:    {contacts['nombre_empresa']}")
        if contacts.get("telefono"):
            print(f"Teléfonos:  {', '.join(contacts['telefono'])}")
        if contacts.get("email"):
            print(f"Emails:     {', '.join(contacts['email'])}")
        if contacts.get("direccion"):
            print(f"Dirección:  {contacts['direccion']}")

        redes = contacts.get("redes_sociales", {})
        redes_encontradas = {k: v for k, v in redes.items() if v}
        if redes_encontradas:
            print("\nRedes sociales:")
            for red, link in redes_encontradas.items():
                print(f"  {red.capitalize():12s}: {link}")

    # Mostrar markdown (primeros 3000 chars si es modo full o markdown)
    if (args.markdown or args.full) and markdown:
        print("\n--- MARKDOWN (primeros 3000 caracteres) ---\n")
        preview = markdown[:3000]
        if len(markdown) > 3000:
            preview += f"\n\n... [{len(markdown) - 3000} caracteres más] ..."
        print(preview)

    print("\n" + "=" * 70)
    words = len(markdown.split()) if markdown else 0
    print(f"Longitud markdown: {len(markdown)} chars | ~{words} palabras")
    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scraping de sitios web con Crawl4AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/crawl4ai_scraper.py "https://empresa.com" --extract-contacts
  python scripts/crawl4ai_scraper.py "https://empresa.com/contacto" --full --save
  python scripts/crawl4ai_scraper.py "https://empresa.com" --markdown

Códigos de salida:
  0 = Éxito
  1 = Fallo (timeout, error) — Claude Code debe usar Firecrawl como fallback
        """,
    )
    parser.add_argument(
        "url",
        help="URL del sitio a scrapear",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Retornar markdown limpio (modo default si no se especifica otro)",
    )
    parser.add_argument(
        "--extract-contacts",
        action="store_true",
        dest="extract_contacts",
        help="Extraer datos estructurados de contacto (teléfono, email, redes sociales)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Retornar markdown Y extraer contactos",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        metavar="N",
        help="Timeout en segundos (default: 30)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Guardar resultado en la base de datos",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Imprimir resultado como JSON",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Validar URL básica
    parsed = urlparse(args.url)
    if not parsed.scheme or not parsed.netloc:
        print(f"ERROR: URL inválida: {args.url}", file=sys.stderr)
        sys.exit(1)

    # Si no se especificó ningún modo, activar markdown por default
    if not args.extract_contacts and not args.full:
        args.markdown = True

    extract = args.extract_contacts or args.full

    # Ejecutar crawler
    result = asyncio.run(
        run_crawler(
            url=args.url,
            timeout=args.timeout,
            extract=extract,
            full=args.full,
        )
    )

    # Salida
    if args.output_json:
        # En modo JSON, no incluir el markdown completo a menos que se pida
        output = {
            "success": result["success"],
            "url": args.url,
            "title": result.get("title", ""),
            "elapsed": result.get("elapsed", 0),
        }
        if not result["success"]:
            output["error"] = result.get("error", "Unknown error")
        if extract:
            output["contacts"] = result.get("contacts", {})
        if args.markdown or args.full:
            output["markdown"] = result.get("markdown", "")
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_readable(result, args.url, args)

    # Guardar en DB si se solicitó
    if args.save:
        try:
            import db_utils

            contacts = result.get("contacts", {})
            has_data = bool(
                contacts.get("telefono")
                or contacts.get("email")
                or contacts.get("nombre_empresa")
            )

            log_id = db_utils.log_scraping(
                url=args.url,
                herramienta="crawl4ai",
                exito=result["success"],
                tiempo=result.get("elapsed", 0),
                error=result.get("error") if not result["success"] else None,
            )

            if not args.output_json:
                print(f"\n[DB] Scraping logueado con ID: {log_id}")

            # Insertar empresa si se extrajeron datos útiles
            if result["success"] and extract and has_data:
                redes = contacts.get("redes_sociales", {})
                empresa_data = {
                    "nombre": contacts.get("nombre_empresa", ""),
                    "sitio_web": args.url,
                    "telefono": ", ".join(contacts.get("telefono", [])),
                    "email": ", ".join(contacts.get("email", [])),
                    "direccion": contacts.get("direccion", ""),
                    "redes_sociales": json.dumps(
                        {k: v for k, v in redes.items() if v},
                        ensure_ascii=False,
                    ),
                    "fuente": "scraping",
                    "url_scrapeada": args.url,
                }
                # Solo insertar si tiene nombre
                if empresa_data["nombre"]:
                    empresa_id = db_utils.insert_empresa(empresa_data)
                    if not args.output_json:
                        print(f"[DB] Empresa guardada con ID: {empresa_id}")

        except ImportError:
            print(
                "\n[WARN] No se pudo importar db_utils. "
                "Asegúrate de que scripts/db_utils.py existe.",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"\n[WARN] Error guardando en DB: {e}", file=sys.stderr)

    # Salir con código 1 si el crawl falló (señal para Claude Code de usar fallback)
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

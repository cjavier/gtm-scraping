#!/usr/bin/env python3
"""
pilot_scraper.py — Scraping con navegador real usando Playwright (modo headed).

Inspirado en Pilot (github.com/TacosyHorchata/Pilot), usa un navegador
Chromium visible que evita bloqueos anti-bot al no ser headless.

Jerarquía de fallback:
  1. crawl4ai_scraper.py (headless, rápido)
  2. pilot_scraper.py    (headed, más robusto) ← ESTE ARCHIVO
  3. Firecrawl MCP       (API externa)
  4. Chrome manual       (usuario)

Uso:
    python scripts/pilot_scraper.py "https://example.com" --extract-contacts
    python scripts/pilot_scraper.py "https://example.com" --full --save
    python scripts/pilot_scraper.py "https://example.com" --markdown
    python scripts/pilot_scraper.py "https://example.com" --pages /contacto /nosotros
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SCRIPT_DIR)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Reusar extracción de contactos de crawl4ai_scraper
from crawl4ai_scraper import extract_contacts_from_markdown


# ---------------------------------------------------------------------------
# HTML a Markdown (conversión simple)
# ---------------------------------------------------------------------------

def html_to_markdown(html: str) -> str:
    """Convierte HTML a markdown simplificado extrayendo texto visible."""
    import re as _re

    # Eliminar scripts y styles
    text = _re.sub(r"<script[^>]*>.*?</script>", "", html, flags=_re.DOTALL | _re.IGNORECASE)
    text = _re.sub(r"<style[^>]*>.*?</style>", "", text, flags=_re.DOTALL | _re.IGNORECASE)
    text = _re.sub(r"<!--.*?-->", "", text, flags=_re.DOTALL)

    # Convertir headers
    for i in range(1, 7):
        text = _re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", rf"\n{'#' * i} \1\n", text, flags=_re.DOTALL | _re.IGNORECASE)

    # Convertir links preservando URL (importante para redes sociales)
    text = _re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=_re.DOTALL | _re.IGNORECASE)

    # Convertir párrafos y line breaks
    text = _re.sub(r"<br\s*/?>", "\n", text, flags=_re.IGNORECASE)
    text = _re.sub(r"</?p[^>]*>", "\n", text, flags=_re.IGNORECASE)
    text = _re.sub(r"<li[^>]*>", "\n- ", text, flags=_re.IGNORECASE)

    # Eliminar todos los tags restantes
    text = _re.sub(r"<[^>]+>", " ", text)

    # Decodificar entidades HTML comunes
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"')

    # Limpiar espacios múltiples y líneas vacías
    text = _re.sub(r"[ \t]+", " ", text)
    text = _re.sub(r"\n\s*\n\s*\n", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Scraper con Playwright (headed mode)
# ---------------------------------------------------------------------------

async def scrape_with_pilot(
    url: str,
    timeout: int = 30,
    extract: bool = False,
    extra_pages: list[str] | None = None,
    headless: bool = False,
) -> dict:
    """
    Navega a una URL con un navegador Chromium real y extrae contenido.

    Args:
        url: URL principal a scrapear
        timeout: Timeout en segundos
        extract: Si True, extraer datos de contacto
        extra_pages: Rutas adicionales a visitar (e.g., ["/contacto", "/nosotros"])
        headless: Si True, usar modo headless (default: False para evitar bloqueos)
    """
    from playwright.async_api import async_playwright

    start = time.time()
    all_markdown = ""
    all_html = ""
    title = ""

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="es-MX",
                timezone_id="America/Mexico_City",
            )

            # Inyectar stealth patches
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
                Object.defineProperty(navigator, 'languages', { get: () => ['es-MX', 'es', 'en'] });
            """)

            page = await context.new_page()
            page.set_default_timeout(timeout * 1000)

            # Navegar a URL principal
            print(f"[Pilot] Navegando a {url} ...", file=sys.stderr)
            response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)

            if not response or response.status >= 400:
                status = response.status if response else "sin respuesta"
                elapsed = time.time() - start
                await browser.close()
                return {
                    "success": False,
                    "error": f"HTTP {status} al cargar {url}",
                    "markdown": "",
                    "contacts": {},
                    "title": "",
                    "elapsed": elapsed,
                }

            # Esperar a que cargue contenido dinámico
            await page.wait_for_load_state("networkidle", timeout=10000)
            await asyncio.sleep(1)  # breve pausa para JS tardío

            title = await page.title()
            html = await page.content()
            all_html += html
            all_markdown += html_to_markdown(html)

            # Scrapear páginas adicionales
            pages_to_visit = extra_pages or []
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

            for extra_path in pages_to_visit:
                extra_url = urljoin(base_url, extra_path)
                try:
                    print(f"[Pilot] Navegando a {extra_url} ...", file=sys.stderr)
                    resp = await page.goto(extra_url, wait_until="domcontentloaded", timeout=timeout * 1000)
                    if resp and resp.status < 400:
                        await page.wait_for_load_state("networkidle", timeout=8000)
                        await asyncio.sleep(0.5)
                        extra_html = await page.content()
                        all_html += "\n" + extra_html
                        all_markdown += "\n\n---\n\n" + html_to_markdown(extra_html)
                except Exception as e:
                    print(f"[Pilot] Error en {extra_url}: {e}", file=sys.stderr)

            await browser.close()

        elapsed = time.time() - start

        result = {
            "success": True,
            "markdown": all_markdown,
            "title": title,
            "url": url,
            "elapsed": elapsed,
            "contacts": {},
            "pages_scraped": 1 + len([p for p in pages_to_visit]),
        }

        if extract:
            # Extraer de markdown Y del HTML raw (para URLs de redes sociales)
            contacts = extract_contacts_from_markdown(all_markdown + "\n" + all_html, title)
            result["contacts"] = contacts

        return result

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
# Salida legible
# ---------------------------------------------------------------------------

def print_readable(result: dict, url: str, show_markdown: bool = False) -> None:
    """Imprime resultado en formato legible."""
    print("=" * 70)
    print(f"PILOT SCRAPING: {url}")
    print(f"Título:   {result.get('title', 'N/A')}")
    print(f"Tiempo:   {result['elapsed']:.2f}s")
    print(f"Páginas:  {result.get('pages_scraped', 1)}")
    print(f"Estado:   {'EXITO' if result['success'] else 'FALLO'}")
    print("=" * 70)

    if not result["success"]:
        print(f"\nERROR: {result['error']}")
        print("\n[FALLBACK] Usar Firecrawl MCP como alternativa.")
        return

    contacts = result.get("contacts", {})
    markdown = result.get("markdown", "")

    if contacts:
        print("\n--- DATOS EXTRAIDOS ---\n")
        if contacts.get("nombre_empresa"):
            print(f"Empresa:    {contacts['nombre_empresa']}")
        if contacts.get("telefono"):
            print(f"Telefonos:  {', '.join(contacts['telefono'])}")
        if contacts.get("email"):
            print(f"Emails:     {', '.join(contacts['email'])}")
        if contacts.get("direccion"):
            print(f"Direccion:  {contacts['direccion']}")

        redes = contacts.get("redes_sociales", {})
        redes_encontradas = {k: v for k, v in redes.items() if v}
        if redes_encontradas:
            print("\nRedes sociales:")
            for red, link in redes_encontradas.items():
                print(f"  {red.capitalize():12s}: {link}")

    if show_markdown and markdown:
        print("\n--- MARKDOWN (primeros 3000 caracteres) ---\n")
        preview = markdown[:3000]
        if len(markdown) > 3000:
            preview += f"\n\n... [{len(markdown) - 3000} caracteres mas] ..."
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
        description="Scraping con navegador real (Pilot/Playwright headed)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/pilot_scraper.py "https://empresa.com" --extract-contacts
  python scripts/pilot_scraper.py "https://empresa.com" --full --save
  python scripts/pilot_scraper.py "https://empresa.com" --pages /contacto /nosotros
  python scripts/pilot_scraper.py "https://empresa.com" --headless

Codigos de salida:
  0 = Exito
  1 = Fallo — Claude Code debe usar Firecrawl como fallback
        """,
    )
    parser.add_argument("url", help="URL del sitio a scrapear")
    parser.add_argument("--markdown", action="store_true", help="Mostrar markdown extraido")
    parser.add_argument(
        "--extract-contacts", action="store_true", dest="extract_contacts",
        help="Extraer datos de contacto",
    )
    parser.add_argument("--full", action="store_true", help="Markdown + contactos")
    parser.add_argument(
        "--pages", nargs="+", metavar="PATH", default=[],
        help="Rutas adicionales a scrapear (e.g., /contacto /nosotros)",
    )
    parser.add_argument("--timeout", type=int, default=30, help="Timeout en segundos (default: 30)")
    parser.add_argument("--headless", action="store_true", help="Usar modo headless (default: headed)")
    parser.add_argument("--save", action="store_true", help="Guardar resultado en la base de datos")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Salida JSON")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    parsed = urlparse(args.url)
    if not parsed.scheme or not parsed.netloc:
        print(f"ERROR: URL invalida: {args.url}", file=sys.stderr)
        sys.exit(1)

    if not args.extract_contacts and not args.full:
        args.markdown = True

    extract = args.extract_contacts or args.full

    result = asyncio.run(
        scrape_with_pilot(
            url=args.url,
            timeout=args.timeout,
            extract=extract,
            extra_pages=args.pages if args.pages else None,
            headless=args.headless,
        )
    )

    if args.output_json:
        output = {
            "success": result["success"],
            "url": args.url,
            "title": result.get("title", ""),
            "elapsed": result.get("elapsed", 0),
            "pages_scraped": result.get("pages_scraped", 1),
        }
        if not result["success"]:
            output["error"] = result.get("error", "Unknown error")
        if extract:
            output["contacts"] = result.get("contacts", {})
        if args.markdown or args.full:
            output["markdown"] = result.get("markdown", "")
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_readable(result, args.url, show_markdown=args.markdown or args.full)

    # Guardar en DB
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
                herramienta="pilot",
                exito=result["success"],
                tiempo=result.get("elapsed", 0),
                error=result.get("error") if not result["success"] else None,
            )

            if not args.output_json:
                print(f"\n[DB] Scraping logueado con ID: {log_id}")

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
                if empresa_data["nombre"]:
                    empresa_id = db_utils.insert_empresa(empresa_data)
                    if not args.output_json:
                        print(f"[DB] Empresa guardada con ID: {empresa_id}")

        except ImportError:
            print("\n[WARN] No se pudo importar db_utils.", file=sys.stderr)
        except Exception as e:
            print(f"\n[WARN] Error guardando en DB: {e}", file=sys.stderr)

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

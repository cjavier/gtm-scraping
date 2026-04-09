#!/usr/bin/env python3
"""Genera el PDF de la guía de implementación."""

import markdown
from weasyprint import HTML

CSS = """
@page {
    size: letter;
    margin: 2.2cm 2.5cm;
    @bottom-center {
        content: "Página " counter(page) " de " counter(pages);
        font-size: 9px;
        color: #999;
        font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    }
}

body {
    font-family: -apple-system, 'Helvetica Neue', 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a1a;
    max-width: 100%;
}

/* ── Cover title ── */
h1:first-of-type {
    font-size: 28pt;
    color: #1a1a1a;
    border-bottom: 3px solid #6366f1;
    padding-bottom: 12px;
    margin-top: 60px;
    margin-bottom: 4px;
}

/* Subtitle right after cover title */
h1:first-of-type + h2 {
    font-size: 14pt;
    color: #6366f1;
    font-weight: 400;
    border: none;
    margin-top: 0;
    padding-bottom: 0;
    margin-bottom: 40px;
}

h1 {
    font-size: 22pt;
    color: #1a1a1a;
    border-bottom: 2px solid #6366f1;
    padding-bottom: 8px;
    margin-top: 40px;
    page-break-before: auto;
}

h2 {
    font-size: 16pt;
    color: #4338ca;
    margin-top: 28px;
    padding-bottom: 4px;
    border-bottom: 1px solid #e5e7eb;
}

h3 {
    font-size: 13pt;
    color: #1a1a1a;
    margin-top: 20px;
}

/* ── Horizontal rules as section separators ── */
hr {
    border: none;
    border-top: 2px solid #6366f1;
    margin: 36px 0;
    page-break-after: avoid;
}

/* ── Paragraphs ── */
p {
    margin-bottom: 10px;
    orphans: 3;
    widows: 3;
}

strong {
    color: #1a1a1a;
}

/* ── Code blocks ── */
pre {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-left: 4px solid #6366f1;
    border-radius: 6px;
    padding: 14px 18px;
    font-size: 10pt;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    line-height: 1.5;
    overflow-x: auto;
    page-break-inside: avoid;
    margin: 12px 0;
}

code {
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10pt;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

pre code {
    background: none;
    padding: 0;
}

/* ── Tables ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

thead {
    background: #6366f1;
    color: white;
}

th {
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
}

td {
    padding: 9px 14px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
}

tr:nth-child(even) {
    background: #f8fafc;
}

/* ── Blockquotes (tips) ── */
blockquote {
    background: #eff6ff;
    border-left: 4px solid #6366f1;
    margin: 14px 0;
    padding: 12px 18px;
    border-radius: 0 6px 6px 0;
    font-size: 10.5pt;
    color: #374151;
    page-break-inside: avoid;
}

blockquote p {
    margin: 0;
}

/* ── Lists ── */
ul, ol {
    margin: 8px 0;
    padding-left: 24px;
}

li {
    margin-bottom: 4px;
}

/* ── Links ── */
a {
    color: #4338ca;
    text-decoration: none;
}

/* ── Summary box at end ── */
pre:last-of-type {
    background: #f0fdf4;
    border-color: #22c55e;
    border-left: 4px solid #22c55e;
    font-size: 11pt;
}
"""

def main():
    with open("docs/guia-implementacion.md", "r", encoding="utf-8") as f:
        md_content = f.read()

    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "smarty"],
    )

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    output_path = "docs/Guia-de-Implementacion-GTM-Scraping.pdf"
    HTML(string=full_html).write_pdf(output_path)
    print(f"PDF generado: {output_path}")

if __name__ == "__main__":
    main()

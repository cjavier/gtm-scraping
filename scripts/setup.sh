#!/bin/bash
set -e

echo "🔧 Configurando proyecto de scraping..."

# 1. Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias Python
pip install crawl4ai playwright aiohttp aiosqlite httpx python-dotenv

# 3. Instalar browsers de Playwright
playwright install chromium

# 4. Instalar dependencias Node
npm init -y
npm install firecrawl-mcp

# 5. Crear la base de datos SQLite
python3 -c "
import sqlite3
conn = sqlite3.connect('db/empresas.db')
with open('db/schema.sql', 'r') as f:
    conn.executescript(f.read())
conn.close()
print('Base de datos creada exitosamente')
"

# 6. Copiar .env.example a .env si no existe
if [ ! -f .env ]; then
    cp .env.example .env
    echo '⚠️  Edita .env con tus API keys'
fi

echo '✅ Setup completo. Ejecuta: source venv/bin/activate'

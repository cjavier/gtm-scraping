-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    industria_objetivo TEXT,
    color TEXT DEFAULT '#3b82f6',
    fecha_creacion TEXT DEFAULT (datetime('now')),
    fecha_actualizacion TEXT DEFAULT (datetime('now'))
);

-- Tabla principal de empresas
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER REFERENCES clientes(id),
    nombre TEXT NOT NULL,
    sitio_web TEXT,
    telefono TEXT,
    email TEXT,
    direccion TEXT,
    ciudad TEXT,
    estado TEXT,
    pais TEXT DEFAULT 'México',
    industria TEXT,
    sub_industria TEXT,
    descripcion TEXT,
    servicios TEXT,
    empleados_estimado TEXT,
    redes_sociales TEXT,
    fuente TEXT,
    query_origen TEXT,
    url_scrapeada TEXT,
    fecha_descubrimiento TEXT DEFAULT (datetime('now')),
    fecha_actualizacion TEXT DEFAULT (datetime('now')),
    notas TEXT,
    status TEXT DEFAULT 'nuevo',
    contacto_nombre TEXT,
    contacto_cargo TEXT,
    contacto_email TEXT,
    contacto_telefono TEXT
);

-- Tabla de búsquedas realizadas (log)
CREATE TABLE IF NOT EXISTS busquedas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    herramienta TEXT NOT NULL,
    resultados_encontrados INTEGER DEFAULT 0,
    resultados_guardados INTEGER DEFAULT 0,
    fecha TEXT DEFAULT (datetime('now')),
    notas TEXT
);

-- Tabla de scraping realizados (log)
CREATE TABLE IF NOT EXISTS scraping_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    herramienta TEXT NOT NULL,
    exito INTEGER DEFAULT 0,
    tiempo_segundos REAL,
    datos_extraidos INTEGER DEFAULT 0,
    error TEXT,
    fecha TEXT DEFAULT (datetime('now'))
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_empresas_cliente_id ON empresas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_empresas_ciudad ON empresas(ciudad);
CREATE INDEX IF NOT EXISTS idx_empresas_estado ON empresas(estado);
CREATE INDEX IF NOT EXISTS idx_empresas_industria ON empresas(industria);
CREATE INDEX IF NOT EXISTS idx_empresas_status ON empresas(status);
CREATE INDEX IF NOT EXISTS idx_empresas_nombre ON empresas(nombre);

-- Vista útil
CREATE VIEW IF NOT EXISTS v_empresas_contacto AS
SELECT
    nombre, sitio_web, telefono, email, ciudad, estado,
    industria, servicios, status, fecha_descubrimiento
FROM empresas
WHERE status != 'descartado'
ORDER BY fecha_descubrimiento DESC;

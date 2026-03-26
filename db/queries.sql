-- Buscar empresas por ciudad
SELECT * FROM empresas WHERE ciudad LIKE '%' || ? || '%';

-- Empresas sin email
SELECT nombre, sitio_web, ciudad FROM empresas WHERE email IS NULL OR email = '';

-- Resumen por ciudad
SELECT ciudad, COUNT(*) as total,
       SUM(CASE WHEN email IS NOT NULL AND email != '' THEN 1 ELSE 0 END) as con_email
FROM empresas GROUP BY ciudad ORDER BY total DESC;

-- Resumen por industria
SELECT industria, COUNT(*) as total FROM empresas GROUP BY industria ORDER BY total DESC;

-- Últimas búsquedas
SELECT * FROM busquedas ORDER BY fecha DESC LIMIT 20;

-- Efectividad de herramientas
SELECT herramienta,
       COUNT(*) as intentos,
       SUM(exito) as exitosos,
       ROUND(AVG(exito) * 100, 1) as tasa_exito_pct,
       ROUND(AVG(tiempo_segundos), 2) as tiempo_promedio_seg
FROM scraping_log GROUP BY herramienta;

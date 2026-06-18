-- ============================================================
-- SEED 03: Monitoreo de Calidad del Aire
-- PostgreSQL
--
-- Objetivo:
-- - Agregar una tercera carga de datos simulados.
-- - Mantener coherencia con la BDD y semillas anteriores.
-- - No borrar datos existentes.
-- - Aumentar volumen para EDA, dashboard, clustering y regresión.
--
-- Periodo simulado:
-- - Desde 2026-09-01 00:00:00
-- - Hasta 2026-11-30 18:00:00
-- - Frecuencia: cada 6 horas
--
-- Contexto ambiental simulado:
-- - Primavera en zona centro-sur.
-- - Menor MP2.5 que en invierno por menor uso de calefacción a leña.
-- - Mayor velocidad del viento en varios días, favoreciendo dispersión.
-- - Episodios puntuales de contaminación industrial en Biobío.
-- - Episodios puntuales por actividad agrícola/quemas controladas simuladas
--   en Maule y O'Higgins.
-- - Aumento progresivo de temperatura hacia noviembre.
-- ============================================================

BEGIN;


-- ============================================================
-- 1. COMUNAS ADICIONALES
-- Se agregan nuevas comunas para ampliar cobertura territorial.
-- Si ya existen, no se duplican.
-- ============================================================

INSERT INTO comunas (
    nombre,
    region,
    poblacion_estimada,
    indice_vulnerabilidad_respiratoria
) VALUES
    ('San Vicente',       'O''Higgins',  51000, 59.60),
    ('Machalí',           'O''Higgins',  61000, 54.80),
    ('Molina',            'Maule',       46000, 62.50),
    ('San Javier',        'Maule',       49000, 66.30),
    ('Bulnes',            'Ñuble',       23000, 67.40),
    ('Coihueco',          'Ñuble',       27000, 69.10),
    ('Talcahuano',        'Biobío',     158000, 70.20),
    ('Arauco',            'Biobío',      38000, 72.70)
ON CONFLICT (nombre) DO NOTHING;


-- ============================================================
-- 2. SENSORES ADICIONALES
-- Se agregan sensores oficiales y comunitarios para las nuevas comunas.
-- También se agregan algunos sensores extra en comunas ya existentes.
-- ============================================================

INSERT INTO estaciones_sensores (
    codigo_unico,
    tipo,
    latitud,
    longitud,
    id_comuna
) VALUES
    ('SEN-SVI-ONG-001', 'sensor_comunitario_ong', -34.438600, -71.077000, (SELECT id_comuna FROM comunas WHERE nombre = 'San Vicente')),
    ('SEN-MAC-OF-001',  'publico_oficial',        -34.180800, -70.649300, (SELECT id_comuna FROM comunas WHERE nombre = 'Machalí')),
    ('SEN-MOL-ONG-001', 'sensor_comunitario_ong', -35.114100, -71.282400, (SELECT id_comuna FROM comunas WHERE nombre = 'Molina')),
    ('SEN-SJA-OF-001',  'publico_oficial',        -35.595800, -71.729200, (SELECT id_comuna FROM comunas WHERE nombre = 'San Javier')),
    ('SEN-BUL-ONG-001', 'sensor_comunitario_ong', -36.742300, -72.298000, (SELECT id_comuna FROM comunas WHERE nombre = 'Bulnes')),
    ('SEN-COI-ONG-001', 'sensor_comunitario_ong', -36.628200, -71.834100, (SELECT id_comuna FROM comunas WHERE nombre = 'Coihueco')),
    ('SEN-TALC-OF-001', 'publico_oficial',        -36.724900, -73.116800, (SELECT id_comuna FROM comunas WHERE nombre = 'Talcahuano')),
    ('SEN-ARA-ONG-001', 'sensor_comunitario_ong', -37.246300, -73.317500, (SELECT id_comuna FROM comunas WHERE nombre = 'Arauco')),

    -- Sensores extra en comunas ya existentes para mejorar cobertura
    ('SEN-COR-ONG-002', 'sensor_comunitario_ong', -37.009500, -73.120500, (SELECT id_comuna FROM comunas WHERE nombre = 'Coronel')),
    ('SEN-HUA-ONG-002', 'sensor_comunitario_ong', -36.793700, -73.086500, (SELECT id_comuna FROM comunas WHERE nombre = 'Hualpén')),
    ('SEN-TAL-ONG-002', 'sensor_comunitario_ong', -35.418900, -71.666200, (SELECT id_comuna FROM comunas WHERE nombre = 'Talca')),
    ('SEN-LAN-ONG-002', 'sensor_comunitario_ong', -37.475900, -72.342500, (SELECT id_comuna FROM comunas WHERE nombre = 'Los Ángeles'))
ON CONFLICT (codigo_unico) DO NOTHING;


-- ============================================================
-- 3. INDUSTRIAS ADICIONALES
-- Se agregan nuevas fuentes fijas coherentes con la cobertura ampliada.
-- ============================================================

INSERT INTO industrias_fuentes (
    nombre,
    rubro_industrial,
    emision_maxima_permitida,
    id_comuna
) VALUES
    ('Agroindustrial San Vicente',        'Agroindustria',            105.00, (SELECT id_comuna FROM comunas WHERE nombre = 'San Vicente')),
    ('Planta Minera Machalí',             'Minería y procesamiento',  280.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Machalí')),
    ('Procesadora Agrícola Molina',       'Agroindustria',             92.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Molina')),
    ('Planta Maderera San Javier',        'Procesamiento de madera',  135.00, (SELECT id_comuna FROM comunas WHERE nombre = 'San Javier')),
    ('Caldera Industrial Bulnes',         'Calderas industriales',    145.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Bulnes')),
    ('Secadora Forestal Coihueco',        'Procesamiento forestal',   125.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Coihueco')),
    ('Puerto Industrial Talcahuano',      'Actividad portuaria',      360.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Talcahuano')),
    ('Celulosa Arauco Costa',             'Celulosa y papel',         540.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Arauco')),
    ('Terminal de Combustibles Hualpén',  'Almacenamiento energético',220.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Hualpén')),
    ('Parque Industrial Coronel Sur',     'Manufactura industrial',   275.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Coronel'))
ON CONFLICT (nombre) DO NOTHING;


-- ============================================================
-- 4. MONITOREO AMBIENTAL - PRIMAVERA 2026
--
-- Genera mediciones para TODOS los sensores existentes.
-- Si una medición ya existe para id_estacion + fecha_hora, no se duplica.
-- ============================================================

WITH calendario AS (
    SELECT generate_series(
        TIMESTAMP '2026-09-01 00:00:00',
        TIMESTAMP '2026-11-30 18:00:00',
        INTERVAL '6 hours'
    ) AS fecha_hora
),

sensores AS (
    SELECT
        s.id_estacion,
        s.codigo_unico,
        s.tipo,
        c.nombre AS comuna,
        c.region,
        c.indice_vulnerabilidad_respiratoria
    FROM estaciones_sensores s
    INNER JOIN comunas c
        ON c.id_comuna = s.id_comuna
),

base AS (
    SELECT
        sen.id_estacion,
        sen.codigo_unico,
        sen.tipo,
        sen.comuna,
        sen.region,
        sen.indice_vulnerabilidad_respiratoria,
        cal.fecha_hora,
        EXTRACT(DAY FROM cal.fecha_hora)::INTEGER AS dia_mes,
        EXTRACT(DOY FROM cal.fecha_hora)::INTEGER AS dia_anio,
        EXTRACT(HOUR FROM cal.fecha_hora)::INTEGER AS hora,
        EXTRACT(DOW FROM cal.fecha_hora)::INTEGER AS dia_semana,
        EXTRACT(MONTH FROM cal.fecha_hora)::INTEGER AS mes,

        -- Episodios puntuales simulados:
        -- 1 = evento agrícola/quema controlada o baja ventilación
        -- 2 = evento industrial localizado
        CASE
            WHEN cal.fecha_hora::DATE BETWEEN DATE '2026-09-10' AND DATE '2026-09-12'
                 AND sen.region IN ('O''Higgins', 'Maule') THEN 1
            WHEN cal.fecha_hora::DATE BETWEEN DATE '2026-10-04' AND DATE '2026-10-05'
                 AND sen.comuna IN ('Talca', 'Curicó', 'Molina', 'San Javier', 'Linares') THEN 1
            WHEN cal.fecha_hora::DATE BETWEEN DATE '2026-10-22' AND DATE '2026-10-24'
                 AND sen.comuna IN ('Hualpén', 'Talcahuano', 'Coronel', 'Lota', 'Penco', 'Arauco') THEN 2
            WHEN cal.fecha_hora::DATE BETWEEN DATE '2026-11-15' AND DATE '2026-11-16'
                 AND sen.comuna IN ('Chillán', 'Bulnes', 'Coihueco', 'San Carlos') THEN 1
            ELSE 0
        END AS evento_simulado

    FROM sensores sen
    CROSS JOIN calendario cal
),

calculos AS (
    SELECT
        id_estacion,
        codigo_unico,
        tipo,
        comuna,
        region,
        indice_vulnerabilidad_respiratoria,
        fecha_hora,
        dia_mes,
        dia_anio,
        hora,
        dia_semana,
        mes,
        evento_simulado,

        -- Temperatura: aumenta progresivamente hacia noviembre.
        (
            CASE hora
                WHEN 0 THEN 8.00
                WHEN 6 THEN 9.20
                WHEN 12 THEN 19.50
                WHEN 18 THEN 15.40
                ELSE 14.00
            END
            +
            CASE mes
                WHEN 9 THEN 0.00
                WHEN 10 THEN 2.40
                WHEN 11 THEN 4.80
                ELSE 0.00
            END
            +
            CASE region
                WHEN 'O''Higgins' THEN 1.60
                WHEN 'Maule' THEN 1.10
                WHEN 'Ñuble' THEN 0.50
                WHEN 'Biobío' THEN 0.10
                ELSE 0.00
            END
            -
            CASE
                WHEN evento_simulado = 1 THEN 0.80
                ELSE 0.00
            END
            +
            ((dia_anio % 6) * 0.12)
        )::NUMERIC AS temperatura_calc,

        -- Humedad: menor que en invierno, pero alta en madrugada.
        LEAST(
            96,
            GREATEST(
                32,
                (
                    CASE hora
                        WHEN 0 THEN 78
                        WHEN 6 THEN 83
                        WHEN 12 THEN 47
                        WHEN 18 THEN 61
                        ELSE 60
                    END
                    -
                    CASE mes
                        WHEN 9 THEN 0
                        WHEN 10 THEN 5
                        WHEN 11 THEN 9
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN evento_simulado = 1 THEN 6
                        ELSE 0
                    END
                    +
                    (dia_anio % 5)
                )
            )
        )::NUMERIC AS humedad_calc,

        -- Viento: primavera con mayor ventilación promedio.
        GREATEST(
            0.40,
            (
                CASE hora
                    WHEN 0 THEN 1.30
                    WHEN 6 THEN 1.60
                    WHEN 12 THEN 4.80
                    WHEN 18 THEN 3.70
                    ELSE 2.40
                END
                +
                CASE mes
                    WHEN 9 THEN 0.20
                    WHEN 10 THEN 0.55
                    WHEN 11 THEN 0.85
                    ELSE 0.00
                END
                +
                ((dia_anio % 5) * 0.18)
                -
                CASE
                    WHEN evento_simulado IN (1, 2) THEN 0.65
                    ELSE 0.00
                END
            )
        )::NUMERIC AS viento_calc,

        -- Dirección: distribución determinística para reproducibilidad.
        (
            (
                (id_estacion * 37)
                + (dia_anio * 17)
                + (hora * 5)
                + (mes * 9)
            ) % 361
        )::NUMERIC AS direccion_calc,

        -- MP2.5: menor que invierno, pero con eventos puntuales.
        GREATEST(
            3,
            (
                CASE comuna
                    WHEN 'Los Ángeles'  THEN 30
                    WHEN 'Chillán'      THEN 29
                    WHEN 'Nacimiento'   THEN 28
                    WHEN 'San Carlos'   THEN 27
                    WHEN 'Coihueco'     THEN 27
                    WHEN 'Bulnes'       THEN 26
                    WHEN 'Parral'       THEN 26
                    WHEN 'Linares'      THEN 25
                    WHEN 'Cabrero'      THEN 25
                    WHEN 'Coronel'      THEN 29
                    WHEN 'Lota'         THEN 28
                    WHEN 'Arauco'       THEN 27
                    WHEN 'Hualpén'      THEN 26
                    WHEN 'Talcahuano'   THEN 26
                    WHEN 'Rancagua'     THEN 24
                    WHEN 'San Vicente'  THEN 24
                    WHEN 'Talca'        THEN 23
                    WHEN 'Curicó'       THEN 22
                    WHEN 'Molina'       THEN 22
                    WHEN 'San Javier'   THEN 23
                    WHEN 'Concepción'   THEN 22
                    WHEN 'Penco'        THEN 23
                    ELSE 21
                END
                +
                CASE hora
                    WHEN 0 THEN 10
                    WHEN 6 THEN 8
                    WHEN 12 THEN -6
                    WHEN 18 THEN 4
                    ELSE 0
                END
                +
                CASE
                    WHEN dia_semana IN (0, 6) THEN 2.5
                    ELSE 0
                END
                +
                CASE
                    WHEN evento_simulado = 1 THEN 30
                    WHEN evento_simulado = 2 THEN 18
                    ELSE 0
                END
                -
                CASE mes
                    WHEN 9 THEN 0
                    WHEN 10 THEN 3
                    WHEN 11 THEN 6
                    ELSE 0
                END
                +
                CASE
                    WHEN tipo = 'sensor_comunitario_ong' THEN 1.5
                    ELSE 0
                END
                +
                ((dia_anio % 8) * 0.85)
            )
        )::NUMERIC AS mp25_calc,

        -- SO2: mayor en zonas industriales, con evento industrial en octubre.
        (
            CASE comuna
                WHEN 'Hualpén'      THEN 46
                WHEN 'Talcahuano'   THEN 50
                WHEN 'Coronel'      THEN 52
                WHEN 'Lota'         THEN 47
                WHEN 'Arauco'       THEN 42
                WHEN 'Penco'        THEN 41
                WHEN 'Concepción'   THEN 35
                WHEN 'Nacimiento'   THEN 34
                WHEN 'Rancagua'     THEN 30
                WHEN 'Machalí'      THEN 32
                WHEN 'Talca'        THEN 24
                WHEN 'Constitución' THEN 26
                ELSE 14
            END
            +
            CASE
                WHEN evento_simulado = 2 THEN 24
                WHEN evento_simulado = 1 THEN 5
                ELSE 0
            END
            +
            CASE
                WHEN hora IN (0, 6) THEN 4
                ELSE 0
            END
            +
            (dia_anio % 5)
        )::NUMERIC AS so2_calc,

        -- NO2: asociado a combustión, tráfico y zonas industriales.
        (
            CASE comuna
                WHEN 'Coronel'      THEN 60
                WHEN 'Hualpén'      THEN 58
                WHEN 'Talcahuano'   THEN 61
                WHEN 'Concepción'   THEN 53
                WHEN 'Lota'         THEN 55
                WHEN 'Penco'        THEN 50
                WHEN 'Rancagua'     THEN 47
                WHEN 'Machalí'      THEN 45
                WHEN 'Talca'        THEN 42
                WHEN 'Curicó'       THEN 38
                WHEN 'Los Ángeles'  THEN 37
                WHEN 'Chillán'      THEN 36
                ELSE 30
            END
            +
            CASE
                WHEN hora IN (6, 18) THEN 8
                ELSE 0
            END
            +
            CASE
                WHEN evento_simulado = 2 THEN 14
                WHEN evento_simulado = 1 THEN 4
                ELSE 0
            END
            +
            (dia_anio % 6)
        )::NUMERIC AS no2_calc

    FROM base
)

INSERT INTO monitoreo_ambiental (
    fecha_hora,
    id_estacion,
    mp25,
    mp10,
    so2,
    no2,
    velocidad_viento,
    direccion_viento_grados,
    temperatura,
    humedad
)
SELECT
    fecha_hora,
    id_estacion,

    ROUND(mp25_calc, 2) AS mp25,

    ROUND(
        (
            mp25_calc * 1.65
            +
            CASE
                WHEN comuna IN ('Coronel', 'Hualpén', 'Talcahuano', 'Lota', 'Penco', 'Arauco') THEN 32
                WHEN comuna IN ('Los Ángeles', 'Chillán', 'San Carlos', 'Nacimiento', 'Coihueco', 'Bulnes') THEN 18
                WHEN comuna IN ('Talca', 'Curicó', 'Molina', 'San Javier', 'Linares', 'Parral') THEN 16
                WHEN comuna IN ('Rancagua', 'San Vicente', 'Machalí') THEN 15
                ELSE 12
            END
            +
            CASE
                WHEN evento_simulado = 1 THEN 18
                WHEN evento_simulado = 2 THEN 12
                ELSE 0
            END
            +
            (dia_anio % 9)
        )::NUMERIC,
        2
    ) AS mp10,

    ROUND(so2_calc, 2) AS so2,
    ROUND(no2_calc, 2) AS no2,
    ROUND(viento_calc, 2) AS velocidad_viento,
    ROUND(direccion_calc, 2) AS direccion_viento_grados,
    ROUND(temperatura_calc, 2) AS temperatura,
    ROUND(humedad_calc, 2) AS humedad

FROM calculos
ON CONFLICT (id_estacion, fecha_hora) DO NOTHING;


-- ============================================================
-- 5. VALIDACIONES RÁPIDAS
-- ============================================================

SELECT COUNT(*) AS total_comunas
FROM comunas;

SELECT COUNT(*) AS total_estaciones_sensores
FROM estaciones_sensores;

SELECT COUNT(*) AS total_industrias_fuentes
FROM industrias_fuentes;

SELECT COUNT(*) AS total_monitoreo_ambiental
FROM monitoreo_ambiental;

SELECT
    MIN(fecha_hora) AS fecha_minima,
    MAX(fecha_hora) AS fecha_maxima
FROM monitoreo_ambiental;

-- Resumen por región para revisar distribución territorial
SELECT
    c.region,
    COUNT(DISTINCT c.id_comuna) AS comunas,
    COUNT(DISTINCT s.id_estacion) AS sensores
FROM comunas c
LEFT JOIN estaciones_sensores s
    ON s.id_comuna = c.id_comuna
GROUP BY c.region
ORDER BY c.region;

-- Distribución aproximada de categorías ICAP para las mediciones existentes
SELECT
    CASE
        WHEN ma.mp25 >= 170 OR ma.mp10 >= 330 THEN 'Emergencia'
        WHEN ma.mp25 >= 110 OR ma.mp10 >= 230 THEN 'Preemergencia'
        WHEN ma.mp25 >= 80  OR ma.mp10 >= 180 THEN 'Alerta'
        WHEN ma.mp25 >= 50  OR ma.mp10 >= 130 THEN 'Regular'
        ELSE 'Buena'
    END AS categoria_icap,
    COUNT(*) AS cantidad_registros
FROM monitoreo_ambiental ma
GROUP BY categoria_icap
ORDER BY
    CASE categoria_icap
        WHEN 'Buena' THEN 1
        WHEN 'Regular' THEN 2
        WHEN 'Alerta' THEN 3
        WHEN 'Preemergencia' THEN 4
        WHEN 'Emergencia' THEN 5
    END;

COMMIT;

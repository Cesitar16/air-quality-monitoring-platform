-- ============================================================
-- SEED: Monitoreo de Calidad del Aire
-- PostgreSQL
--
-- Este script puebla las 4 tablas principales del caso:
-- - comunas
-- - estaciones_sensores
-- - industrias_fuentes
-- - monitoreo_ambiental
--
-- Datos simulados con sentido ambiental:
-- - Comunas de O'Higgins, Maule, Ñuble y Biobío.
-- - Sensores oficiales y comunitarios.
-- - Industrias fuentes por comuna.
-- - Mediciones cada 6 horas durante 14 días de invierno.
-- - MP2.5 aumenta en horarios de baja temperatura/ventilación.
-- - Comunas del centro-sur con uso de leña presentan mayores valores.
-- - Zonas industriales presentan SO2/NO2 relativamente más altos.
-- ============================================================

BEGIN;

-- ============================================================
-- LIMPIEZA PARA EJECUCIÓN REPRODUCIBLE DEL SEED
-- ============================================================

TRUNCATE TABLE monitoreo_ambiental, industrias_fuentes, estaciones_sensores, comunas
RESTART IDENTITY CASCADE;


-- ============================================================
-- 1. COMUNAS
-- ============================================================

INSERT INTO comunas (
    nombre,
    region,
    poblacion_estimada,
    indice_vulnerabilidad_respiratoria
) VALUES
    ('Rancagua',     'O''Higgins', 265000, 61.50),
    ('San Fernando','O''Higgins',  78000, 58.00),
    ('Talca',        'Maule',     250000, 64.20),
    ('Curicó',       'Maule',     163000, 60.00),
    ('Chillán',      'Ñuble',     198000, 72.80),
    ('San Carlos',   'Ñuble',      53000, 66.10),
    ('Concepción',   'Biobío',    230000, 69.50),
    ('Hualpén',      'Biobío',     97000, 68.40),
    ('Coronel',      'Biobío',    125000, 76.20),
    ('Los Ángeles',  'Biobío',    202000, 74.30);


-- ============================================================
-- 2. ESTACIONES / SENSORES
-- ============================================================

INSERT INTO estaciones_sensores (
    codigo_unico,
    tipo,
    latitud,
    longitud,
    id_comuna
) VALUES
    (
        'SEN-RAN-OF-001',
        'publico_oficial',
        -34.170830,
        -70.744440,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Rancagua')
    ),
    (
        'SEN-RAN-ONG-001',
        'sensor_comunitario_ong',
        -34.176100,
        -70.730200,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Rancagua')
    ),
    (
        'SEN-SF-ONG-001',
        'sensor_comunitario_ong',
        -34.584200,
        -70.989000,
        (SELECT id_comuna FROM comunas WHERE nombre = 'San Fernando')
    ),
    (
        'SEN-TAL-OF-001',
        'publico_oficial',
        -35.426400,
        -71.655400,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Talca')
    ),
    (
        'SEN-CUR-ONG-001',
        'sensor_comunitario_ong',
        -34.982800,
        -71.239400,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Curicó')
    ),
    (
        'SEN-CHI-OF-001',
        'publico_oficial',
        -36.606640,
        -72.103440,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Chillán')
    ),
    (
        'SEN-CHI-ONG-001',
        'sensor_comunitario_ong',
        -36.615200,
        -72.118500,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Chillán')
    ),
    (
        'SEN-SCA-ONG-001',
        'sensor_comunitario_ong',
        -36.424800,
        -71.958000,
        (SELECT id_comuna FROM comunas WHERE nombre = 'San Carlos')
    ),
    (
        'SEN-CON-OF-001',
        'publico_oficial',
        -36.827000,
        -73.050300,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Concepción')
    ),
    (
        'SEN-HUA-OF-001',
        'publico_oficial',
        -36.787000,
        -73.102000,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Hualpén')
    ),
    (
        'SEN-COR-ONG-001',
        'sensor_comunitario_ong',
        -37.016700,
        -73.133300,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Coronel')
    ),
    (
        'SEN-LAN-OF-001',
        'publico_oficial',
        -37.469700,
        -72.353700,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Los Ángeles')
    );


-- ============================================================
-- 3. INDUSTRIAS / FUENTES FIJAS
-- ============================================================

INSERT INTO industrias_fuentes (
    nombre,
    rubro_industrial,
    emision_maxima_permitida,
    id_comuna
) VALUES
    (
        'Termoeléctrica Rancagua Centro',
        'Energía termoeléctrica',
        320.00,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Rancagua')
    ),
    (
        'Planta Secado Maderas San Fernando',
        'Procesamiento de madera',
        125.00,
        (SELECT id_comuna FROM comunas WHERE nombre = 'San Fernando')
    ),
    (
        'Celulosa Maule Norte',
        'Celulosa y papel',
        420.00,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Talca')
    ),
    (
        'Agroindustrial Curicó',
        'Agroindustria',
        95.00,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Curicó')
    ),
    (
        'Planta de Calderas Chillán',
        'Calderas industriales',
        180.00,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Chillán')
    ),
    (
        'Complejo Industrial Hualpén',
        'Refinería y petroquímica',
        500.00,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Hualpén')
    ),
    (
        'Central Termoeléctrica Coronel',
        'Energía termoeléctrica',
        650.00,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Coronel')
    ),
    (
        'Fundición Biobío',
        'Fundición y metalurgia',
        390.00,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Concepción')
    ),
    (
        'Planta Biomasa Los Ángeles',
        'Energía biomasa',
        260.00,
        (SELECT id_comuna FROM comunas WHERE nombre = 'Los Ángeles')
    );


-- ============================================================
-- 4. MONITOREO AMBIENTAL
-- ============================================================
-- Se generan mediciones cada 6 horas entre el 01-06-2026 y 14-06-2026.
--
-- Criterio de simulación:
-- - Horarios nocturnos/madrugada tienen mayor MP2.5 por menor ventilación.
-- - Días 5, 6 y 12 simulan episodios críticos de invierno.
-- - Chillán, San Carlos y Los Ángeles tienen valores mayores por contexto residencial/leña.
-- - Hualpén, Coronel y Concepción tienen SO2/NO2 más altos por presencia industrial.
-- ============================================================

WITH mediciones_base AS (
    SELECT
        s.id_estacion,
        s.codigo_unico,
        c.nombre AS comuna,
        c.region,
        gs.fecha_hora,

        (
            CASE c.nombre
                WHEN 'Chillán' THEN 48
                WHEN 'Los Ángeles' THEN 50
                WHEN 'San Carlos' THEN 43
                WHEN 'Coronel' THEN 45
                WHEN 'Hualpén' THEN 38
                WHEN 'Rancagua' THEN 36
                WHEN 'Talca' THEN 34
                WHEN 'Concepción' THEN 32
                WHEN 'Curicó' THEN 31
                WHEN 'San Fernando' THEN 30
                ELSE 28
            END
            +
            CASE EXTRACT(HOUR FROM gs.fecha_hora)::INTEGER
                WHEN 0 THEN 22
                WHEN 6 THEN 18
                WHEN 12 THEN -5
                WHEN 18 THEN 12
                ELSE 0
            END
            +
            ((EXTRACT(DAY FROM gs.fecha_hora)::INTEGER % 5) * 2)
            +
            CASE
                WHEN EXTRACT(DAY FROM gs.fecha_hora)::INTEGER IN (5, 6, 12)
                     AND c.nombre IN ('Chillán', 'Los Ángeles', 'San Carlos')
                    THEN 35
                WHEN EXTRACT(DAY FROM gs.fecha_hora)::INTEGER IN (5, 6, 12)
                    THEN 20
                ELSE 0
            END
        )::NUMERIC AS mp25_calc,

        (
            CASE c.nombre
                WHEN 'Hualpén' THEN 42
                WHEN 'Coronel' THEN 48
                WHEN 'Concepción' THEN 32
                WHEN 'Rancagua' THEN 28
                WHEN 'Talca' THEN 24
                WHEN 'Chillán' THEN 18
                WHEN 'Los Ángeles' THEN 20
                ELSE 12
            END
            +
            CASE
                WHEN EXTRACT(HOUR FROM gs.fecha_hora)::INTEGER IN (0, 6) THEN 5
                ELSE 0
            END
            +
            (EXTRACT(DAY FROM gs.fecha_hora)::INTEGER % 4)
        )::NUMERIC AS so2_calc,

        (
            CASE c.nombre
                WHEN 'Hualpén' THEN 56
                WHEN 'Coronel' THEN 62
                WHEN 'Concepción' THEN 50
                WHEN 'Rancagua' THEN 48
                WHEN 'Talca' THEN 42
                WHEN 'Chillán' THEN 35
                WHEN 'Los Ángeles' THEN 36
                ELSE 28
            END
            +
            CASE
                WHEN EXTRACT(HOUR FROM gs.fecha_hora)::INTEGER IN (6, 18) THEN 8
                ELSE 0
            END
            +
            (EXTRACT(DAY FROM gs.fecha_hora)::INTEGER % 5)
        )::NUMERIC AS no2_calc,

        GREATEST(
            0.30,
            (
                CASE EXTRACT(HOUR FROM gs.fecha_hora)::INTEGER
                    WHEN 0 THEN 0.80
                    WHEN 6 THEN 1.10
                    WHEN 12 THEN 3.80
                    WHEN 18 THEN 2.30
                    ELSE 1.50
                END
                +
                ((EXTRACT(DAY FROM gs.fecha_hora)::INTEGER % 3) * 0.25)
                -
                CASE
                    WHEN EXTRACT(DAY FROM gs.fecha_hora)::INTEGER IN (5, 6, 12) THEN 0.40
                    ELSE 0
                END
            )
        )::NUMERIC AS velocidad_viento_calc,

        (
            (
                (s.id_estacion * 27)
                + (EXTRACT(DAY FROM gs.fecha_hora)::INTEGER * 13)
                + (EXTRACT(HOUR FROM gs.fecha_hora)::INTEGER * 3)
            ) % 361
        )::NUMERIC AS direccion_viento_calc,

        (
            CASE EXTRACT(HOUR FROM gs.fecha_hora)::INTEGER
                WHEN 0 THEN 5.50
                WHEN 6 THEN 4.80
                WHEN 12 THEN 13.50
                WHEN 18 THEN 8.20
                ELSE 9.00
            END
            +
            CASE c.region
                WHEN 'O''Higgins' THEN 1.50
                WHEN 'Maule' THEN 0.80
                WHEN 'Ñuble' THEN 0.20
                WHEN 'Biobío' THEN 0.00
                ELSE 0.00
            END
            -
            CASE
                WHEN EXTRACT(DAY FROM gs.fecha_hora)::INTEGER IN (5, 6, 12) THEN 1.20
                ELSE 0.00
            END
        )::NUMERIC AS temperatura_calc,

        LEAST(
            98,
            (
                CASE EXTRACT(HOUR FROM gs.fecha_hora)::INTEGER
                    WHEN 0 THEN 88
                    WHEN 6 THEN 92
                    WHEN 12 THEN 62
                    WHEN 18 THEN 78
                    ELSE 75
                END
                +
                (EXTRACT(DAY FROM gs.fecha_hora)::INTEGER % 6)
                +
                CASE
                    WHEN EXTRACT(DAY FROM gs.fecha_hora)::INTEGER IN (5, 6, 12) THEN 3
                    ELSE 0
                END
            )
        )::NUMERIC AS humedad_calc

    FROM estaciones_sensores s
    INNER JOIN comunas c
        ON c.id_comuna = s.id_comuna
    CROSS JOIN generate_series(
        TIMESTAMP '2026-06-01 00:00:00',
        TIMESTAMP '2026-06-14 18:00:00',
        INTERVAL '6 hours'
    ) AS gs(fecha_hora)
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
            mp25_calc * 1.75
            +
            CASE
                WHEN comuna IN ('Coronel', 'Hualpén', 'Concepción') THEN 35
                WHEN comuna IN ('Rancagua', 'Talca') THEN 20
                WHEN comuna IN ('Chillán', 'Los Ángeles', 'San Carlos') THEN 15
                ELSE 10
            END
        ),
        2
    ) AS mp10,

    ROUND(so2_calc, 2) AS so2,
    ROUND(no2_calc, 2) AS no2,
    ROUND(velocidad_viento_calc, 2) AS velocidad_viento,
    ROUND(direccion_viento_calc, 2) AS direccion_viento_grados,
    ROUND(temperatura_calc, 2) AS temperatura,
    ROUND(humedad_calc, 2) AS humedad

FROM mediciones_base
ORDER BY id_estacion, fecha_hora;


-- ============================================================
-- VALIDACIÓN RÁPIDA DEL SEED
-- ============================================================

-- Total comunas esperadas: 10
SELECT COUNT(*) AS total_comunas FROM comunas;

-- Total sensores esperados: 12
SELECT COUNT(*) AS total_estaciones_sensores FROM estaciones_sensores;

-- Total industrias esperadas: 9
SELECT COUNT(*) AS total_industrias_fuentes FROM industrias_fuentes;

-- Total mediciones esperadas: 672
-- 12 sensores * 56 timestamps = 672 registros
SELECT COUNT(*) AS total_monitoreo_ambiental FROM monitoreo_ambiental;

COMMIT;

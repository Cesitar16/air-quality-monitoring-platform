-- ============================================================
-- SEED 02: Monitoreo de Calidad del Aire
-- PostgreSQL
--
-- Objetivo:
-- - Agregar más datos simulados al proyecto.
-- - Mantener coherencia con la BDD de 4 tablas principales.
-- - No eliminar datos existentes.
-- - Puede ejecutarse después del primer seed.
-- - También puede ejecutarse varias veces sin duplicar comunas,
--   sensores, industrias ni mediciones, gracias a ON CONFLICT.
--
-- Periodo simulado:
-- - Desde 2026-06-15 00:00:00
-- - Hasta 2026-08-31 18:00:00
-- - Frecuencia: cada 6 horas
--
-- Criterio ambiental de simulación:
-- - Invierno en zona centro-sur.
-- - Mayores niveles de MP2.5 en noche y madrugada.
-- - Episodios críticos simulados en algunos periodos.
-- - Comunas con fuerte calefacción residencial/leña tienen más MP2.5.
-- - Comunas industriales tienen más SO2 y NO2.
-- - Baja velocidad del viento aumenta la acumulación de contaminantes.
-- ============================================================

BEGIN;


-- ============================================================
-- 1. COMUNAS
-- Se agregan comunas adicionales para ampliar el análisis territorial.
-- ON CONFLICT evita duplicados si ya existen.
-- ============================================================

INSERT INTO comunas (
    nombre,
    region,
    poblacion_estimada,
    indice_vulnerabilidad_respiratoria
) VALUES
    ('Rancagua',      'O''Higgins', 265000, 61.50),
    ('San Fernando', 'O''Higgins',  78000, 58.00),
    ('Talca',         'Maule',     250000, 64.20),
    ('Curicó',        'Maule',     163000, 60.00),
    ('Chillán',       'Ñuble',     198000, 72.80),
    ('San Carlos',    'Ñuble',      53000, 66.10),
    ('Concepción',    'Biobío',    230000, 69.50),
    ('Hualpén',       'Biobío',     97000, 68.40),
    ('Coronel',       'Biobío',    125000, 76.20),
    ('Los Ángeles',   'Biobío',    202000, 74.30),

    -- Comunas adicionales
    ('Linares',       'Maule',     101000, 67.80),
    ('Parral',        'Maule',      42000, 70.40),
    ('Constitución',  'Maule',      50000, 63.20),
    ('Cauquenes',     'Maule',      41000, 65.90),
    ('Tomé',          'Biobío',     58000, 66.70),
    ('Penco',         'Biobío',     49000, 64.80),
    ('Lota',          'Biobío',     44000, 73.90),
    ('Nacimiento',    'Biobío',     28000, 71.60),
    ('Cabrero',       'Biobío',     30000, 69.30)
ON CONFLICT (nombre) DO NOTHING;


-- ============================================================
-- 2. ESTACIONES / SENSORES
-- Se agregan nuevos sensores oficiales y comunitarios.
-- Si algunos códigos ya existen, no se duplican.
-- ============================================================

INSERT INTO estaciones_sensores (
    codigo_unico,
    tipo,
    latitud,
    longitud,
    id_comuna
) VALUES
    -- Sensores base, para que el seed 02 también sea consistente si se ejecuta solo
    ('SEN-RAN-OF-001',  'publico_oficial',        -34.170830, -70.744440, (SELECT id_comuna FROM comunas WHERE nombre = 'Rancagua')),
    ('SEN-RAN-ONG-001', 'sensor_comunitario_ong', -34.176100, -70.730200, (SELECT id_comuna FROM comunas WHERE nombre = 'Rancagua')),
    ('SEN-SF-ONG-001',  'sensor_comunitario_ong', -34.584200, -70.989000, (SELECT id_comuna FROM comunas WHERE nombre = 'San Fernando')),
    ('SEN-TAL-OF-001',  'publico_oficial',        -35.426400, -71.655400, (SELECT id_comuna FROM comunas WHERE nombre = 'Talca')),
    ('SEN-CUR-ONG-001', 'sensor_comunitario_ong', -34.982800, -71.239400, (SELECT id_comuna FROM comunas WHERE nombre = 'Curicó')),
    ('SEN-CHI-OF-001',  'publico_oficial',        -36.606640, -72.103440, (SELECT id_comuna FROM comunas WHERE nombre = 'Chillán')),
    ('SEN-CHI-ONG-001', 'sensor_comunitario_ong', -36.615200, -72.118500, (SELECT id_comuna FROM comunas WHERE nombre = 'Chillán')),
    ('SEN-SCA-ONG-001', 'sensor_comunitario_ong', -36.424800, -71.958000, (SELECT id_comuna FROM comunas WHERE nombre = 'San Carlos')),
    ('SEN-CON-OF-001',  'publico_oficial',        -36.827000, -73.050300, (SELECT id_comuna FROM comunas WHERE nombre = 'Concepción')),
    ('SEN-HUA-OF-001',  'publico_oficial',        -36.787000, -73.102000, (SELECT id_comuna FROM comunas WHERE nombre = 'Hualpén')),
    ('SEN-COR-ONG-001', 'sensor_comunitario_ong', -37.016700, -73.133300, (SELECT id_comuna FROM comunas WHERE nombre = 'Coronel')),
    ('SEN-LAN-OF-001',  'publico_oficial',        -37.469700, -72.353700, (SELECT id_comuna FROM comunas WHERE nombre = 'Los Ángeles')),

    -- Sensores adicionales
    ('SEN-RAN-ONG-002', 'sensor_comunitario_ong', -34.158900, -70.726500, (SELECT id_comuna FROM comunas WHERE nombre = 'Rancagua')),
    ('SEN-SF-OF-001',   'publico_oficial',        -34.587800, -70.982400, (SELECT id_comuna FROM comunas WHERE nombre = 'San Fernando')),
    ('SEN-TAL-ONG-001', 'sensor_comunitario_ong', -35.433200, -71.641800, (SELECT id_comuna FROM comunas WHERE nombre = 'Talca')),
    ('SEN-CUR-OF-001',  'publico_oficial',        -34.985400, -71.247900, (SELECT id_comuna FROM comunas WHERE nombre = 'Curicó')),
    ('SEN-CHI-ONG-002', 'sensor_comunitario_ong', -36.600800, -72.089200, (SELECT id_comuna FROM comunas WHERE nombre = 'Chillán')),
    ('SEN-SCA-OF-001',  'publico_oficial',        -36.426500, -71.963300, (SELECT id_comuna FROM comunas WHERE nombre = 'San Carlos')),
    ('SEN-CON-ONG-001', 'sensor_comunitario_ong', -36.820600, -73.043100, (SELECT id_comuna FROM comunas WHERE nombre = 'Concepción')),
    ('SEN-HUA-ONG-001', 'sensor_comunitario_ong', -36.781200, -73.094900, (SELECT id_comuna FROM comunas WHERE nombre = 'Hualpén')),
    ('SEN-COR-OF-001',  'publico_oficial',        -37.022600, -73.142100, (SELECT id_comuna FROM comunas WHERE nombre = 'Coronel')),
    ('SEN-LAN-ONG-001', 'sensor_comunitario_ong', -37.462100, -72.359900, (SELECT id_comuna FROM comunas WHERE nombre = 'Los Ángeles')),

    ('SEN-LIN-OF-001',  'publico_oficial',        -35.846700, -71.593100, (SELECT id_comuna FROM comunas WHERE nombre = 'Linares')),
    ('SEN-LIN-ONG-001', 'sensor_comunitario_ong', -35.851200, -71.584500, (SELECT id_comuna FROM comunas WHERE nombre = 'Linares')),
    ('SEN-PAR-ONG-001', 'sensor_comunitario_ong', -36.143100, -71.826100, (SELECT id_comuna FROM comunas WHERE nombre = 'Parral')),
    ('SEN-CONST-OF-001','publico_oficial',        -35.333300, -72.416700, (SELECT id_comuna FROM comunas WHERE nombre = 'Constitución')),
    ('SEN-CAU-ONG-001', 'sensor_comunitario_ong', -35.967700, -72.322900, (SELECT id_comuna FROM comunas WHERE nombre = 'Cauquenes')),
    ('SEN-TOM-ONG-001', 'sensor_comunitario_ong', -36.617600, -72.955400, (SELECT id_comuna FROM comunas WHERE nombre = 'Tomé')),
    ('SEN-PEN-OF-001',  'publico_oficial',        -36.740600, -72.995400, (SELECT id_comuna FROM comunas WHERE nombre = 'Penco')),
    ('SEN-LOT-ONG-001', 'sensor_comunitario_ong', -37.089900, -73.157700, (SELECT id_comuna FROM comunas WHERE nombre = 'Lota')),
    ('SEN-NAC-OF-001',  'publico_oficial',        -37.502400, -72.673100, (SELECT id_comuna FROM comunas WHERE nombre = 'Nacimiento')),
    ('SEN-CAB-ONG-001', 'sensor_comunitario_ong', -37.033300, -72.400000, (SELECT id_comuna FROM comunas WHERE nombre = 'Cabrero'))
ON CONFLICT (codigo_unico) DO NOTHING;


-- ============================================================
-- 3. INDUSTRIAS / FUENTES FIJAS
-- Se agregan fuentes industriales coherentes con la zona.
-- ON CONFLICT evita duplicados por nombre.
-- ============================================================

INSERT INTO industrias_fuentes (
    nombre,
    rubro_industrial,
    emision_maxima_permitida,
    id_comuna
) VALUES
    -- Industrias base
    ('Termoeléctrica Rancagua Centro',     'Energía termoeléctrica', 320.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Rancagua')),
    ('Planta Secado Maderas San Fernando','Procesamiento de madera',125.00, (SELECT id_comuna FROM comunas WHERE nombre = 'San Fernando')),
    ('Celulosa Maule Norte',              'Celulosa y papel',       420.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Talca')),
    ('Agroindustrial Curicó',             'Agroindustria',           95.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Curicó')),
    ('Planta de Calderas Chillán',        'Calderas industriales',  180.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Chillán')),
    ('Complejo Industrial Hualpén',       'Refinería y petroquímica',500.00,(SELECT id_comuna FROM comunas WHERE nombre = 'Hualpén')),
    ('Central Termoeléctrica Coronel',    'Energía termoeléctrica', 650.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Coronel')),
    ('Fundición Biobío',                  'Fundición y metalurgia', 390.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Concepción')),
    ('Planta Biomasa Los Ángeles',        'Energía biomasa',        260.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Los Ángeles')),

    -- Industrias adicionales
    ('Planta Maderera Linares Sur',       'Procesamiento de madera',155.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Linares')),
    ('Secadora Agrícola Parral',          'Agroindustria',           90.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Parral')),
    ('Puerto Industrial Constitución',    'Actividad portuaria',    210.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Constitución')),
    ('Planta Pesquera Tomé',              'Procesamiento pesquero', 140.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Tomé')),
    ('Cementera Penco',                   'Cemento y áridos',       310.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Penco')),
    ('Central Térmica Lota',              'Energía termoeléctrica', 430.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Lota')),
    ('Celulosa Nacimiento',               'Celulosa y papel',       520.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Nacimiento')),
    ('Planta Industrial Cabrero',         'Manufactura industrial', 190.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Cabrero')),
    ('Planta de Calefacción Distrital Ñuble','Calderas industriales',160.00,(SELECT id_comuna FROM comunas WHERE nombre = 'Chillán')),
    ('Maestranza Talca Oriente',          'Metalurgia menor',       115.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Talca')),
    ('Terminal Logístico Hualpén',        'Logística industrial',   150.00, (SELECT id_comuna FROM comunas WHERE nombre = 'Hualpén'))
ON CONFLICT (nombre) DO NOTHING;


-- ============================================================
-- 4. MONITOREO AMBIENTAL AMPLIADO
--
-- Se generan datos para TODOS los sensores existentes en la BDD.
-- Esto incluye sensores del primer seed y sensores nuevos de este seed.
--
-- Si una medición ya existe para un sensor y fecha/hora, no se duplica.
-- ============================================================

WITH calendario AS (
    SELECT generate_series(
        TIMESTAMP '2026-06-15 00:00:00',
        TIMESTAMP '2026-08-31 18:00:00',
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
        cal.fecha_hora,
        EXTRACT(DAY FROM cal.fecha_hora)::INTEGER AS dia_mes,
        EXTRACT(DOY FROM cal.fecha_hora)::INTEGER AS dia_anio,
        EXTRACT(HOUR FROM cal.fecha_hora)::INTEGER AS hora,
        EXTRACT(DOW FROM cal.fecha_hora)::INTEGER AS dia_semana,

        CASE
            WHEN cal.fecha_hora::DATE BETWEEN DATE '2026-06-19' AND DATE '2026-06-21' THEN 1
            WHEN cal.fecha_hora::DATE BETWEEN DATE '2026-07-03' AND DATE '2026-07-05' THEN 1
            WHEN cal.fecha_hora::DATE BETWEEN DATE '2026-07-18' AND DATE '2026-07-19' THEN 1
            WHEN cal.fecha_hora::DATE BETWEEN DATE '2026-08-07' AND DATE '2026-08-08' THEN 1
            WHEN cal.fecha_hora::DATE BETWEEN DATE '2026-08-20' AND DATE '2026-08-22' THEN 2
            ELSE 0
        END AS episodio_invierno

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
        fecha_hora,
        dia_mes,
        dia_anio,
        hora,
        dia_semana,
        episodio_invierno,

        GREATEST(
            5,
            (
                CASE comuna
                    WHEN 'Los Ángeles'  THEN 55
                    WHEN 'Chillán'      THEN 53
                    WHEN 'Nacimiento'   THEN 51
                    WHEN 'San Carlos'   THEN 48
                    WHEN 'Parral'       THEN 47
                    WHEN 'Linares'      THEN 45
                    WHEN 'Cabrero'      THEN 44
                    WHEN 'Coronel'      THEN 46
                    WHEN 'Lota'         THEN 45
                    WHEN 'Hualpén'      THEN 40
                    WHEN 'Rancagua'     THEN 38
                    WHEN 'Talca'        THEN 36
                    WHEN 'Concepción'   THEN 35
                    WHEN 'Curicó'       THEN 33
                    WHEN 'San Fernando' THEN 31
                    WHEN 'Constitución' THEN 30
                    WHEN 'Tomé'         THEN 29
                    WHEN 'Penco'        THEN 32
                    WHEN 'Cauquenes'    THEN 34
                    ELSE 30
                END
                +
                CASE hora
                    WHEN 0 THEN 24
                    WHEN 6 THEN 20
                    WHEN 12 THEN -8
                    WHEN 18 THEN 14
                    ELSE 0
                END
                +
                CASE
                    WHEN dia_semana IN (0, 6) THEN 5
                    ELSE 0
                END
                +
                CASE
                    WHEN episodio_invierno = 1
                         AND comuna IN ('Los Ángeles', 'Chillán', 'Nacimiento', 'San Carlos', 'Parral', 'Linares', 'Cabrero', 'Cauquenes')
                        THEN 42
                    WHEN episodio_invierno = 1
                        THEN 25
                    WHEN episodio_invierno = 2
                         AND comuna IN ('Los Ángeles', 'Chillán', 'Nacimiento', 'San Carlos', 'Parral', 'Linares', 'Cabrero', 'Cauquenes')
                        THEN 88
                    WHEN episodio_invierno = 2
                        THEN 45
                    ELSE 0
                END
                +
                CASE
                    WHEN tipo = 'sensor_comunitario_ong' THEN 2
                    ELSE 0
                END
                +
                ((dia_anio % 7) * 1.35)
            )
        )::NUMERIC AS mp25_calc,

        GREATEST(
            0.30,
            (
                CASE hora
                    WHEN 0 THEN 0.70
                    WHEN 6 THEN 1.00
                    WHEN 12 THEN 4.10
                    WHEN 18 THEN 2.40
                    ELSE 1.50
                END
                +
                ((dia_anio % 4) * 0.22)
                -
                CASE
                    WHEN episodio_invierno > 0 THEN 0.35
                    ELSE 0
                END
            )
        )::NUMERIC AS viento_calc,

        (
            (
                (id_estacion * 31)
                + (dia_anio * 11)
                + (hora * 4)
            ) % 361
        )::NUMERIC AS direccion_calc,

        (
            CASE hora
                WHEN 0 THEN 5.10
                WHEN 6 THEN 4.20
                WHEN 12 THEN 13.20
                WHEN 18 THEN 8.00
                ELSE 9.00
            END
            +
            CASE region
                WHEN 'O''Higgins' THEN 1.60
                WHEN 'Maule' THEN 0.90
                WHEN 'Ñuble' THEN 0.30
                WHEN 'Biobío' THEN 0.10
                ELSE 0.00
            END
            -
            CASE
                WHEN episodio_invierno > 0 THEN 1.40
                ELSE 0.00
            END
            +
            ((dia_anio % 5) * 0.18)
        )::NUMERIC AS temperatura_calc,

        LEAST(
            98,
            (
                CASE hora
                    WHEN 0 THEN 89
                    WHEN 6 THEN 93
                    WHEN 12 THEN 61
                    WHEN 18 THEN 79
                    ELSE 75
                END
                +
                (dia_anio % 6)
                +
                CASE
                    WHEN episodio_invierno > 0 THEN 4
                    ELSE 0
                END
            )
        )::NUMERIC AS humedad_calc,

        (
            CASE comuna
                WHEN 'Hualpén'      THEN 48
                WHEN 'Coronel'      THEN 55
                WHEN 'Lota'         THEN 50
                WHEN 'Penco'        THEN 46
                WHEN 'Concepción'   THEN 38
                WHEN 'Nacimiento'   THEN 36
                WHEN 'Rancagua'     THEN 34
                WHEN 'Talca'        THEN 28
                WHEN 'Constitución' THEN 30
                WHEN 'Tomé'         THEN 24
                ELSE 16
            END
            +
            CASE
                WHEN hora IN (0, 6) THEN 6
                ELSE 0
            END
            +
            CASE
                WHEN episodio_invierno > 0
                     AND comuna IN ('Hualpén', 'Coronel', 'Lota', 'Penco', 'Concepción', 'Nacimiento')
                    THEN 8
                ELSE 0
            END
            +
            (dia_anio % 5)
        )::NUMERIC AS so2_calc,

        (
            CASE comuna
                WHEN 'Coronel'      THEN 66
                WHEN 'Hualpén'      THEN 62
                WHEN 'Concepción'   THEN 55
                WHEN 'Lota'         THEN 58
                WHEN 'Penco'        THEN 52
                WHEN 'Rancagua'     THEN 50
                WHEN 'Talca'        THEN 44
                WHEN 'Los Ángeles'  THEN 39
                WHEN 'Chillán'      THEN 38
                WHEN 'Curicó'       THEN 37
                ELSE 31
            END
            +
            CASE
                WHEN hora IN (6, 18) THEN 9
                ELSE 0
            END
            +
            CASE
                WHEN episodio_invierno > 0 THEN 5
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
            mp25_calc * 1.72
            +
            CASE
                WHEN comuna IN ('Coronel', 'Hualpén', 'Concepción', 'Lota', 'Penco') THEN 38
                WHEN comuna IN ('Los Ángeles', 'Chillán', 'San Carlos', 'Nacimiento', 'Linares', 'Parral', 'Cabrero') THEN 22
                WHEN comuna IN ('Rancagua', 'Talca', 'Curicó') THEN 18
                ELSE 12
            END
            +
            (dia_anio % 11)
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

-- Total de comunas cargadas
SELECT COUNT(*) AS total_comunas
FROM comunas;

-- Total de sensores cargados
SELECT COUNT(*) AS total_estaciones_sensores
FROM estaciones_sensores;

-- Total de industrias cargadas
SELECT COUNT(*) AS total_industrias_fuentes
FROM industrias_fuentes;

-- Total de mediciones cargadas
SELECT COUNT(*) AS total_monitoreo_ambiental
FROM monitoreo_ambiental;

-- Rango temporal disponible
SELECT
    MIN(fecha_hora) AS fecha_minima,
    MAX(fecha_hora) AS fecha_maxima
FROM monitoreo_ambiental;

-- Distribución ICAP aproximada según MP2.5 y MP10
SELECT
    CASE
        WHEN mp25 >= 170 OR mp10 >= 330 THEN 'Emergencia'
        WHEN mp25 >= 110 OR mp10 >= 230 THEN 'Preemergencia'
        WHEN mp25 >= 80  OR mp10 >= 180 THEN 'Alerta'
        WHEN mp25 >= 50  OR mp10 >= 130 THEN 'Regular'
        ELSE 'Buena'
    END AS categoria_icap,
    COUNT(*) AS cantidad_registros
FROM monitoreo_ambiental
GROUP BY categoria_icap
ORDER BY 1;

COMMIT;

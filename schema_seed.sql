-- ============================================================
-- CASO 3: MONITOREO CALIDAD DEL AIRE - ZONA CENTRO-SUR CHILE
-- PostgreSQL
-- Archivo sugerido: database/schema_seed.sql
-- ============================================================

DROP TABLE IF EXISTS monitoreo_ambiental CASCADE;
DROP TABLE IF EXISTS estaciones_sensores CASCADE;
DROP TABLE IF EXISTS industrias_fuentes CASCADE;
DROP TABLE IF EXISTS comunas CASCADE;

DROP TYPE IF EXISTS tipo_sensor_enum CASCADE;
DROP TYPE IF EXISTS region_enum CASCADE;
DROP TYPE IF EXISTS nivel_riesgo_enum CASCADE;

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE region_enum AS ENUM (
    'O''Higgins',
    'Maule',
    'Ñuble',
    'Biobío'
);

CREATE TYPE tipo_sensor_enum AS ENUM (
    'publico_oficial',
    'sensor_comunitario'
);

CREATE TYPE nivel_riesgo_enum AS ENUM (
    'bajo',
    'moderado',
    'critico'
);

-- ============================================================
-- TABLA: comunas
-- ============================================================

CREATE TABLE comunas (
    id_comuna SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    region region_enum NOT NULL,
    poblacion_estimada INTEGER NOT NULL CHECK (poblacion_estimada > 0),
    indice_vulnerabilidad_respiratoria NUMERIC(5,2) NOT NULL
        CHECK (indice_vulnerabilidad_respiratoria BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA: estaciones_sensores
-- ============================================================

CREATE TABLE estaciones_sensores (
    id_estacion SERIAL PRIMARY KEY,
    codigo_sensor VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(120) NOT NULL,
    tipo tipo_sensor_enum NOT NULL,
    latitud NUMERIC(9,6) NOT NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud NUMERIC(9,6) NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    id_comuna INTEGER NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_instalacion DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_estacion_comuna
        FOREIGN KEY (id_comuna)
        REFERENCES comunas(id_comuna)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- ============================================================
-- TABLA: industrias_fuentes
-- ============================================================

CREATE TABLE industrias_fuentes (
    id_industria SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    rubro_industrial VARCHAR(100) NOT NULL,
    latitud NUMERIC(9,6) NOT NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud NUMERIC(9,6) NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    id_comuna INTEGER NOT NULL,
    emision_maxima_permitida NUMERIC(10,2) NOT NULL
        CHECK (emision_maxima_permitida >= 0),
    unidad_emision VARCHAR(30) DEFAULT 'ton/año',
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_industria_comuna
        FOREIGN KEY (id_comuna)
        REFERENCES comunas(id_comuna)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- ============================================================
-- TABLA: monitoreo_ambiental
-- Serie temporal diaria/horaria
-- ============================================================

CREATE TABLE monitoreo_ambiental (
    id_monitoreo BIGSERIAL PRIMARY KEY,
    fecha_hora TIMESTAMP NOT NULL,
    id_estacion INTEGER NOT NULL,

    mp25 NUMERIC(8,2) NOT NULL CHECK (mp25 >= 0),
    mp10 NUMERIC(8,2) NOT NULL CHECK (mp10 >= 0),
    so2 NUMERIC(8,2) NOT NULL CHECK (so2 >= 0),
    no2 NUMERIC(8,2) NOT NULL CHECK (no2 >= 0),

    velocidad_viento NUMERIC(6,2) NOT NULL CHECK (velocidad_viento >= 0),
    direccion_viento_grados NUMERIC(6,2) NOT NULL
        CHECK (direccion_viento_grados BETWEEN 0 AND 360),

    temperatura NUMERIC(5,2) NOT NULL CHECK (temperatura BETWEEN -20 AND 50),
    humedad NUMERIC(5,2) NOT NULL CHECK (humedad BETWEEN 0 AND 100),

    fuente_dato VARCHAR(50) DEFAULT 'seed_simulado',
    nivel_riesgo nivel_riesgo_enum,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_monitoreo_estacion
        FOREIGN KEY (id_estacion)
        REFERENCES estaciones_sensores(id_estacion)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uq_monitoreo_estacion_fecha
        UNIQUE (id_estacion, fecha_hora)
);

-- ============================================================
-- FUNCIÓN: Clasificar nivel de riesgo por MP2.5
-- ============================================================

CREATE OR REPLACE FUNCTION calcular_nivel_riesgo(mp25_val NUMERIC)
RETURNS nivel_riesgo_enum AS $$
BEGIN
    IF mp25_val < 25 THEN
        RETURN 'bajo';
    ELSIF mp25_val < 50 THEN
        RETURN 'moderado';
    ELSE
        RETURN 'critico';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- TRIGGER: Asignar riesgo automáticamente
-- ============================================================

CREATE OR REPLACE FUNCTION trg_asignar_nivel_riesgo()
RETURNS TRIGGER AS $$
BEGIN
    NEW.nivel_riesgo := calcular_nivel_riesgo(NEW.mp25);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER before_insert_update_monitoreo_riesgo
BEFORE INSERT OR UPDATE ON monitoreo_ambiental
FOR EACH ROW
EXECUTE FUNCTION trg_asignar_nivel_riesgo();

-- ============================================================
-- ÍNDICES PARA API, DASHBOARD Y MODELOS
-- ============================================================

CREATE INDEX idx_comunas_region
ON comunas(region);

CREATE INDEX idx_estaciones_comuna
ON estaciones_sensores(id_comuna);

CREATE INDEX idx_industrias_comuna
ON industrias_fuentes(id_comuna);

CREATE INDEX idx_monitoreo_fecha
ON monitoreo_ambiental(fecha_hora);

CREATE INDEX idx_monitoreo_estacion
ON monitoreo_ambiental(id_estacion);

CREATE INDEX idx_monitoreo_riesgo
ON monitoreo_ambiental(nivel_riesgo);

CREATE INDEX idx_monitoreo_mp25
ON monitoreo_ambiental(mp25);

-- ============================================================
-- SEED: comunas
-- ============================================================

INSERT INTO comunas
(nombre, region, poblacion_estimada, indice_vulnerabilidad_respiratoria)
VALUES
('Rancagua', 'O''Higgins', 265000, 68.50),
('San Fernando', 'O''Higgins', 76000, 61.20),
('Talca', 'Maule', 236000, 72.40),
('Curicó', 'Maule', 165000, 69.80),
('Chillán', 'Ñuble', 184000, 75.30),
('San Carlos', 'Ñuble', 54000, 70.10),
('Concepción', 'Biobío', 230000, 66.70),
('Los Ángeles', 'Biobío', 215000, 78.90);

-- ============================================================
-- SEED: estaciones_sensores
-- ============================================================

INSERT INTO estaciones_sensores
(codigo_sensor, nombre, tipo, latitud, longitud, id_comuna, activo)
VALUES
('OH-RAN-001', 'Estación Centro Rancagua', 'publico_oficial', -34.170132, -70.740625, 1, TRUE),
('OH-RAN-002', 'Sensor Comunitario Norte Rancagua', 'sensor_comunitario', -34.150221, -70.728901, 1, TRUE),
('OH-SF-001', 'Estación San Fernando Centro', 'publico_oficial', -34.585860, -70.989190, 2, TRUE),

('MA-TAL-001', 'Estación Talca Centro', 'publico_oficial', -35.426400, -71.655420, 3, TRUE),
('MA-TAL-002', 'Sensor Comunitario Talca Sur', 'sensor_comunitario', -35.445812, -71.664231, 3, TRUE),
('MA-CUR-001', 'Estación Curicó Centro', 'publico_oficial', -34.982790, -71.239430, 4, TRUE),

('NB-CHI-001', 'Estación Chillán Centro', 'publico_oficial', -36.606640, -72.103440, 5, TRUE),
('NB-CHI-002', 'Sensor Comunitario Chillán Oriente', 'sensor_comunitario', -36.621110, -72.081230, 5, TRUE),
('NB-SC-001', 'Estación San Carlos Centro', 'publico_oficial', -36.424770, -71.958000, 6, TRUE),

('BB-CON-001', 'Estación Concepción Centro', 'publico_oficial', -36.826990, -73.049770, 7, TRUE),
('BB-CON-002', 'Sensor Comunitario Barrio Norte', 'sensor_comunitario', -36.805210, -73.062100, 7, TRUE),
('BB-LA-001', 'Estación Los Ángeles Centro', 'publico_oficial', -37.469730, -72.353660, 8, TRUE);

-- ============================================================
-- SEED: industrias_fuentes
-- ============================================================

INSERT INTO industrias_fuentes
(nombre, rubro_industrial, latitud, longitud, id_comuna, emision_maxima_permitida)
VALUES
('Planta Industrial Rancagua Norte', 'Procesamiento industrial', -34.145000, -70.735000, 1, 1200.00),
('Complejo Energético San Fernando', 'Termoeléctrica', -34.590000, -70.970000, 2, 1800.00),
('Celulosa Maule Talca', 'Celulosa', -35.410000, -71.670000, 3, 2500.00),
('Agroindustria Curicó Sur', 'Agroindustria', -35.000000, -71.250000, 4, 950.00),
('Fundición Ñuble', 'Fundición', -36.600000, -72.090000, 5, 2100.00),
('Planta Maderera San Carlos', 'Maderera', -36.430000, -71.940000, 6, 870.00),
('Complejo Industrial Concepción', 'Industrial químico', -36.815000, -73.070000, 7, 2300.00),
('Planta Biomasa Los Ángeles', 'Energía biomasa', -37.455000, -72.370000, 8, 1600.00);

-- ============================================================
-- SEED: monitoreo_ambiental
-- Datos simulados por 30 días cada 6 horas por estación
-- ============================================================

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
    humedad,
    fuente_dato
)
SELECT
    fecha.fecha_hora,
    est.id_estacion,

    ROUND((
        CASE
            WHEN c.region IN ('Ñuble', 'Biobío') THEN 35
            WHEN c.region = 'Maule' THEN 28
            ELSE 24
        END
        + RANDOM() * 35
        + CASE
            WHEN EXTRACT(HOUR FROM fecha.fecha_hora) IN (0, 6) THEN 12
            ELSE 0
          END
    )::NUMERIC, 2) AS mp25,

    ROUND((
        CASE
            WHEN c.region IN ('Ñuble', 'Biobío') THEN 55
            WHEN c.region = 'Maule' THEN 45
            ELSE 38
        END
        + RANDOM() * 50
    )::NUMERIC, 2) AS mp10,

    ROUND((5 + RANDOM() * 30)::NUMERIC, 2) AS so2,
    ROUND((8 + RANDOM() * 45)::NUMERIC, 2) AS no2,

    ROUND((0.5 + RANDOM() * 18)::NUMERIC, 2) AS velocidad_viento,
    ROUND((RANDOM() * 360)::NUMERIC, 2) AS direccion_viento_grados,

    ROUND((5 + RANDOM() * 25)::NUMERIC, 2) AS temperatura,
    ROUND((45 + RANDOM() * 50)::NUMERIC, 2) AS humedad,

    'seed_simulado'
FROM estaciones_sensores est
JOIN comunas c ON c.id_comuna = est.id_comuna
CROSS JOIN generate_series(
    NOW() - INTERVAL '30 days',
    NOW(),
    INTERVAL '6 hours'
) AS fecha(fecha_hora);

-- ============================================================
-- VISTA: monitoreo completo para API, dashboard y EDA
-- ============================================================

CREATE OR REPLACE VIEW vw_monitoreo_detalle AS
SELECT
    m.id_monitoreo,
    m.fecha_hora,
    c.nombre AS comuna,
    c.region,
    c.poblacion_estimada,
    c.indice_vulnerabilidad_respiratoria,
    e.codigo_sensor,
    e.nombre AS estacion,
    e.tipo AS tipo_sensor,
    e.latitud,
    e.longitud,
    m.mp25,
    m.mp10,
    m.so2,
    m.no2,
    m.velocidad_viento,
    m.direccion_viento_grados,
    m.temperatura,
    m.humedad,
    m.nivel_riesgo,
    m.fuente_dato
FROM monitoreo_ambiental m
JOIN estaciones_sensores e ON e.id_estacion = m.id_estacion
JOIN comunas c ON c.id_comuna = e.id_comuna;

-- ============================================================
-- VISTA: resumen por comuna
-- Útil para dashboard ejecutivo
-- ============================================================

CREATE OR REPLACE VIEW vw_resumen_comuna AS
SELECT
    comuna,
    region,
    COUNT(*) AS total_mediciones,
    ROUND(AVG(mp25), 2) AS promedio_mp25,
    ROUND(MAX(mp25), 2) AS maximo_mp25,
    ROUND(AVG(mp10), 2) AS promedio_mp10,
    ROUND(AVG(temperatura), 2) AS promedio_temperatura,
    ROUND(AVG(humedad), 2) AS promedio_humedad,
    ROUND(AVG(velocidad_viento), 2) AS promedio_viento,
    COUNT(*) FILTER (WHERE nivel_riesgo = 'critico') AS dias_o_periodos_criticos
FROM vw_monitoreo_detalle
GROUP BY comuna, region;

-- ============================================================
-- VISTA: dataset para Machine Learning
-- Útil para clustering y regresión
-- ============================================================

CREATE OR REPLACE VIEW vw_dataset_ml AS
SELECT
    id_monitoreo,
    EXTRACT(HOUR FROM fecha_hora) AS hora,
    EXTRACT(DOW FROM fecha_hora) AS dia_semana,
    comuna,
    region,
    codigo_sensor,
    mp25,
    mp10,
    so2,
    no2,
    velocidad_viento,
    direccion_viento_grados,
    temperatura,
    humedad,
    indice_vulnerabilidad_respiratoria,
    nivel_riesgo
FROM vw_monitoreo_detalle;

-- ============================================================
-- VISTA: industrias cercanas por comuna
-- Útil para análisis de fuentes contaminantes
-- ============================================================

CREATE OR REPLACE VIEW vw_industrias_por_comuna AS
SELECT
    c.nombre AS comuna,
    c.region,
    i.nombre AS industria,
    i.rubro_industrial,
    i.emision_maxima_permitida,
    i.unidad_emision,
    i.activa
FROM industrias_fuentes i
JOIN comunas c ON c.id_comuna = i.id_comuna;

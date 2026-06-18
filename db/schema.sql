-- ============================================================
-- BASE DE DATOS: Monitoreo de Calidad del Aire
-- PostgreSQL
-- Caso: Monitoreo calidad del aire zona centro-sur de Chile
--
-- Versión alineada al caso:
-- - Solo 4 tablas principales solicitadas.
-- - Sin seed.
-- - Sin funciones.
-- - Sin triggers.
-- - Sin vistas.
-- - Con PK, FK, UK, ENUMS y restricciones normales.
-- ============================================================


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
    'sensor_comunitario_ong'
);


-- ============================================================
-- TABLA: comunas
--
-- Almacena los municipios participantes, región,
-- población estimada y vulnerabilidad respiratoria.
--
-- Nota:
-- El índice de vulnerabilidad respiratoria se modela como un
-- valor entre 0 y 100, donde valores mayores representan mayor
-- vulnerabilidad de la población frente a episodios de contaminación.
-- ============================================================

CREATE TABLE comunas (
    id_comuna SERIAL,
    nombre VARCHAR(100) NOT NULL,
    region region_enum NOT NULL,
    poblacion_estimada INTEGER NOT NULL,
    indice_vulnerabilidad_respiratoria NUMERIC(5,2) NOT NULL,

    CONSTRAINT pk_comunas
        PRIMARY KEY (id_comuna),

    CONSTRAINT uk_comunas_nombre
        UNIQUE (nombre),

    CONSTRAINT chk_comunas_poblacion_estimada
        CHECK (poblacion_estimada > 0),

    CONSTRAINT chk_comunas_indice_vulnerabilidad_respiratoria
        CHECK (
            indice_vulnerabilidad_respiratoria >= 0
            AND indice_vulnerabilidad_respiratoria <= 100
        )
);


-- ============================================================
-- TABLA: estaciones_sensores
--
-- Registra los puntos de monitoreo o sensores IoT instalados.
--
-- Campos solicitados por el caso:
-- - código único
-- - tipo de sensor
-- - coordenadas geográficas
-- - comuna donde se ubica
--
-- Restricciones normales:
-- - latitud entre -90 y 90
-- - longitud entre -180 y 180
-- ============================================================

CREATE TABLE estaciones_sensores (
    id_estacion SERIAL,
    codigo_unico VARCHAR(50) NOT NULL,
    tipo tipo_sensor_enum NOT NULL,
    latitud NUMERIC(9,6) NOT NULL,
    longitud NUMERIC(9,6) NOT NULL,
    id_comuna INTEGER NOT NULL,

    CONSTRAINT pk_estaciones_sensores
        PRIMARY KEY (id_estacion),

    CONSTRAINT uk_estaciones_sensores_codigo_unico
        UNIQUE (codigo_unico),

    CONSTRAINT fk_estaciones_sensores_comunas
        FOREIGN KEY (id_comuna)
        REFERENCES comunas(id_comuna),

    CONSTRAINT chk_estaciones_sensores_latitud
        CHECK (latitud >= -90 AND latitud <= 90),

    CONSTRAINT chk_estaciones_sensores_longitud
        CHECK (longitud >= -180 AND longitud <= 180)
);


-- ============================================================
-- TABLA: industrias_fuentes
--
-- Detalla las principales fuentes fijas de contaminación
-- autorizadas en la zona.
--
-- Campos solicitados por el caso:
-- - nombre de la fuente industrial
-- - rubro industrial
-- - nivel de emisión máxima permitida
-- - comuna asociada
--
-- Nota:
-- La emisión máxima permitida se restringe a valores mayores
-- o iguales a cero, porque representa un límite técnico/ambiental.
-- ============================================================

CREATE TABLE industrias_fuentes (
    id_industria SERIAL,
    nombre VARCHAR(150) NOT NULL,
    rubro_industrial VARCHAR(100) NOT NULL,
    emision_maxima_permitida NUMERIC(10,2) NOT NULL,
    id_comuna INTEGER NOT NULL,

    CONSTRAINT pk_industrias_fuentes
        PRIMARY KEY (id_industria),

    CONSTRAINT uk_industrias_fuentes_nombre
        UNIQUE (nombre),

    CONSTRAINT fk_industrias_fuentes_comunas
        FOREIGN KEY (id_comuna)
        REFERENCES comunas(id_comuna),

    CONSTRAINT chk_industrias_fuentes_emision_maxima_permitida
        CHECK (emision_maxima_permitida >= 0)
);


-- ============================================================
-- TABLA: monitoreo_ambiental
--
-- Tabla transaccional de serie temporal.
-- Registra diariamente las métricas ambientales capturadas por
-- cada estación o sensor.
--
-- Campos solicitados por el caso:
-- - fecha/hora
-- - estación/sensor
-- - MP2.5
-- - MP10
-- - SO2
-- - NO2
-- - velocidad del viento
-- - dirección del viento
-- - temperatura
-- - humedad ambiental
--
-- Unidades recomendadas para interpretar los datos:
-- - mp25: microgramos por metro cúbico, µg/m3
-- - mp10: microgramos por metro cúbico, µg/m3
-- - so2: microgramos por metro cúbico normal, µg/m3N
-- - no2: microgramos por metro cúbico normal, µg/m3N
-- - velocidad_viento: metros por segundo, m/s
-- - direccion_viento_grados: grados, entre 0 y 360
-- - temperatura: grados Celsius, °C
-- - humedad: porcentaje, %
--
-- Umbrales de referencia sobre salud/calidad del aire:
--
-- MP2.5:
-- - Referencia Chile D.S. 12/2011:
--   20 µg/m3 promedio anual.
--   50 µg/m3 promedio de 24 horas.
-- - Es relevante para salud porque las partículas finas pueden
--   ingresar profundamente al sistema respiratorio.
--
-- MP10:
-- - Referencia Chile D.S. 12/2021:
--   50 µg/m3N promedio anual.
--   130 µg/m3N promedio de 24 horas.
--
-- SO2:
-- - Referencia Chile D.S. 104/2018:
--   150 µg/m3N promedio de 24 horas.
--   350 µg/m3N promedio de 1 hora.
--
-- NO2:
-- - Referencia Chile D.S. 40/2023:
--   40 µg/m3N promedio anual.
--   100 µg/m3N promedio de 24 horas.
--
-- Viento:
-- - La velocidad del viento ayuda a analizar dispersión de contaminantes.
-- - La dirección del viento ayuda a relacionar contaminación con fuentes
--   industriales cercanas.
--
-- Humedad y temperatura:
-- - No son contaminantes por sí mismas en esta tabla.
-- - Se registran porque influyen en la concentración, dispersión y
--   comportamiento del material particulado.
-- ============================================================

CREATE TABLE monitoreo_ambiental (
    id_monitoreo SERIAL,
    fecha_hora TIMESTAMP NOT NULL,
    id_estacion INTEGER NOT NULL,
    mp25 NUMERIC(8,2) NOT NULL,
    mp10 NUMERIC(8,2) NOT NULL,
    so2 NUMERIC(8,2) NOT NULL,
    no2 NUMERIC(8,2) NOT NULL,
    velocidad_viento NUMERIC(6,2) NOT NULL,
    direccion_viento_grados NUMERIC(5,2) NOT NULL,
    temperatura NUMERIC(5,2) NOT NULL,
    humedad NUMERIC(5,2) NOT NULL,

    CONSTRAINT pk_monitoreo_ambiental
        PRIMARY KEY (id_monitoreo),

    CONSTRAINT fk_monitoreo_ambiental_estaciones_sensores
        FOREIGN KEY (id_estacion)
        REFERENCES estaciones_sensores(id_estacion),

    CONSTRAINT uk_monitoreo_ambiental_estacion_fecha
        UNIQUE (id_estacion, fecha_hora),

    CONSTRAINT chk_monitoreo_ambiental_mp25
        CHECK (mp25 >= 0),

    CONSTRAINT chk_monitoreo_ambiental_mp10
        CHECK (mp10 >= 0),

    CONSTRAINT chk_monitoreo_ambiental_so2
        CHECK (so2 >= 0),

    CONSTRAINT chk_monitoreo_ambiental_no2
        CHECK (no2 >= 0),

    CONSTRAINT chk_monitoreo_ambiental_velocidad_viento
        CHECK (velocidad_viento >= 0),

    CONSTRAINT chk_monitoreo_ambiental_direccion_viento
        CHECK (
            direccion_viento_grados >= 0
            AND direccion_viento_grados <= 360
        ),

    CONSTRAINT chk_monitoreo_ambiental_temperatura
        CHECK (temperatura >= -50 AND temperatura <= 60),

    CONSTRAINT chk_monitoreo_ambiental_humedad
        CHECK (humedad >= 0 AND humedad <= 100)
);
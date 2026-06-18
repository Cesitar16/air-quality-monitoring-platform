# 02 - Diccionario de Datos

## Proyecto

**Sistema de Monitoreo de Calidad del Aire para la Zona Centro-Sur de Chile**

Este documento describe el diccionario de datos del modelo relacional utilizado en el proyecto. Su objetivo es documentar de forma clara las tablas, columnas, tipos de datos, claves, restricciones, unidades de medida y significado de cada campo utilizado en la base de datos.

El modelo se mantiene alineado al caso de negocio, considerando las cuatro tablas principales solicitadas:

- `comunas`
- `estaciones_sensores`
- `industrias_fuentes`
- `monitoreo_ambiental`

---

## 1. Convenciones generales

### 1.1 Motor de base de datos

El modelo está diseñado para:

```text
PostgreSQL
```

### 1.2 Nomenclatura

Se utiliza nomenclatura en español y estilo `snake_case`.

Ejemplos:

```text
id_comuna
codigo_unico
fecha_hora
velocidad_viento
direccion_viento_grados
```

### 1.3 Tipos de claves

| Abreviatura | Significado |
|---|---|
| PK | Primary Key / Clave primaria |
| FK | Foreign Key / Clave foránea |
| UK | Unique Key / Valor único |
| NN | Not Null / Campo obligatorio |

### 1.4 Reglas generales

- Cada tabla posee una clave primaria.
- Las relaciones entre tablas se realizan mediante claves foráneas.
- Los campos principales del negocio son obligatorios.
- Las mediciones ambientales se registran en una tabla transaccional de serie temporal.
- El ICAP/ICA no se almacena como campo base, porque es una métrica derivada calculada desde los contaminantes.

---

# 2. Tipos ENUM

## 2.1 `region_enum`

Define las regiones consideradas en el caso de negocio.

| Valor permitido | Descripción |
|---|---|
| `O'Higgins` | Región del Libertador General Bernardo O'Higgins |
| `Maule` | Región del Maule |
| `Ñuble` | Región de Ñuble |
| `Biobío` | Región del Biobío |

### Uso

Este ENUM se utiliza en la tabla:

```text
comunas.region
```

---

## 2.2 `tipo_sensor_enum`

Define el tipo de estación o sensor registrado en el sistema.

| Valor permitido | Descripción |
|---|---|
| `publico_oficial` | Estación oficial del Estado o red pública |
| `sensor_comunitario_ong` | Sensor comunitario o IoT gestionado por la ONG |

### Uso

Este ENUM se utiliza en la tabla:

```text
estaciones_sensores.tipo
```

---

# 3. Tabla `comunas`

## 3.1 Descripción

La tabla `comunas` almacena los municipios participantes del sistema de monitoreo ambiental.

Incluye información territorial, población estimada y una variable resumida de vulnerabilidad en salud respiratoria.

---

## 3.2 Estructura de campos

| Campo | Tipo de dato | Clave | Nulo | Descripción |
|---|---|---|---|---|
| `id_comuna` | `SERIAL` | PK | No | Identificador único de la comuna |
| `nombre` | `VARCHAR(100)` | UK | No | Nombre de la comuna participante |
| `region` | `region_enum` | - | No | Región a la que pertenece la comuna |
| `poblacion_estimada` | `INTEGER` | - | No | Población aproximada de la comuna |
| `indice_vulnerabilidad_respiratoria` | `NUMERIC(5,2)` | - | No | Índice comunal de vulnerabilidad respiratoria |

---

## 3.3 Detalle de variables

### `id_comuna`

Identificador interno de cada comuna.

- Tipo: `SERIAL`
- Clave primaria: Sí
- Uso: relacionar comunas con sensores e industrias.

Ejemplo:

```text
1
2
3
```

---

### `nombre`

Nombre oficial o referencial de la comuna.

- Tipo: `VARCHAR(100)`
- Restricción: único.
- Uso: identificar territorialmente los datos.

Ejemplo:

```text
Chillán
Talca
Concepción
Rancagua
```

---

### `region`

Región administrativa donde se ubica la comuna.

- Tipo: `region_enum`
- Valores permitidos:
  - `O'Higgins`
  - `Maule`
  - `Ñuble`
  - `Biobío`

Ejemplo:

```text
Ñuble
Biobío
```

---

### `poblacion_estimada`

Cantidad aproximada de habitantes de la comuna.

- Tipo: `INTEGER`
- Restricción recomendada: mayor que cero.
- Uso analítico: permite ponderar exposición de población ante episodios de contaminación.

Ejemplo:

```text
198624
250000
```

---

### `indice_vulnerabilidad_respiratoria`

Indicador resumido de vulnerabilidad respiratoria de la comuna.

- Tipo: `NUMERIC(5,2)`
- Escala propuesta: 0 a 100.
- Interpretación:
  - Valores bajos: menor vulnerabilidad respiratoria.
  - Valores altos: mayor vulnerabilidad respiratoria.
- No corresponde al ICAP.
- No corresponde a concentración de contaminantes.

Ejemplo:

```text
35.50
72.80
91.20
```

---

## 3.4 Restricciones

| Restricción | Campo | Descripción |
|---|---|---|
| `pk_comunas` | `id_comuna` | Identifica de forma única cada comuna |
| `uk_comunas_nombre` | `nombre` | Evita repetir comunas |
| `chk_comunas_poblacion_estimada` | `poblacion_estimada` | Valida población mayor que cero |
| `chk_comunas_indice_vulnerabilidad_respiratoria` | `indice_vulnerabilidad_respiratoria` | Valida índice entre 0 y 100 |

---

# 4. Tabla `estaciones_sensores`

## 4.1 Descripción

La tabla `estaciones_sensores` registra los puntos de monitoreo ambiental instalados en las comunas.

Puede contener estaciones oficiales o sensores comunitarios de bajo costo administrados por la ONG.

Cada sensor pertenece a una comuna.

---

## 4.2 Estructura de campos

| Campo | Tipo de dato | Clave | Nulo | Descripción |
|---|---|---|---|---|
| `id_estacion` | `SERIAL` | PK | No | Identificador único de la estación o sensor |
| `codigo_unico` | `VARCHAR(50)` | UK | No | Código único del dispositivo |
| `tipo` | `tipo_sensor_enum` | - | No | Tipo de estación o sensor |
| `latitud` | `NUMERIC(9,6)` | - | No | Coordenada geográfica de latitud |
| `longitud` | `NUMERIC(9,6)` | - | No | Coordenada geográfica de longitud |
| `id_comuna` | `INTEGER` | FK | No | Comuna donde se ubica la estación o sensor |

---

## 4.3 Detalle de variables

### `id_estacion`

Identificador interno de cada estación o sensor.

- Tipo: `SERIAL`
- Clave primaria: Sí
- Uso: relacionar cada medición ambiental con el sensor que la produjo.

Ejemplo:

```text
1
2
3
```

---

### `codigo_unico`

Código único asignado a la estación o sensor.

- Tipo: `VARCHAR(50)`
- Restricción: único.
- Uso: identificar dispositivos físicos o fuentes de monitoreo.

Ejemplo:

```text
SEN-NUBLE-001
SEN-BIOBIO-004
EST-MAULE-002
```

---

### `tipo`

Tipo de estación o sensor.

- Tipo: `tipo_sensor_enum`
- Valores permitidos:
  - `publico_oficial`
  - `sensor_comunitario_ong`

Ejemplo:

```text
publico_oficial
sensor_comunitario_ong
```

---

### `latitud`

Coordenada geográfica de latitud.

- Tipo: `NUMERIC(9,6)`
- Rango recomendado: -90 a 90.
- Uso analítico: ubicación espacial del sensor.

Ejemplo:

```text
-36.606640
-33.448890
```

---

### `longitud`

Coordenada geográfica de longitud.

- Tipo: `NUMERIC(9,6)`
- Rango recomendado: -180 a 180.
- Uso analítico: ubicación espacial del sensor.

Ejemplo:

```text
-72.103440
-70.669270
```

---

### `id_comuna`

Identificador de la comuna donde se ubica el sensor.

- Tipo: `INTEGER`
- Clave foránea: `comunas(id_comuna)`
- Uso: permite agrupar mediciones por comuna.

Ejemplo:

```text
1
4
7
```

---

## 4.4 Restricciones

| Restricción | Campo | Descripción |
|---|---|---|
| `pk_estaciones_sensores` | `id_estacion` | Identifica de forma única cada estación |
| `uk_estaciones_sensores_codigo_unico` | `codigo_unico` | Evita códigos de sensor repetidos |
| `fk_estaciones_sensores_comunas` | `id_comuna` | Relaciona el sensor con una comuna |
| `chk_estaciones_sensores_latitud` | `latitud` | Valida rango geográfico de latitud |
| `chk_estaciones_sensores_longitud` | `longitud` | Valida rango geográfico de longitud |

---

# 5. Tabla `industrias_fuentes`

## 5.1 Descripción

La tabla `industrias_fuentes` registra las principales fuentes fijas de contaminación autorizadas en la zona de estudio.

Ejemplos de fuentes:

- Termoeléctricas
- Celulosas
- Fundiciones
- Plantas industriales
- Otras fuentes fijas relevantes

Cada industria se asocia a una comuna.

---

## 5.2 Estructura de campos

| Campo | Tipo de dato | Clave | Nulo | Descripción |
|---|---|---|---|---|
| `id_industria` | `SERIAL` | PK | No | Identificador único de la industria |
| `nombre` | `VARCHAR(150)` | UK | No | Nombre de la fuente industrial |
| `rubro_industrial` | `VARCHAR(100)` | - | No | Rubro o actividad industrial |
| `emision_maxima_permitida` | `NUMERIC(10,2)` | - | No | Nivel máximo de emisión permitido |
| `id_comuna` | `INTEGER` | FK | No | Comuna donde se ubica la fuente industrial |

---

## 5.3 Detalle de variables

### `id_industria`

Identificador interno de la fuente industrial.

- Tipo: `SERIAL`
- Clave primaria: Sí
- Uso: diferenciar cada industria registrada.

Ejemplo:

```text
1
2
3
```

---

### `nombre`

Nombre de la industria o fuente fija de contaminación.

- Tipo: `VARCHAR(150)`
- Restricción: único.
- Uso: identificar la fuente emisora.

Ejemplo:

```text
Planta Celulosa Biobío
Termoeléctrica Centro Sur
Fundición Industrial Maule
```

---

### `rubro_industrial`

Rubro o actividad económica de la fuente contaminante.

- Tipo: `VARCHAR(100)`
- Uso analítico: permite agrupar industrias según tipo de actividad.

Ejemplo:

```text
Celulosa
Termoeléctrica
Fundición
Manufactura
```

---

### `emision_maxima_permitida`

Nivel máximo de emisión autorizado para la industria.

- Tipo: `NUMERIC(10,2)`
- Restricción recomendada: mayor o igual a cero.
- Uso: representar el límite ambiental permitido para la fuente industrial.
- Nota: este campo no reemplaza un historial real de emisiones, pero permite representar el límite autorizado solicitado en el caso.

Ejemplo:

```text
120.50
300.00
80.75
```

---

### `id_comuna`

Identificador de la comuna donde se ubica la fuente industrial.

- Tipo: `INTEGER`
- Clave foránea: `comunas(id_comuna)`
- Uso: relacionar fuentes industriales con territorios comunales.

Ejemplo:

```text
2
5
8
```

---

## 5.4 Restricciones

| Restricción | Campo | Descripción |
|---|---|---|
| `pk_industrias_fuentes` | `id_industria` | Identifica de forma única cada fuente industrial |
| `uk_industrias_fuentes_nombre` | `nombre` | Evita nombres de industrias repetidos |
| `fk_industrias_fuentes_comunas` | `id_comuna` | Relaciona la industria con una comuna |
| `chk_industrias_fuentes_emision_maxima_permitida` | `emision_maxima_permitida` | Evita valores negativos de emisión permitida |

---

# 6. Tabla `monitoreo_ambiental`

## 6.1 Descripción

La tabla `monitoreo_ambiental` es la tabla transaccional del sistema.

Registra mediciones ambientales de forma temporal, asociadas a una estación o sensor específico.

Es la tabla principal para:

- análisis de series temporales;
- dashboards ambientales;
- cálculo de ICAP;
- análisis exploratorio;
- clustering de días o zonas críticas;
- modelos predictivos de MP2.5.

---

## 6.2 Estructura de campos

| Campo | Tipo de dato | Clave | Nulo | Descripción |
|---|---|---|---|---|
| `id_monitoreo` | `SERIAL` | PK | No | Identificador único del registro de monitoreo |
| `fecha_hora` | `TIMESTAMP` | UK compuesta | No | Fecha y hora de la medición |
| `id_estacion` | `INTEGER` | FK / UK compuesta | No | Estación o sensor que registra la medición |
| `mp25` | `NUMERIC(8,2)` | - | No | Concentración de material particulado fino MP2.5 |
| `mp10` | `NUMERIC(8,2)` | - | No | Concentración de material particulado respirable MP10 |
| `so2` | `NUMERIC(8,2)` | - | No | Concentración de dióxido de azufre |
| `no2` | `NUMERIC(8,2)` | - | No | Concentración de dióxido de nitrógeno |
| `velocidad_viento` | `NUMERIC(6,2)` | - | No | Velocidad del viento |
| `direccion_viento_grados` | `NUMERIC(5,2)` | - | No | Dirección del viento en grados |
| `temperatura` | `NUMERIC(5,2)` | - | No | Temperatura ambiental |
| `humedad` | `NUMERIC(5,2)` | - | No | Humedad ambiental |

---

## 6.3 Detalle de variables

### `id_monitoreo`

Identificador interno de cada medición ambiental.

- Tipo: `SERIAL`
- Clave primaria: Sí
- Uso: identificar de manera única cada registro de serie temporal.

Ejemplo:

```text
1
2
3
```

---

### `fecha_hora`

Fecha y hora en que se registró la medición ambiental.

- Tipo: `TIMESTAMP`
- Uso: análisis temporal, agrupación diaria, horaria, semanal o mensual.
- Forma parte de una restricción única junto con `id_estacion`.

Ejemplo:

```text
2026-06-01 08:00:00
2026-06-01 14:00:00
2026-06-02 00:00:00
```

---

### `id_estacion`

Identificador de la estación o sensor que generó la medición.

- Tipo: `INTEGER`
- Clave foránea: `estaciones_sensores(id_estacion)`
- Uso: asociar cada medición a un punto geográfico.

Ejemplo:

```text
1
2
7
```

---

### `mp25`

Concentración de material particulado fino MP2.5.

- Tipo: `NUMERIC(8,2)`
- Unidad recomendada: `µg/m³`
- Restricción recomendada: mayor o igual a cero.
- Uso:
  - cálculo de ICAP;
  - análisis de calidad del aire;
  - modelos predictivos;
  - detección de episodios críticos.

Ejemplo:

```text
12.50
48.90
91.00
125.30
```

---

### `mp10`

Concentración de material particulado respirable MP10.

- Tipo: `NUMERIC(8,2)`
- Unidad recomendada: `µg/m³`
- Restricción recomendada: mayor o igual a cero.
- Uso:
  - cálculo de ICAP;
  - análisis de contaminación por partículas;
  - comparación con MP2.5;
  - detección de episodios críticos.

Ejemplo:

```text
60.00
130.50
180.00
230.20
```

---

### `so2`

Concentración de dióxido de azufre.

- Tipo: `NUMERIC(8,2)`
- Unidad recomendada: `µg/m³N`
- Restricción recomendada: mayor o igual a cero.
- Uso:
  - análisis complementario de contaminación industrial;
  - detección de episodios asociados a combustión;
  - variable explicativa para modelos predictivos.

Ejemplo:

```text
15.30
80.00
150.20
```

---

### `no2`

Concentración de dióxido de nitrógeno.

- Tipo: `NUMERIC(8,2)`
- Unidad recomendada: `µg/m³N`
- Restricción recomendada: mayor o igual a cero.
- Uso:
  - análisis complementario de contaminación por combustión;
  - relación con actividad industrial o vehicular;
  - variable explicativa para modelos predictivos.

Ejemplo:

```text
18.50
45.00
100.00
```

---

### `velocidad_viento`

Velocidad del viento al momento de la medición.

- Tipo: `NUMERIC(6,2)`
- Unidad recomendada: `m/s`
- Restricción recomendada: mayor o igual a cero.
- Uso:
  - analizar dispersión de contaminantes;
  - identificar condiciones de baja ventilación;
  - explicar acumulación de MP2.5 y MP10;
  - alimentar modelos predictivos.

Ejemplo:

```text
0.80
2.50
5.30
```

---

### `direccion_viento_grados`

Dirección del viento registrada en grados.

- Tipo: `NUMERIC(5,2)`
- Unidad recomendada: grados.
- Rango recomendado: 0 a 360.
- Uso:
  - analizar procedencia o transporte de contaminantes;
  - relacionar contaminación con industrias cercanas;
  - graficar patrones de viento.

Ejemplo:

```text
0.00
90.00
180.00
270.00
360.00
```

Referencia general:

| Grados | Dirección |
|---:|---|
| 0 / 360 | Norte |
| 90 | Este |
| 180 | Sur |
| 270 | Oeste |

---

### `temperatura`

Temperatura ambiental al momento de la medición.

- Tipo: `NUMERIC(5,2)`
- Unidad recomendada: grados Celsius, `°C`.
- Rango operativo recomendado para validación: -50 a 60.
- Uso:
  - análisis meteorológico;
  - relación con calefacción residencial;
  - predicción de MP2.5;
  - identificación de condiciones estacionales.

Ejemplo:

```text
3.50
12.80
25.20
```

---

### `humedad`

Humedad relativa ambiental.

- Tipo: `NUMERIC(5,2)`
- Unidad recomendada: porcentaje, `%`.
- Rango recomendado: 0 a 100.
- Uso:
  - análisis meteorológico;
  - interpretación del comportamiento de partículas;
  - complemento para modelos predictivos.

Ejemplo:

```text
45.00
72.30
95.50
```

---

## 6.4 Restricciones

| Restricción | Campo | Descripción |
|---|---|---|
| `pk_monitoreo_ambiental` | `id_monitoreo` | Identifica de forma única cada medición |
| `fk_monitoreo_ambiental_estaciones_sensores` | `id_estacion` | Relaciona la medición con un sensor |
| `uk_monitoreo_ambiental_estacion_fecha` | `id_estacion`, `fecha_hora` | Evita dos mediciones duplicadas para el mismo sensor y momento |
| `chk_monitoreo_ambiental_mp25` | `mp25` | Evita valores negativos |
| `chk_monitoreo_ambiental_mp10` | `mp10` | Evita valores negativos |
| `chk_monitoreo_ambiental_so2` | `so2` | Evita valores negativos |
| `chk_monitoreo_ambiental_no2` | `no2` | Evita valores negativos |
| `chk_monitoreo_ambiental_velocidad_viento` | `velocidad_viento` | Evita velocidades negativas |
| `chk_monitoreo_ambiental_direccion_viento` | `direccion_viento_grados` | Valida dirección entre 0 y 360 grados |
| `chk_monitoreo_ambiental_temperatura` | `temperatura` | Valida rango operativo de temperatura |
| `chk_monitoreo_ambiental_humedad` | `humedad` | Valida humedad entre 0 y 100 |

---

# 7. Relaciones entre tablas

## 7.1 Relación `comunas` → `estaciones_sensores`

Una comuna puede tener muchas estaciones o sensores.

```text
comunas.id_comuna 1 ─── N estaciones_sensores.id_comuna
```

Ejemplo:

```text
Comuna: Chillán
Sensores: SEN-NUBLE-001, SEN-NUBLE-002, SEN-NUBLE-003
```

---

## 7.2 Relación `comunas` → `industrias_fuentes`

Una comuna puede tener muchas fuentes industriales registradas.

```text
comunas.id_comuna 1 ─── N industrias_fuentes.id_comuna
```

Ejemplo:

```text
Comuna: Concepción
Industrias: Planta Industrial A, Termoeléctrica B
```

---

## 7.3 Relación `estaciones_sensores` → `monitoreo_ambiental`

Una estación o sensor puede generar muchas mediciones ambientales a lo largo del tiempo.

```text
estaciones_sensores.id_estacion 1 ─── N monitoreo_ambiental.id_estacion
```

Ejemplo:

```text
Sensor: SEN-BIOBIO-001
Mediciones:
- 2026-06-01 08:00:00
- 2026-06-01 14:00:00
- 2026-06-01 20:00:00
```

---

# 8. Métricas derivadas

Las siguientes métricas no forman parte obligatoria de las tablas base, pero pueden calcularse en SQL, Python, backend o dashboard.

---

## 8.1 ICAP / ICA

El ICAP es una métrica derivada calculada principalmente desde:

```text
MP2.5
MP10
```

No se recomienda almacenarlo directamente como campo base porque puede recalcularse a partir de las mediciones.

Ejemplo de cálculo SQL:

```sql
SELECT
    id_monitoreo,
    fecha_hora,
    id_estacion,
    mp25,
    mp10,
    CASE
        WHEN mp25 >= 170 OR mp10 >= 330 THEN 'Emergencia'
        WHEN mp25 >= 110 OR mp10 >= 230 THEN 'Preemergencia'
        WHEN mp25 >= 80  OR mp10 >= 180 THEN 'Alerta'
        WHEN mp25 >= 50  OR mp10 >= 130 THEN 'Regular'
        ELSE 'Buena'
    END AS categoria_icap
FROM monitoreo_ambiental;
```

---

## 8.2 Promedio diario de MP2.5

Métrica útil para dashboards y modelos predictivos.

```sql
SELECT
    DATE(fecha_hora) AS fecha,
    id_estacion,
    AVG(mp25) AS promedio_diario_mp25
FROM monitoreo_ambiental
GROUP BY DATE(fecha_hora), id_estacion;
```

---

## 8.3 Máximo diario de MP2.5

Métrica útil para detectar episodios críticos.

```sql
SELECT
    DATE(fecha_hora) AS fecha,
    id_estacion,
    MAX(mp25) AS maximo_diario_mp25
FROM monitoreo_ambiental
GROUP BY DATE(fecha_hora), id_estacion;
```

---

# 9. Uso de variables en Ciencia de Datos

## 9.1 Variables para EDA

| Variable | Uso |
|---|---|
| `fecha_hora` | Patrones temporales |
| `id_estacion` | Comparación entre sensores |
| `mp25` | Principal contaminante para análisis |
| `mp10` | Contaminación por partículas respirables |
| `so2` | Análisis de fuentes industriales |
| `no2` | Análisis de combustión |
| `velocidad_viento` | Dispersión o acumulación |
| `direccion_viento_grados` | Relación con fuentes industriales |
| `temperatura` | Contexto meteorológico |
| `humedad` | Contexto meteorológico |
| `id_comuna` | Agrupación territorial |
| `indice_vulnerabilidad_respiratoria` | Priorización por salud pública |

---

## 9.2 Variables para clustering

Posibles variables para segmentar zonas o días críticos:

```text
mp25
mp10
so2
no2
velocidad_viento
temperatura
humedad
indice_vulnerabilidad_respiratoria
```

La dirección del viento puede transformarse antes de modelar, porque es una variable circular. Por ejemplo:

```text
direccion_viento_sin = sin(direccion_viento_grados)
direccion_viento_cos = cos(direccion_viento_grados)
```

Esto evita que el modelo interprete incorrectamente que 359° está muy lejos de 0°, cuando en realidad son direcciones casi iguales.

---

## 9.3 Variables para regresión

Variable objetivo sugerida:

```text
mp25_24h_futuro
```

Variables predictoras sugeridas:

```text
mp25_actual
mp10_actual
so2
no2
velocidad_viento
direccion_viento_grados
temperatura
humedad
hora
dia_semana
comuna
emision_maxima_permitida
```

---

# 10. Consideraciones de calidad de datos

## 10.1 Valores faltantes

Los campos ambientales son obligatorios en la base de datos. Sin embargo, en procesos ETL se debe validar si una fuente externa trae datos faltantes antes de insertar en la base.

Ejemplos de valores inválidos:

```text
NULL
NaN
"sin dato"
"NR"
"ausente"
```

---

## 10.2 Duplicados

La restricción única:

```text
id_estacion + fecha_hora
```

evita duplicar una medición para el mismo sensor y momento.

---

## 10.3 Rangos inválidos

Se deben rechazar o corregir valores como:

| Campo | Valor inválido |
|---|---|
| `mp25` | negativo |
| `mp10` | negativo |
| `so2` | negativo |
| `no2` | negativo |
| `velocidad_viento` | negativo |
| `direccion_viento_grados` | menor que 0 o mayor que 360 |
| `humedad` | menor que 0 o mayor que 100 |
| `latitud` | menor que -90 o mayor que 90 |
| `longitud` | menor que -180 o mayor que 180 |

---

# 11. Resumen de tablas

| Tabla | Tipo | Descripción |
|---|---|---|
| `comunas` | Maestra | Información territorial y vulnerabilidad respiratoria |
| `estaciones_sensores` | Maestra | Sensores o estaciones de monitoreo |
| `industrias_fuentes` | Maestra | Fuentes fijas de contaminación |
| `monitoreo_ambiental` | Transaccional | Mediciones ambientales en serie temporal |

---

# 12. Conclusión

Este diccionario de datos documenta la estructura central del modelo relacional del sistema de monitoreo ambiental.

El diseño permite:

- representar comunas participantes;
- registrar estaciones oficiales y sensores comunitarios;
- identificar fuentes industriales;
- almacenar mediciones ambientales en el tiempo;
- calcular métricas derivadas como ICAP;
- alimentar procesos ETL, dashboards y modelos de Ciencia de Datos.

La tabla `monitoreo_ambiental` es el núcleo analítico del proyecto, ya que contiene las variables necesarias para estudiar contaminación, clima, riesgo ambiental y predicción de MP2.5.

# 01 - Contexto de Negocio

## Proyecto

**Sistema de Monitoreo de Calidad del Aire para la Zona Centro-Sur de Chile**

Este documento describe el contexto de negocio del proyecto, la problemática que busca resolver, los actores involucrados, los objetivos principales y el valor esperado de la solución. Su propósito es servir como base conceptual para el desarrollo de la base de datos, API REST, pipeline ETL, notebooks analíticos, dashboard y presentación final del proyecto.

---

## 1. Resumen ejecutivo

Una ONG ambiental, en conjunto con municipios de la zona centro-sur de Chile, requiere una solución tecnológica que permita monitorear de forma continua la calidad del aire en comunas ubicadas en las regiones de:

- O'Higgins
- Maule
- Ñuble
- Biobío

El problema principal es que actualmente la información ambiental se encuentra dispersa, se publica con retrasos, proviene de fuentes heterogéneas y no está centralizada en una plataforma común. Esto dificulta la identificación temprana de episodios críticos de contaminación y limita la capacidad de respuesta de municipios, organizaciones ambientales y ciudadanía.

La solución propuesta busca integrar datos de sensores, estaciones oficiales, fuentes industriales y variables meteorológicas para generar análisis, visualizaciones y modelos predictivos que permitan comprender y anticipar episodios de contaminación atmosférica.

---

## 2. Contexto del problema

La calidad del aire en la zona centro-sur de Chile se ve afectada por múltiples factores, entre ellos:

- Emisiones provenientes del sector industrial.
- Contaminación residencial, especialmente asociada al uso de leña.
- Condiciones meteorológicas que favorecen la acumulación de contaminantes.
- Incremento de enfermedades respiratorias en la población.
- Episodios de alerta, preemergencia o emergencia ambiental.
- Falta de centralización de datos provenientes de sensores y estaciones oficiales.

Actualmente, los datos de calidad del aire no siempre están disponibles de forma simple, oportuna y comprensible. Las estaciones oficiales pueden publicar datos con retraso o en formatos difíciles de procesar, mientras que sensores comunitarios o IoT pueden recolectar información relevante pero sin estar conectados a una base central.

Esto provoca una brecha entre la información técnica disponible y la toma de decisiones rápidas para proteger a la población.

---

## 3. Situación actual

El monitoreo ambiental se realiza de forma desarticulada. Existen distintas fuentes de información, pero no necesariamente se comunican entre sí.

Entre los principales problemas actuales se identifican:

| Problema | Impacto |
|---|---|
| Datos publicados con retraso | Dificulta reaccionar ante episodios críticos |
| Formatos complejos de procesar | Aumenta el tiempo de análisis |
| Sensores IoT no centralizados | Se pierde valor analítico de la información local |
| Bitácoras industriales aisladas | Dificulta relacionar contaminación con fuentes emisoras |
| Información técnica poco comprensible | Vecinos y ciudadanía no interpretan fácilmente el riesgo |
| Falta de predicción | La reacción ocurre tarde, no de forma preventiva |

---

## 4. Necesidad del negocio

La ONG y los municipios necesitan una plataforma integrada que permita:

1. Centralizar información ambiental proveniente de sensores, estaciones oficiales y fuentes industriales.
2. Consultar registros históricos de contaminación por comuna, sensor y fecha.
3. Analizar patrones espaciales y temporales de contaminación.
4. Relacionar episodios críticos con condiciones meteorológicas y fuentes industriales.
5. Entregar información comprensible para ciudadanos, investigadores y autoridades.
6. Desarrollar modelos predictivos que apoyen alertas tempranas.

El objetivo no es solamente almacenar datos, sino transformar esos datos en información útil para la toma de decisiones ambientales y sanitarias.

---

## 5. Actores involucrados

### 5.1 ONG ambiental

Organización interesada en monitorear, analizar y comunicar información ambiental a la ciudadanía. Su rol principal es impulsar la centralización de datos, la transparencia ambiental y la generación de alertas tempranas.

### 5.2 Municipios participantes

Instituciones locales de las regiones de O'Higgins, Maule, Ñuble y Biobío. Requieren información clara para apoyar decisiones comunales, fiscalización, comunicación pública y prevención de riesgos sanitarios.

### 5.3 Ciudadanía y vecinos

Usuarios finales que necesitan comprender la calidad del aire de su comuna en lenguaje simple. Para este grupo, los datos técnicos deben transformarse en indicadores comprensibles, como categorías de calidad del aire.

### 5.4 Equipo de Ciencia de Datos

Responsable de consumir la información consolidada, realizar análisis exploratorio, construir modelos de clustering y entrenar modelos predictivos para estimar niveles futuros de contaminación.

### 5.5 Autoridades e investigadores

Usuarios que requieren visualizaciones más detalladas, datos históricos y análisis por comuna, contaminante, fuente industrial y variable meteorológica.

---

## 6. Objetivo general del proyecto

Diseñar e implementar una solución tecnológica integral que permita almacenar, procesar, analizar y visualizar datos de calidad del aire para apoyar la detección, comprensión y predicción de episodios críticos de contaminación atmosférica en comunas de la zona centro-sur de Chile.

---

## 7. Objetivos específicos

- Implementar una base de datos relacional que normalice la información ambiental relevante.
- Registrar comunas, sensores, industrias fuentes y mediciones ambientales.
- Exponer servicios mediante una API REST para consultar y cargar datos.
- Construir un pipeline de datos que integre fuentes heterogéneas.
- Realizar análisis exploratorio de contaminación por comuna, sensor y periodo.
- Calcular métricas comprensibles para ciudadanía, como categorías de calidad del aire.
- Aplicar clustering para segmentar zonas o días según riesgo ambiental.
- Entrenar modelos predictivos para estimar MP2.5 en las próximas 24 horas.
- Desarrollar dashboards interactivos diferenciados por audiencia.
- Documentar la solución de forma clara, reproducible y profesional.

---

## 8. Alcance del proyecto

El proyecto se divide en tres fases principales:

### Fase A: Persistencia y modelo de datos

Se implementa una base de datos relacional en PostgreSQL o MySQL. La base debe normalizar la operación del sistema ambiental mediante cuatro tablas principales:

| Tabla | Propósito |
|---|---|
| `comunas` | Registrar municipios participantes, región, población estimada e índice de vulnerabilidad respiratoria |
| `estaciones_sensores` | Registrar estaciones oficiales o sensores comunitarios IoT, con código único, tipo y coordenadas |
| `industrias_fuentes` | Registrar fuentes fijas de contaminación, rubro industrial y emisión máxima permitida |
| `monitoreo_ambiental` | Registrar series temporales de mediciones ambientales por estación o sensor |

La tabla `monitoreo_ambiental` es la base para el análisis temporal, ya que registra mediciones por fecha y hora.

### Fase B: Backend y exposición de servicios

Se implementa una API REST para comunicar la base de datos con otros componentes del sistema.

Los servicios mínimos considerados son:

- Endpoints de consulta o analítica mediante métodos GET.
- Endpoint de consulta específica por identificador.
- Rutas POST para recibir datos diarios desde sensores.
- Actualización de registros ambientales en la base de datos.

El backend permite que el sistema no dependa de consultas manuales directas a la base de datos, facilitando la integración con dashboards, scripts ETL y notebooks.

### Fase C: Ciencia de Datos y modelamiento predictivo

Se desarrollan notebooks Jupyter y scripts Python para construir el pipeline analítico del proyecto.

Esta fase considera:

#### Análisis Exploratorio de Datos (EDA)

Busca identificar patrones espaciales y temporales de contaminación. Algunos análisis esperados son:

- Evolución de MP2.5 y MP10 por comuna.
- Comparación de contaminación entre sensores.
- Relación entre dirección del viento y niveles máximos de MP2.5.
- Relación entre proximidad a industrias y contaminación.
- Transformación de datos técnicos en categorías comprensibles para vecinos.

#### Clustering / Aprendizaje No Supervisado

Se utilizan algoritmos como K-Means para agrupar días o zonas sensorizadas según nivel de riesgo ambiental.

Ejemplos de grupos posibles:

- Riesgo bajo
- Riesgo moderado
- Riesgo crítico

El objetivo es descubrir patrones de riesgo sin depender únicamente de reglas manuales.

#### Regresión / Aprendizaje Supervisado

Se entrena un modelo predictivo para estimar la concentración esperada de MP2.5 en las próximas 24 horas.

Variables posibles de entrada:

- MP2.5 histórico
- MP10 histórico
- Velocidad del viento
- Dirección del viento
- Temperatura
- Humedad
- Información de industrias o emisiones permitidas
- Comuna o zona monitoreada
- Hora, día o estacionalidad

La predicción de MP2.5 puede funcionar como base para un sistema de alertas tempranas.

---

## 9. Variables principales del proyecto

### 9.1 Variables territoriales

| Variable | Descripción |
|---|---|
| Región | Región administrativa donde se ubica la comuna |
| Comuna | Municipio participante del sistema |
| Población estimada | Cantidad aproximada de habitantes |
| Índice de vulnerabilidad respiratoria | Indicador comunal para priorizar zonas sensibles |

### 9.2 Variables de sensores

| Variable | Descripción |
|---|---|
| Código único | Identificador del sensor o estación |
| Tipo de sensor | Público oficial o comunitario ONG |
| Latitud | Coordenada geográfica |
| Longitud | Coordenada geográfica |
| Comuna | Comuna donde se ubica el sensor |

### 9.3 Variables industriales

| Variable | Descripción |
|---|---|
| Nombre industria | Fuente fija de contaminación |
| Rubro industrial | Tipo de actividad productiva |
| Emisión máxima permitida | Límite autorizado de emisión |
| Comuna | Ubicación comunal de la fuente |

### 9.4 Variables ambientales

| Variable | Descripción |
|---|---|
| Fecha/hora | Momento de la medición |
| MP2.5 | Material particulado fino |
| MP10 | Material particulado respirable |
| SO2 | Dióxido de azufre |
| NO2 | Dióxido de nitrógeno |
| Velocidad del viento | Intensidad del viento, útil para analizar dispersión |
| Dirección del viento | Orientación del viento, útil para relacionar contaminación con fuentes |
| Temperatura | Condición meteorológica |
| Humedad | Condición meteorológica |

---

## 10. Uso del ICAP / ICA en el negocio

El caso menciona la necesidad de transformar datos técnicos en métricas comprensibles para vecinos, como el Índice de Calidad del Aire.

En el contexto chileno, se recomienda documentar y utilizar el ICAP, es decir, el Índice de Calidad del Aire referido a Partículas. Este indicador se puede calcular principalmente a partir de MP2.5 y MP10.

En este proyecto, el ICAP puede utilizarse para:

- Clasificar la calidad del aire de forma simple.
- Mostrar categorías en dashboards ciudadanos.
- Identificar episodios críticos.
- Generar alertas comprensibles.
- Comparar comunas según severidad ambiental.

Ejemplo de salida para usuarios:

```text
Comuna: Chillán
MP2.5 promedio 24h: 92 µg/m³
Condición estimada: Alerta
Recomendación: reducir exposición prolongada al aire libre en grupos sensibles.
```

---

## 11. Preguntas de negocio

El sistema debe permitir responder preguntas como:

1. ¿Qué comunas presentan mayores niveles de MP2.5?
2. ¿En qué horarios o fechas aumentan los episodios críticos?
3. ¿Existe relación entre baja velocidad del viento y aumento de material particulado?
4. ¿La dirección del viento permite asociar contaminación con industrias cercanas?
5. ¿Qué sensores registran más episodios críticos?
6. ¿Qué comunas combinan alta contaminación y alta vulnerabilidad respiratoria?
7. ¿Se puede predecir el MP2.5 esperado para las próximas 24 horas?
8. ¿Qué condiciones meteorológicas gatillan una emergencia ambiental comunal?
9. ¿Qué zonas deben priorizarse para alertas ciudadanas?
10. ¿Cómo presentar la información de forma distinta para vecinos, investigadores y autoridades?

---

## 12. Audiencias del dashboard

El dashboard debe considerar diferentes niveles de profundidad según la audiencia.

### 12.1 Audiencia ciudadana

Necesita información clara y simple.

Visualizaciones sugeridas:

- Estado de calidad del aire por comuna.
- Categoría ICAP / ICA.
- Alertas simples.
- Recomendaciones generales.
- Semáforo de riesgo.

Lenguaje sugerido:

```text
Calidad del aire: Alerta
Personas sensibles deberían reducir actividad física intensa al aire libre.
```

### 12.2 Audiencia técnica

Necesita mayor detalle analítico.

Visualizaciones sugeridas:

- Series temporales de contaminantes.
- Comparación por sensor.
- Mapas con coordenadas de estaciones e industrias.
- Correlación entre viento, temperatura, humedad y MP2.5.
- Resultados de clustering.
- Evaluación de modelos predictivos.

### 12.3 Audiencia ejecutiva o municipal

Necesita indicadores resumidos para toma de decisiones.

Visualizaciones sugeridas:

- Ranking de comunas con mayor riesgo.
- Cantidad de episodios críticos por periodo.
- Comunas con alta vulnerabilidad respiratoria.
- Tendencia semanal o mensual.
- Resumen de alertas.
- Priorización territorial.

---

## 13. Valor de negocio esperado

La solución genera valor porque permite:

- Centralizar información ambiental dispersa.
- Reducir tiempos de análisis.
- Mejorar la toma de decisiones municipales.
- Facilitar la comunicación de riesgos a la ciudadanía.
- Relacionar contaminación con variables meteorológicas e industriales.
- Apoyar la prevención mediante predicción de MP2.5.
- Generar evidencia para políticas ambientales locales.
- Crear visualizaciones adaptadas a diferentes usuarios.

---

## 14. Indicadores sugeridos

| Indicador | Descripción |
|---|---|
| Promedio diario de MP2.5 | Nivel promedio de material particulado fino por día |
| Máximo diario de MP2.5 | Mayor concentración registrada en el día |
| Promedio diario de MP10 | Nivel promedio de material particulado respirable |
| Cantidad de episodios críticos | Número de registros clasificados como alerta, preemergencia o emergencia |
| Comuna con mayor riesgo | Comuna con mayor frecuencia de episodios críticos |
| Sensor con mayor concentración | Sensor que registra mayor nivel de contaminación |
| Días con baja ventilación | Días con baja velocidad del viento |
| Relación viento-contaminación | Análisis entre dirección/velocidad del viento y MP2.5 |
| Vulnerabilidad ambiental comunal | Cruce entre contaminación y vulnerabilidad respiratoria |
| Predicción MP2.5 24h | Estimación de concentración esperada para el día siguiente |

---

## 15. Fuentes de datos esperadas

De acuerdo con el alcance del proyecto y la evaluación, la solución debe integrar múltiples fuentes de datos. Para este caso, se proponen:

| Fuente | Tipo | Uso |
|---|---|---|
| Base de datos SQL | PostgreSQL/MySQL | Almacenamiento relacional de comunas, sensores, industrias y monitoreo |
| API REST | Servicio backend | Carga y consulta de mediciones ambientales |
| CSV/Excel | Archivo externo | Datos simulados, históricos o entregados por la cátedra |
| Sensores IoT simulados | Datos operacionales | Registros diarios de variables ambientales |

Estas fuentes permiten construir un pipeline ETL reproducible y alineado con un escenario profesional.

---

## 16. Alcance analítico

El análisis de datos tendrá tres niveles:

### Nivel descriptivo

Responde qué está ocurriendo.

Ejemplos:

- Promedio de MP2.5 por comuna.
- Evolución diaria de MP10.
- Sensores con mayor concentración de contaminantes.

### Nivel diagnóstico

Responde por qué podría estar ocurriendo.

Ejemplos:

- Relación entre viento y contaminación.
- Relación entre industrias cercanas y MP2.5.
- Comparación de comunas según vulnerabilidad respiratoria.

### Nivel predictivo

Responde qué podría ocurrir.

Ejemplos:

- Predicción de MP2.5 para las próximas 24 horas.
- Identificación temprana de condiciones de riesgo.
- Soporte para alertas automáticas.

---

## 17. Supuestos del proyecto

Para desarrollar la solución se consideran los siguientes supuestos:

- Los datos utilizados pueden ser simulados si la cátedra no entrega datos reales.
- Las mediciones ambientales se registran diariamente o en intervalos definidos.
- Cada sensor pertenece a una comuna.
- Cada industria fuente se asocia a una comuna.
- El análisis de proximidad puede apoyarse en coordenadas geográficas.
- El ICAP se calcula como métrica derivada y no necesariamente se almacena como dato base.
- Los modelos predictivos entregan estimaciones y no reemplazan una declaración oficial de emergencia ambiental.

---

## 18. Restricciones y consideraciones

- La calidad del modelo depende de la calidad de los datos disponibles.
- Si los datos son simulados, las conclusiones deben interpretarse como resultados académicos.
- Las variables meteorológicas ayudan a explicar episodios críticos, pero no son contaminantes.
- SO2 y NO2 son contaminantes relevantes, aunque no forman parte directa del ICAP referido a partículas.
- La plataforma debe diferenciar entre análisis técnico y comunicación ciudadana.
- La solución debe ser reproducible mediante documentación, Docker y estructura clara de carpetas.

---

## 19. Relación con la evaluación

Este contexto de negocio se conecta directamente con los entregables de la evaluación:

| Requisito | Relación con el proyecto |
|---|---|
| Pipeline ETL | Integración de sensores, API, base SQL y archivos simulados |
| Documentación técnica | Explicación del caso, arquitectura, API, despliegue y uso |
| Dashboard interactivo | Visualización de calidad del aire diferenciada por audiencia |
| Git colaborativo | Control de versiones, ramas, merges y evidencia del trabajo |
| Docker | Ejecución reproducible de base de datos, API y dashboard |
| Presentación | Defensa del valor de negocio, arquitectura y resultados |

---

## 20. Criterios de éxito

El proyecto será exitoso si logra:

- Registrar correctamente comunas, sensores, industrias y mediciones ambientales.
- Integrar al menos tres fuentes de datos.
- Ejecutar un pipeline ETL reproducible.
- Exponer datos mediante API REST.
- Mostrar dashboards interactivos y comprensibles.
- Identificar patrones espaciotemporales de contaminación.
- Segmentar días o zonas según riesgo ambiental.
- Estimar MP2.5 futuro mediante un modelo de regresión.
- Documentar claramente la solución.
- Ejecutarse en un entorno Dockerizado.
- Comunicar valor técnico y ciudadano durante la presentación.

---

## 21. Conclusión

El proyecto busca resolver una problemática ambiental real: la falta de centralización, análisis oportuno y comunicación clara de datos de calidad del aire.

La solución propuesta no se limita a almacenar mediciones, sino que busca construir una plataforma end-to-end capaz de integrar datos, procesarlos, analizarlos, visualizarlos y generar predicciones útiles para la toma de decisiones.

Desde el punto de vista de negocio, el mayor valor está en transformar datos ambientales técnicos en información comprensible y accionable para municipios, investigadores y vecinos de las comunas afectadas.

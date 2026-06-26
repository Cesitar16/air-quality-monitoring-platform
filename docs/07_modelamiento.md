# Modelamiento de riesgo ambiental

## 1. Introducción

Esta etapa del proyecto analiza el comportamiento de la calidad del aire y construye perfiles relativos de riesgo ambiental mediante análisis exploratorio de datos y clustering.

El modelamiento consume el dataset integrado por el pipeline ETL y expuesto por la API del proyecto. La solución permite transformar miles de mediciones ambientales en información resumida e interpretable para apoyar visualizaciones, análisis territorial y toma de decisiones dentro del caso de estudio.

Los principales componentes desarrollados son:

* carga paginada del dataset desde la API;
* limpieza y validación de datos;
* análisis exploratorio de calidad del aire;
* estudio de relaciones entre contaminantes y meteorología;
* selección y estandarización de variables;
* evaluación del número de clusters;
* entrenamiento de K-Means;
* interpretación de perfiles de riesgo;
* análisis territorial de los resultados.

---

## 2. Objetivos

### 2.1 Objetivo general

Construir un flujo reproducible de análisis y clustering que permita identificar patrones de contaminación y generar perfiles relativos de riesgo ambiental.

### 2.2 Objetivos específicos

1. Consumir el dataset completo desde la API del proyecto.
2. Validar calidad, cobertura y consistencia de los datos.
3. Identificar comunas y regiones con mayores niveles de MP2.5.
4. Analizar la evolución temporal de la contaminación.
5. Estudiar relaciones entre contaminantes y variables meteorológicas.
6. Seleccionar variables representativas y evitar redundancia.
7. Evaluar diferentes cantidades de clusters.
8. Entrenar un modelo K-Means reproducible.
9. Interpretar los clusters como niveles relativos de riesgo.
10. Analizar la distribución territorial del riesgo crítico.

---

## 3. Arquitectura de la solución

La etapa de modelamiento se encuentra separada de la lógica interna del ETL y consume su resultado mediante la API.

El flujo general es:

```text
Fuentes simuladas
        ↓
Pipeline ETL
        ↓
PostgreSQL
        ↓
API /analytics/dataset-modelado
        ↓
Preprocesamiento
        ↓
Análisis exploratorio
        ↓
Estandarización de variables
        ↓
K-Means
        ↓
Perfiles de riesgo ambiental
```

Los principales archivos de esta etapa son:

```text
notebooks/
├── 01_eda_calidad_aire.ipynb
└── 02_clustering_riesgo_ambiental.ipynb

src/
├── __init__.py
├── preprocessing.py
├── clustering.py
└── visualizations.py

docs/
└── 07_modelamiento.md
```

### Responsabilidad de cada componente

#### `src/preprocessing.py`

Contiene funciones reutilizables para:

* cargar datos desde la API con paginación;
* cargar datos desde un CSV cuando sea necesario;
* convertir columnas a tipos adecuados;
* procesar fechas;
* validar rangos;
* eliminar duplicados;
* generar resúmenes de calidad;
* guardar datasets procesados.

#### `src/visualizations.py`

Contiene funciones para:

* MP2.5 promedio por comuna;
* MP2.5 promedio por región;
* evolución temporal;
* ranking de sensores;
* gráficos de dispersión;
* matriz de correlación;
* visualización de clusters.

#### `src/clustering.py`

Contiene funciones para:

* preparar variables de modelamiento;
* imputar valores faltantes;
* eliminar columnas vacías o constantes;
* aplicar `StandardScaler`;
* entrenar K-Means;
* evaluar diferentes valores de K;
* obtener centroides;
* agregar clusters al dataset;
* calcular perfiles relativos;
* asignar etiquetas de riesgo.

---

## 4. Fuente de datos

El análisis utiliza el endpoint:

```text
GET /analytics/dataset-modelado
```

La descarga se realiza mediante paginación usando los parámetros:

```text
limit
offset
```

Se utilizan solicitudes de hasta 1.000 registros hasta recuperar la totalidad del dataset.

Antes de ejecutar los notebooks se validó el flujo mediante:

```powershell
docker compose up --build -d
```

```powershell
.\.venv\Scripts\python.exe etl/run_pipeline.py --load-api
```

El pipeline ETL procesó las fuentes simuladas, validó las mediciones y cargó registros compatibles en la API.

La carga paginada desde la API obtuvo:

| Métrica                            |              Resultado |
| ---------------------------------- | ---------------------: |
| Registros recuperados desde la API |                 26.693 |
| Registros después de la limpieza   |                 26.622 |
| Columnas recibidas desde la API    |                     16 |
| Regiones                           |                      4 |
| Comunas                            |                     27 |
| Estaciones                         |                     44 |
| Fecha inicial                      |     6 de enero de 2026 |
| Fecha final                        | 9 de diciembre de 2026 |

La diferencia entre las filas recuperadas y las filas procesadas corresponde principalmente a registros duplicados eliminados durante el preprocesamiento.

Las fuentes pertenecen a un caso académico con datos simulados. Por lo tanto, los resultados no representan mediciones ambientales oficiales actuales.

---

## 5. Variables del dataset

El endpoint proporciona las siguientes variables:

### Variables temporales y territoriales

* `fecha_hora`
* `comuna`
* `region`
* `codigo_estacion`
* `tipo_sensor`

### Contaminantes

* `mp25`
* `mp10`
* `so2`
* `no2`

### Variables meteorológicas

* `velocidad_viento`
* `direccion_viento_grados`
* `temperatura`
* `humedad`

### Variables de contexto

* `indice_vulnerabilidad_respiratoria`
* `emision_maxima_permitida`
* `categoria_ica`

Durante el preprocesamiento también se generan variables temporales auxiliares:

* fecha;
* año;
* mes;
* día;
* hora;
* día de la semana.

---

## 6. Preprocesamiento

Antes del análisis se aplicaron las siguientes transformaciones:

1. Conversión de `fecha_hora` a tipo fecha.
2. Conversión de variables ambientales a formato numérico.
3. Limpieza de espacios en variables categóricas.
4. Validación de valores no negativos en contaminantes.
5. Validación de humedad entre 0 y 100.
6. Validación de dirección del viento entre 0 y 360 grados.
7. Validación de temperatura dentro de un rango razonable.
8. Eliminación de duplicados por fecha y estación.
9. Ordenamiento cronológico y territorial.
10. Reinicio del índice del DataFrame.

Para el clustering, los valores faltantes de las variables seleccionadas se imputaron mediante la mediana.

La mediana fue elegida porque es menos sensible a valores extremos que la media.

---

## 7. Resultados del análisis exploratorio

### 7.1 Cobertura del dataset

El análisis exploratorio se realizó sobre 26.622 registros procesados.

La información cubre:

* cuatro regiones;
* 27 comunas;
* 44 estaciones;
* aproximadamente once meses de 2026.

---

## 8. Distribución territorial de MP2.5

### 8.1 Comunas con mayor promedio

Las cinco comunas con mayor concentración promedio de MP2.5 fueron:

| Comuna      | Región | MP2.5 promedio | MP2.5 máximo | Mediciones |
| ----------- | ------ | -------------: | -----------: | ---------: |
| Chillán     | Ñuble  |          57,36 |       176,05 |      2.139 |
| Los Ángeles | Biobío |          53,57 |       178,05 |      1.766 |
| Nacimiento  | Biobío |          53,56 |       172,05 |        674 |
| San Carlos  | Ñuble  |          53,40 |       171,05 |      1.411 |
| Parral      | Maule  |          52,96 |       170,05 |        674 |

Chillán presentó el mayor promedio comunal de MP2.5.

Los Ángeles registró el máximo individual más alto entre las comunas del ranking, con 178,05.

### 8.2 Comparación regional

Los promedios regionales fueron:

| Región    | MP2.5 promedio | MP2.5 máximo | Mediciones |
| --------- | -------------: | -----------: | ---------: |
| Ñuble     |          51,99 |       176,05 |      4.276 |
| Biobío    |          46,33 |       178,05 |     10.804 |
| Maule     |          43,35 |       170,05 |      7.272 |
| O'Higgins |          41,28 |       118,05 |      4.270 |

Ñuble presentó la mayor concentración promedio regional.

Biobío concentró la mayor cantidad de mediciones y el valor máximo de MP2.5 más alto.

La cantidad de mediciones es diferente entre territorios, por lo que los promedios deben interpretarse considerando la cobertura disponible en cada región y comuna.

---

## 9. Evolución temporal

Los mayores promedios diarios de MP2.5 fueron:

| Fecha                | MP2.5 promedio | MP2.5 máximo | Mediciones |
| -------------------- | -------------: | -----------: | ---------: |
| 22 de agosto de 2026 |         126,49 |       178,05 |        128 |
| 21 de agosto de 2026 |         120,14 |       171,70 |        128 |
| 20 de agosto de 2026 |         118,79 |       170,35 |        128 |
| 19 de julio de 2026  |          97,28 |       133,40 |        128 |
| 21 de junio de 2026  |          97,28 |       133,40 |        128 |

El episodio más crítico ocurrió entre el 20 y el 22 de agosto de 2026.

Los mayores niveles se concentran durante meses fríos, lo que muestra un patrón estacional dentro del caso de estudio.

Este comportamiento puede estar asociado a una combinación de:

* menor temperatura;
* mayor humedad;
* menor ventilación;
* acumulación de contaminantes.

Estas relaciones representan asociaciones observadas en el dataset y no demuestran causalidad.

---

## 10. Correlaciones

Las correlaciones de las variables ambientales con MP2.5 fueron:

| Variable                              | Correlación con MP2.5 |
| ------------------------------------- | --------------------: |
| MP10                                  |                 0,980 |
| Humedad                               |                 0,721 |
| Índice de vulnerabilidad respiratoria |                 0,177 |
| NO2                                   |                 0,161 |
| SO2                                   |                 0,117 |
| Emisión máxima permitida              |                 0,025 |
| Velocidad del viento                  |                -0,661 |
| Temperatura                           |                -0,769 |

### Interpretación

MP2.5 y MP10 presentan una correlación de 0,980. Esto muestra que ambas variables cambian de manera muy similar dentro del dataset.

La humedad presenta una asociación positiva importante con MP2.5.

La temperatura y la velocidad del viento presentan asociaciones negativas:

* al aumentar la temperatura, MP2.5 tiende a disminuir;
* al aumentar la velocidad del viento, MP2.5 tiende a disminuir.

Las variables SO2, NO2, emisiones industriales y vulnerabilidad presentan correlaciones individuales menores con MP2.5, pero aportan dimensiones adicionales para el modelamiento multivariable.

---

## 11. Selección de variables para clustering

Las variables utilizadas en K-Means fueron:

```text
mp25
so2
no2
velocidad_viento
indice_vulnerabilidad_respiratoria
emision_maxima_permitida
```

MP10 fue excluido porque presenta una correlación de 0,980 con MP2.5.

Incluir simultáneamente MP2.5 y MP10 podría entregar una influencia duplicada al material particulado dentro del cálculo de distancias.

Las variables seleccionadas representan dimensiones diferentes:

| Dimensión                  | Variable                              |
| -------------------------- | ------------------------------------- |
| Material particulado       | MP2.5                                 |
| Contaminación gaseosa      | SO2 y NO2                             |
| Dispersión atmosférica     | Velocidad del viento                  |
| Vulnerabilidad territorial | Índice de vulnerabilidad respiratoria |
| Contexto industrial        | Emisión máxima permitida              |

---

## 12. Estandarización

K-Means utiliza distancias para asignar registros a los clusters.

Como las variables presentan escalas diferentes, se aplicó:

```python
StandardScaler
```

La transformación produce variables centradas alrededor de cero y con desviación estándar cercana a uno.

La estandarización evita que variables con valores numéricos mayores dominen de manera artificial el cálculo de distancias.

---

## 13. Evaluación del número de clusters

Se evaluaron valores de K entre 2 y 6.

Las métricas utilizadas fueron:

### Inercia

Representa la suma de las distancias cuadradas de los registros respecto de sus centroides.

Una menor inercia indica grupos internos más compactos, aunque siempre disminuye al aumentar K.

### Silhouette

Evalúa simultáneamente:

* cohesión dentro de cada cluster;
* separación respecto de otros clusters.

Un valor mayor representa una mejor separación.

Los resultados fueron:

|  K |    Inercia | Silhouette |
| -: | ---------: | ---------: |
|  2 | 106.261,27 |     0,3242 |
|  3 |  83.926,53 |     0,2813 |
|  4 |  71.554,02 |     0,2686 |
|  5 |  63.276,73 |     0,2606 |
|  6 |  56.432,11 |     0,2733 |

El mayor silhouette se obtuvo con K=2.

Sin embargo, se seleccionó K=3 para construir tres perfiles interpretables:

* bajo riesgo;
* riesgo moderado;
* riesgo crítico.

La decisión combina evaluación estadística e interpretabilidad funcional.

K=3 presenta una separación inferior a K=2, pero permite representar tres niveles relativos de riesgo y mantiene un silhouette positivo de aproximadamente 0,2813.

---

## 14. Modelo K-Means

El modelo fue entrenado con:

```text
n_clusters = 3
random_state = 42
n_init = 10
```

El uso de `random_state=42` permite reproducir los resultados.

Después del entrenamiento:

1. se asignó un cluster a cada registro;
2. se recuperaron los centroides en las unidades originales;
3. se calculó un perfil promedio por cluster;
4. se generó un puntaje relativo de riesgo;
5. se asignaron etiquetas interpretables.

La numeración interna de los clusters no representa un orden de riesgo.

Las etiquetas fueron asignadas después de estudiar los perfiles de cada grupo.

---

## 15. Puntaje relativo de riesgo

Para interpretar los clusters se utilizó un puntaje relativo basado en variables normalizadas.

Las ponderaciones disponibles son:

| Variable                              | Peso | Dirección |
| ------------------------------------- | ---: | --------- |
| MP2.5                                 | 0,45 | Directa   |
| SO2                                   | 0,08 | Directa   |
| NO2                                   | 0,08 | Directa   |
| Velocidad del viento                  | 0,04 | Inversa   |
| Índice de vulnerabilidad respiratoria | 0,12 | Directa   |
| Emisión máxima permitida              | 0,04 | Directa   |

Una relación directa significa que valores mayores aumentan el puntaje relativo.

La velocidad del viento se interpreta de forma inversa porque una mayor ventilación favorece la dispersión de contaminantes.

El puntaje permite ordenar los clusters de menor a mayor riesgo relativo.

No corresponde a un indicador regulatorio oficial.

---

## 16. Resultados del clustering

### 16.1 Distribución general

| Nivel de riesgo | Registros | Porcentaje |
| --------------- | --------: | ---------: |
| Bajo riesgo     |    13.175 |     49,49% |
| Riesgo moderado |     7.010 |     26,33% |
| Riesgo crítico  |     6.437 |     24,18% |

Aproximadamente la mitad de los registros pertenece al perfil de bajo riesgo.

Cerca de una cuarta parte del dataset fue clasificada como riesgo crítico relativo.

### 16.2 Perfil promedio

| Nivel de riesgo | Puntaje |  MP2.5 |    SO2 |    NO2 |
| --------------- | ------: | -----: | -----: | -----: |
| Bajo riesgo     |   0,000 | 32,143 | 21,954 | 41,352 |
| Riesgo moderado |   0,568 | 44,201 | 50,883 | 62,913 |
| Riesgo crítico  |   0,678 | 74,723 | 27,539 | 46,023 |

---

## 17. Interpretación de los perfiles

### 17.1 Bajo riesgo

El cluster de bajo riesgo contiene 13.175 registros.

Sus características principales son:

* menor promedio de MP2.5;
* menor puntaje relativo;
* valores promedio menores de SO2 y NO2 que el grupo moderado;
* condiciones comparativamente menos desfavorables dentro del dataset.

La etiqueta bajo riesgo es relativa a los otros clusters y no significa ausencia de contaminación.

### 17.2 Riesgo moderado

El cluster moderado contiene 7.010 registros.

Sus características principales son:

* MP2.5 promedio superior al grupo bajo;
* mayores promedios de SO2 y NO2;
* puntaje de riesgo de aproximadamente 0,568;
* combinación ambiental diferente al resto de los clusters.

El grupo moderado no representa solamente un punto intermedio lineal. Se distingue especialmente por sus contaminantes gaseosos.

### 17.3 Riesgo crítico

El cluster crítico contiene 6.437 registros.

Sus características principales son:

* MP2.5 promedio de aproximadamente 74,723;
* mayor puntaje relativo de riesgo;
* concentración de MP2.5 considerablemente superior a los demás grupos;
* combinación desfavorable de contaminación, dispersión, vulnerabilidad y contexto industrial.

El MP2.5 promedio del grupo crítico es más del doble que el promedio del grupo bajo.

---

## 18. Distribución territorial del riesgo crítico

Las comunas con mayor proporción de registros críticos fueron:

| Región    | Comuna      | Mediciones | MP2.5 promedio | MP2.5 máximo | Porcentaje crítico |
| --------- | ----------- | ---------: | -------------: | -----------: | -----------------: |
| O'Higgins | Rancagua    |      2.140 |          45,91 |       118,05 |             43,04% |
| Ñuble     | Chillán     |      2.139 |          57,36 |       176,05 |             42,36% |
| Ñuble     | San Carlos  |      1.411 |          53,40 |       171,05 |             38,70% |
| Maule     | Linares     |      1.347 |          50,98 |       168,05 |             38,08% |
| Maule     | Parral      |        674 |          52,96 |       170,05 |             37,69% |
| Biobío    | Los Ángeles |      1.766 |          53,57 |       178,05 |             37,15% |
| Biobío    | Cabrero     |        674 |          50,45 |       167,05 |             36,80% |
| Maule     | Talca       |      1.769 |          41,64 |       116,05 |             33,80% |
| Maule     | Cauquenes   |        675 |          44,17 |       157,05 |             32,15% |
| Biobío    | Nacimiento  |        674 |          53,56 |       172,05 |             29,67% |

Rancagua presenta el porcentaje crítico más alto, aunque no posee el mayor promedio general de MP2.5.

Esto demuestra que el clustering utiliza múltiples variables y no clasifica los registros únicamente según MP2.5.

---

## 19. Aporte del modelo

El modelo permite convertir 26.622 registros ambientales en tres perfiles resumidos.

Sus principales aportes son:

* simplificar la interpretación de datos multivariables;
* identificar condiciones ambientales de mayor riesgo relativo;
* comparar patrones entre comunas;
* apoyar la priorización territorial;
* entregar información para visualizaciones;
* facilitar análisis posteriores;
* proporcionar una base para incorporar resultados al dashboard.

---

## 20. Limitaciones

El análisis presenta las siguientes limitaciones:

1. Las fuentes corresponden a datos simulados de un caso académico.
2. Las categorías de riesgo son relativas al dataset.
3. Las etiquetas no corresponden a categorías regulatorias oficiales.
4. K-Means utiliza distancia euclidiana y supone clusters aproximadamente compactos.
5. Los valores faltantes fueron imputados mediante la mediana.
6. La selección de variables influye directamente en los resultados.
7. El escalamiento modifica la forma en que las variables participan en las distancias.
8. Las ponderaciones del puntaje constituyen una decisión analítica.
9. K=2 obtuvo mejor silhouette que K=3.
10. K=3 fue seleccionado principalmente por interpretabilidad funcional.
11. Una proyección en dos dimensiones no representa completamente un modelo de seis variables.
12. Las correlaciones no demuestran causalidad.
13. El periodo disponible no cubre varios años.
14. Los perfiles deberían ser revisados por especialistas ambientales antes de utilizarse en un contexto real.

---

## 21. Próximos pasos

Como continuación se recomienda:

1. Validar las ponderaciones con especialistas ambientales.
2. Comparar K-Means con clustering jerárquico.
3. Evaluar DBSCAN para detectar grupos no esféricos.
4. Aplicar PCA para visualizar el espacio multivariable.
5. Evaluar estabilidad del modelo ante nuevas cargas.
6. Monitorear cambios en los centroides.
7. Analizar deriva de datos.
8. Incorporar información de más años.
9. Persistir las etiquetas en una tabla analítica.
10. Exponer resultados mediante un endpoint.
11. Incorporar clusters al dashboard.
12. Crear pruebas automatizadas de preprocesamiento.
13. Crear pruebas automatizadas del modelamiento.
14. Comparar el puntaje relativo con categorías ICA.
15. Evaluar mecanismos de reentrenamiento después de cada carga ETL.

---

## 22. Ejecución del análisis

### 22.1 Crear y activar el entorno

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 22.2 Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements-analysis.txt
```

También deben instalarse las dependencias de la API y el ETL:

```powershell
pip install -r api/requirements.txt
```

### 22.3 Levantar los servicios

```powershell
docker compose up --build -d
```

### 22.4 Verificar la API

```powershell
Invoke-RestMethod http://localhost:8000/health
```

La respuesta esperada es:

```json
{
  "status": "ok",
  "service": "air-quality-api",
  "database": "connected"
}
```

### 22.5 Ejecutar el ETL

```powershell
.\.venv\Scripts\python.exe etl/run_pipeline.py --load-api
```

### 22.6 Ejecutar los notebooks

Abrir:

```text
notebooks/01_eda_calidad_aire.ipynb
notebooks/02_clustering_riesgo_ambiental.ipynb
```

Seleccionar el kernel correspondiente a `.venv`.

Después ejecutar:

```text
Restart Kernel and Run All Cells
```

---

## 23. Validación técnica

Los módulos pueden validarse con:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/preprocessing.py
.\.venv\Scripts\python.exe -m py_compile src/visualizations.py
.\.venv\Scripts\python.exe -m py_compile src/clustering.py
```

Las pruebas del repositorio pueden ejecutarse con:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

También se debe comprobar que:

* ambos notebooks ejecuten todas sus celdas;
* no queden errores guardados;
* la API devuelva el dataset completo;
* no existan valores nulos después de la preparación del modelo;
* se generen tres clusters;
* todos los registros tengan una etiqueta de riesgo;
* las tres etiquetas esperadas estén presentes.

---

## 24. Conclusiones generales

El análisis exploratorio permitió identificar diferencias territoriales y temporales en la contaminación por MP2.5.

Ñuble presentó el mayor promedio regional, mientras que Chillán encabezó el ranking comunal.

Los principales episodios críticos se concentraron durante agosto de 2026.

MP2.5 mostró relaciones importantes con:

* MP10;
* humedad;
* temperatura;
* velocidad del viento.

Estas relaciones permitieron justificar la selección de variables y evitar redundancia antes del clustering.

El modelo K-Means resumió 26.622 registros en tres perfiles interpretables:

* bajo riesgo;
* riesgo moderado;
* riesgo crítico.

El perfil crítico concentra aproximadamente el 24,18% del dataset y presenta un MP2.5 promedio claramente superior al de los otros grupos.

Los resultados permiten identificar patrones ambientales y territoriales dentro del caso de estudio, pero deben interpretarse como una clasificación relativa y académica, no como una evaluación ambiental oficial.

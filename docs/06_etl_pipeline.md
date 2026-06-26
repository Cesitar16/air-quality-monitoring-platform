# Pipeline ETL - Calidad del Aire

## Objetivo

Este pipeline ETL integra fuentes externas simuladas del caso de calidad del aire para transformar, validar y cargar mediciones hacia PostgreSQL mediante la API del proyecto. También genera `dataset_modelado.csv` para analítica, EDA y fases posteriores.

## Fuentes planificadas

- `mediciones_oficiales.csv`
- `sensores_comunitarios.csv`
- `fiscalizacion_industrias.xlsx`
- `clima_historico.csv`
- `mapeo_estaciones.csv`

## Flujo ETL

`Extract -> Transform -> Validate -> Load`

## Salidas esperadas

- `data/processed/mediciones_limpias.csv`
- `data/processed/mediciones_validas.csv`
- `data/processed/industrias_limpias.csv`
- `data/processed/clima_limpio.csv`
- `data/processed/errores_etl.csv`
- `data/processed/payload_monitoreo_bulk.json`
- `data/processed/omitidas_carga_api.csv`
- `data/processed/reporte_carga_api.csv`
- `data/processed/dataset_modelado.csv`

## Relación con la API

El ETL usa los siguientes endpoints existentes:

- `GET /health`
- `GET /estaciones`
- `GET /comunas`
- `GET /monitoreo`
- `POST /monitoreo/bulk`
- `GET /analytics/dataset-modelado`

## Ejecución local

### Preparar entorno con uv y Python 3.13+

```bash
uv venv --python 3.13 .venv
```

En PowerShell:

```powershell
.venv\Scripts\Activate.ps1
uv pip install --python .\.venv\Scripts\python.exe -r api/requirements.txt
```

### Ejecutar ETL

Modo por defecto:

```bash
python etl/run_pipeline.py
```

Modo explícito dry-run:

```bash
python etl/run_pipeline.py --dry-run
```

Carga real vía API:

```bash
python etl/run_pipeline.py --load-api
```

Con el intérprete del entorno:

```powershell
.\.venv\Scripts\python.exe etl/run_pipeline.py --dry-run
.\.venv\Scripts\python.exe etl/run_pipeline.py --load-api
```

## Fase 2: Fuentes raw y extracción

### Fuentes implementadas

- `mediciones_oficiales.csv`
- `sensores_comunitarios.csv`
- `fiscalizacion_industrias.xlsx`
- `clima_historico.csv`

Estas fuentes representan sistemas externos simulados y usan códigos de estación referenciales, no alineados automáticamente con la base relacional.

### Problemas de calidad simulados

- coma decimal
- espacios extras
- variantes de nombres de región y comuna
- duplicados
- valores faltantes
- valores fuera de rango
- formatos de fecha mixtos

Las fuentes incluyen valores UTF-8 y variantes sucias controladas para la normalización posterior, por ejemplo: `Ñuble`, `Biobío`, `Chillán`, `Chillan`, `Concepción`, `Concepcion`, `Curicó`, `Curico`, `Hualpén`.

## Fase 3: Transformación y limpieza base

### Transformaciones implementadas

- Normalización de columnas.
- Normalización de comunas.
- Normalización de regiones.
- Conversión de fechas mixtas.
- Conversión de números con coma decimal.
- Unión de mediciones oficiales y comunitarias.
- Cruce con clima histórico.

### Salidas generadas

- `data/processed/mediciones_limpias.csv`
- `data/processed/industrias_limpias.csv`
- `data/processed/clima_limpio.csv`

### Importante

En esta fase todavía no se eliminan registros inválidos por reglas ambientales. Duplicados, faltantes, negativos, humedades mayores a 100 y direcciones mayores a 360 permanecen para la Fase 4.

## Fase 4: Validación ambiental y trazabilidad de errores

### Validaciones implementadas

- Esquema de columnas obligatorio.
- Contaminantes no negativos.
- Variables meteorológicas validadas cuando el valor existe.
- Detección de duplicados por código de estación y fecha_hora.
- Fuente de dato permitida.

### Salidas generadas

- `data/processed/mediciones_validas.csv`
- `data/processed/errores_etl.csv`

### Política de errores

Los registros inválidos no se eliminan silenciosamente. Se separan en `errores_etl.csv` con `numero_fila`, `fase` y `motivo_error`.

Una medición puede mantenerse válida aunque no tenga clima asociado. Si el valor climático existe, se valida su rango.

`errores_etl.csv` se genera siempre, incluso si no hay errores. En ese caso queda vacío, pero con encabezados completos.

## Fase 5: Carga a API y dataset modelado

### Modos de ejecución

- Dry-run: prepara payload, omitidas, reporte y dataset local sin depender de Docker/API.
- Load API: intenta enviar mediciones válidas al endpoint `POST /monitoreo/bulk`.

### Política de mapeo base

- Coincidencia exacta primero entre `codigo_estacion` ETL y `codigo_unico` de API.
- Si no hay match exacto, se usa heurística segura por comuna + tipo de sensor.
- Solo se asigna por heurística si existe exactamente una candidata.
- Si hay cero candidatas, se registra `estacion_no_encontrada`.
- Si hay más de una candidata, se registra `estacion_ambigua`.
- Nunca se elige la primera estación si existe ambigüedad.

## Fase 6: Mapeo real de estaciones y carga end-to-end

### Contrato de `mapeo_estaciones.csv`

El archivo `data/raw/mapeo_estaciones.csv` debe existir en UTF-8 y contener exactamente estas columnas:

- `codigo_estacion_raw`
- `codigo_unico_api`
- `comuna`
- `region`
- `fuente_dato`
- `tipo_sensor_api`

Este archivo resuelve el puente entre los códigos externos simulados del ETL como `OF-TAL-001` u `ONG-CON-001` y los códigos reales de la API como `SEN-TAL-OF-001` o `SEN-CON-ONG-001`.

### Precedencia de mapeo

La carga usa esta precedencia cerrada:

1. Coincidencia exacta entre `codigo_estacion` raw y `codigo_unico` expuesto por la API.
2. Mapeo manual preferente desde `data/raw/mapeo_estaciones.csv`.
3. Heurística segura por `comuna + tipo_sensor`.
4. Si no se puede resolver, la medición se omite con `estacion_no_encontrada` o `estacion_ambigua`.

Si el CSV manual apunta a un `codigo_unico_api` que no aparece en `GET /estaciones`, la fila no revienta el pipeline: queda registrada con `motivo_omision = codigo_api_no_disponible`.

### Política de mediciones ya existentes

Antes de llamar a `POST /monitoreo/bulk`, el ETL consulta `GET /monitoreo` para detectar mediciones ya presentes por `id_estacion + fecha_hora`.

- Las mediciones ya existentes no se reenvían.
- Se registran en `omitidas_carga_api.csv` con `motivo_omision = medicion_ya_existente`.
- No se alteran timestamps ni datos procesados para forzar inserciones.

### Política de clima requerido por API

El ETL permite clima faltante hasta la validación ambiental y por eso `mediciones_validas.csv` puede conservar filas sin datos climáticos completos.

Sin embargo, `POST /monitoreo/bulk` exige valores numéricos para:

- `velocidad_viento`
- `direccion_viento_grados`
- `temperatura`
- `humedad`

Por eso, antes del envío a la API:

- las filas con clima faltante no entran a `payload_monitoreo_bulk.json`
- quedan registradas en `omitidas_carga_api.csv` con `motivo_omision = clima_requerido_por_api`
- si después de ese filtro y de `medicion_ya_existente` no quedan filas enviables, no se hace `POST /monitoreo/bulk`
- `reporte_carga_api.csv` deja `insertados = 0`, `errores = 0` y el mensaje `No hay mediciones nuevas compatibles para enviar a la API.`

### Diferencia entre `--dry-run` y `--load-api`

- `--dry-run` es el modo por defecto. Ejecuta Extract + Transform + Validate + preparación de carga, sin requerir Docker.
- `--load-api` es estricto. Si fallan `/health`, `/estaciones`, `/monitoreo` o `GET /analytics/dataset-modelado`, el pipeline termina con error claro y no cae silenciosamente a dry-run.

### Salidas generadas

- `data/processed/payload_monitoreo_bulk.json`
- `data/processed/omitidas_carga_api.csv`
- `data/processed/reporte_carga_api.csv`
- `data/processed/dataset_modelado.csv`

## Docker y smoke test manual

Para validar la carga real end-to-end antes de demo o entrega:

1. Si hubo ejecuciones previas, limpiar estado:

   ```bash
   docker compose down -v
   ```

2. Levantar servicios:

   ```bash
   docker compose up --build
   ```

3. Verificar API:

   - `GET http://localhost:8000/health`
   - `GET http://localhost:8000/estaciones`

4. Ejecutar ETL real:

   ```powershell
   .\.venv\Scripts\python.exe etl/run_pipeline.py --load-api
   ```

5. Revisar:

   - `data/processed/payload_monitoreo_bulk.json`
   - `data/processed/omitidas_carga_api.csv`
   - `data/processed/reporte_carga_api.csv`
   - `data/processed/dataset_modelado.csv`

6. Confirmar que `dataset_modelado.csv` fue obtenido desde `GET /analytics/dataset-modelado` y que las omitidas por duplicado quedaron trazadas como `medicion_ya_existente`.

## Estado actual

Fase 6.1: corrección de CLI y filtro de clima requerido por API preparada.

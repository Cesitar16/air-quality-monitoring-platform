# Datos del proyecto

## raw

Contiene las fuentes originales simuladas:

- mediciones oficiales
- sensores comunitarios
- fiscalizacion industrial
- clima historico
- mapeo de estaciones

## processed

Contiene las salidas generadas por ETL, clustering y regresion:

- tablas limpias y validadas
- dataset para modelamiento
- clusters de riesgo ambiental
- pronosticos de MP2.5 a 24h

Los archivos de `processed/` pueden regenerarse ejecutando el ETL y los pipelines de modelamiento.

# Docker

## Decision tomada

El archivo canonico sigue siendo `docker-compose.yml` en la raiz porque ya funciona con la base y la API. Esta carpeta agrega una referencia mas ordenada para futuras extensiones sin romper ese contrato.

## Archivos

- `docker/docker-compose.yml`: compose alternativo con servicio de dashboard
- `docker/api.Dockerfile`: referencia para construir la API desde contexto raiz
- `docker/dashboard.Dockerfile`: referencia para construir Streamlit

## Uso recomendado hoy

```powershell
docker compose up --build
```

Si se desea experimentar con la version de esta carpeta, revisar y adaptar rutas antes de usarla en otro entorno.

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY dashboards/requirements.txt dashboards/requirements.txt
RUN pip install --no-cache-dir -r dashboards/requirements.txt

COPY dashboards dashboards
COPY src src
COPY data data
COPY models models
COPY api/app api/app

EXPOSE 8501

CMD ["streamlit", "run", "dashboards/app.py", "--server.address=0.0.0.0", "--server.port=8501"]

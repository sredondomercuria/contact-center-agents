# Imagen para Cloud Run: sirve el dashboard (que también expone /tasks/run-batch
# para Cloud Scheduler). Instalación editable para leer skills/ y knowledge_base/.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=8080
WORKDIR /app

COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
COPY skills ./skills
COPY knowledge_base ./knowledge_base

RUN pip install -e ".[integrations,gcp]"

EXPOSE 8080
CMD ["python", "-m", "contact_center.webapp.app"]

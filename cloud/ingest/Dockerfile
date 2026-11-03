FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ingest.py .
RUN useradd --system --no-create-home ingest
USER ingest
ENV PYTHONUNBUFFERED=1
CMD ["python", "ingest.py"]

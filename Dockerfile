FROM python:3.11-slim-bookworm

# awscli is handy if you ever pull artifacts/models from S3 at runtime
RUN apt-get update -y && apt-get install -y awscli && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# artifacts/ is gitignored (DVC-tracked, no remote), so the model isn't in the
# build context. Regenerate it at build time — stages 01-04 are self-contained
# (data ingestion downloads from a public URL). Stage 05 (MLflow eval) is skipped
# on purpose: it needs tracking credentials and isn't required to serve.
RUN python src/mlProject/pipeline/stage_01_data_ingestion.py \
    && python src/mlProject/pipeline/stage_02_data_validation.py \
    && python src/mlProject/pipeline/stage_03_data_transformation.py \
    && python src/mlProject/pipeline/stage_04_model_trainer.py

EXPOSE 8080

CMD ["python", "app.py"]

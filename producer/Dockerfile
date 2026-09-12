FROM python:3.12-slim

WORKDIR /app

COPY producer/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY common ./common
COPY producer ./producer

# The Fernet key is deliberately not copied into the image. Mount it at runtime
# at /run/secrets/model.key (or set MODEL_KEY_PATH to another mounted location).
ENTRYPOINT ["python", "-m", "producer.producer"]

FROM python:3.12-slim

WORKDIR /app

COPY consumer/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY common ./common
COPY consumer ./consumer

# The decryption key is deliberately not copied into the image. Mount it
# read-only at /run/secrets/model.key (or set MODEL_KEY_PATH at runtime).
ENTRYPOINT ["python", "-m", "consumer.consumer"]

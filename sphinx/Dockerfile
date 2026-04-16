FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends tini libsodium23 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY sphinx/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY sphinx/app.py .

ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["python", "app.py"]

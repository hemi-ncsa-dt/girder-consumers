FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends tini libsodium23 ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Workaround: the Kafka broker (kafka.kde.idies.jhu.edu:30600) serves its SSL.com
# leaf cert without the intermediate, so add the intermediate to the system trust
# store. Remove once `openssl s_client -showcerts` shows the full chain.
COPY certs/ssl.com-tls-i-rsa-r1.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

WORKDIR /app
COPY helix-otherdata/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ ./common/
COPY helix-otherdata/app.py .

ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["python", "app.py"]

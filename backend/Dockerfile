# python:3.12-slim publishes arm64 builds, so this image builds natively on the
# Ampere box with no buildx/--platform juggling. Every dependency we use ships
# aarch64 wheels (psycopg[binary], cryptography), which is why there is no gcc
# here - if that ever stops being true the build fails loudly rather than
# silently falling back to a slow source compile.
FROM python:3.12-slim

# Bytecode files and stdout buffering both cause more confusion than they save
# in a container: .pyc clutters the layer, and buffered stdout means `docker
# logs` shows nothing until the buffer flushes, which looks like a hang.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Requirements are copied and installed before the source so that editing a
# router does not invalidate the (slow) dependency layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY main.py .

# The app never needs to write to its own filesystem - uploads are held in
# memory and handed to OpenAI, and everything durable goes to Postgres. Running
# as a non-root user means a container compromise does not start out as root.
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000

# No --reload here: it watches the filesystem and restarts on change, which is
# a development convenience and a production liability.
# --proxy-headers makes uvicorn honour X-Forwarded-Proto from Caddy, so
# request.url reports https and not http. Without it oauthlib rejects the OAuth
# callback outright ("OAuth 2 MUST utilize https"), because TLS terminates at
# Caddy and the hop to this container is plain HTTP.
#
# --forwarded-allow-ips="*" is safe *because of the topology*: this container
# publishes no port and sits on the Compose network, so Caddy is the only thing
# that can reach it. A client cannot forge these headers from outside.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]

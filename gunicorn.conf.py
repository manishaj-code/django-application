"""Gunicorn settings. Every value can be overridden through environment variables."""

import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# A good starting point is 2-4 workers per CPU core; cap the default so small
# containers with many reported cores don't run out of memory.
workers = int(os.environ.get("WEB_CONCURRENCY", min(multiprocessing.cpu_count() * 2 + 1, 5)))
threads = int(os.environ.get("GUNICORN_THREADS", "1"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))
graceful_timeout = 30
keepalive = 5

# Recycle workers periodically to contain slow memory growth.
max_requests = 1000
max_requests_jitter = 100

# Log to stdout/stderr for the container/platform to collect.
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()

# Proxies allowed to set X-Forwarded-* headers. Only widen this when the app
# port is reachable solely through your reverse proxy (as in compose.yaml).
forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1")

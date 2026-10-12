"""
Small cache-backed, fixed-window rate limiter for sensitive endpoints.

Requests are counted per client IP and per named limit (see
``settings.RATELIMITS``). When the limit is exceeded the view is not called
and an HTTP 429 page is returned instead.
"""

import hashlib
import logging
import time
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render

logger = logging.getLogger(__name__)

_PERIODS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_rate(rate):
    """Turn ``"10/m"`` into ``(10, 60)``."""
    count, _, period = rate.partition("/")
    try:
        return int(count), _PERIODS[period.strip().lower()]
    except (ValueError, KeyError):
        raise ValueError(f"Invalid rate {rate!r}; expected e.g. '10/m'.") from None


def client_ip(request):
    """Best-effort client IP, honouring ``settings.NUM_PROXIES`` trusted proxies."""
    num_proxies = getattr(settings, "NUM_PROXIES", 0)
    if num_proxies:
        forwarded = [
            part.strip()
            for part in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
            if part.strip()
        ]
        if len(forwarded) >= num_proxies:
            return forwarded[-num_proxies]
    return request.META.get("REMOTE_ADDR", "")


def is_rate_limited(request, name):
    """Count this request against limit ``name``; True if it is over the limit."""
    if not settings.RATELIMIT_ENABLED:
        return False
    limit, period = parse_rate(settings.RATELIMITS[name])
    window = int(time.time() // period)
    ip_hash = hashlib.sha256(client_ip(request).encode()).hexdigest()[:32]
    key = f"ratelimit:{name}:{ip_hash}:{window}"
    cache.add(key, 0, timeout=period)
    try:
        count = cache.incr(key)
    except ValueError:  # key expired between add() and incr()
        cache.set(key, 1, timeout=period)
        count = 1
    if count > limit:
        logger.warning("Rate limit '%s' exceeded for a client.", name)
        return True
    return False


def ratelimit(name, methods=("POST",)):
    """Decorator for function views (use ``method_decorator`` for classes)."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.method in methods and is_rate_limited(request, name):
                return render(request, "errors/429.html", status=429)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator

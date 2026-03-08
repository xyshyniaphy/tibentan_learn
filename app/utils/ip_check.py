"""IP whitelist checking utilities."""
from fastapi import Request
from app.config import get_settings


def get_client_ip(request: Request) -> str:
    """Get the client IP address from the request, handling proxies."""
    # Check X-Forwarded-For header first (common for reverse proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, first one is the client
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header (used by nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return "127.0.0.1"


def is_ip_allowed(request: Request) -> bool:
    """Check if the client IP is in the whitelist."""
    settings = get_settings()
    client_ip = get_client_ip(request)

    # Parse whitelist from settings
    whitelist = [ip.strip() for ip in settings.ip_whitelist.split(",") if ip.strip()]

    # Check if client IP is in whitelist
    return client_ip in whitelist

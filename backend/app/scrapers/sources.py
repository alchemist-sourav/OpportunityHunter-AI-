import ipaddress
import socket
from urllib.parse import urlparse

from app.core.exceptions import DiscoveryInvalidUrlError

_PRIVATE_NETWORKS = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
    ipaddress.ip_network("::ffff:0:0/96"),
)


def normalize_domain(raw: str) -> str:
    if not raw:
        return ""
    domain = raw.strip().lower()
    if "://" in domain:
        domain = urlparse(domain).hostname or ""
    domain = domain.split("/")[0]
    domain = domain.lstrip(".").rstrip(".")
    return domain


def normalize_domain_list(raw: str) -> list[str]:
    return [normalize_domain(part) for part in raw.split(",") if normalize_domain(part)]


def is_allowed_domain(domain: str, allowed: set[str] | list[str]) -> bool:
    allowed_set = set(allowed)
    if domain in allowed_set:
        return True
    return any(domain.endswith(f".{suffix}") for suffix in allowed_set if suffix)


def seed_url_for_domain(domain: str) -> str:
    return f"https://{domain}/"


def _is_private_ip(ip: ipaddress._BaseAddress) -> bool:
    if ip.version == 6 and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return any(ip in network for network in _PRIVATE_NETWORKS)


def hostname_resolves_to_private(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if _is_private_ip(ip):
            return True
    return False


def is_private_ip_literal(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return _is_private_ip(ip)


def validate_public_url(url: str) -> str:
    """Return the normalized URL if it is http(s) and resolves only to public IPs.

    Guards against crawling private IPs, localhost, internal network resources,
    cloud metadata endpoints, and link-local destinations — both at the URL
    level and for any resolved host (i.e. redirect destinations).
    """
    if not url or not isinstance(url, str):
        raise DiscoveryInvalidUrlError("URL must be a non-empty string.")
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise DiscoveryInvalidUrlError(f"URL '{_trim(url)}' must use http(s).")
    if not parsed.hostname:
        raise DiscoveryInvalidUrlError(f"URL '{_trim(url)}' has no host.")
    host = parsed.hostname.rstrip(".")
    if is_private_ip_literal(host):
        raise DiscoveryInvalidUrlError(f"URL '{_trim(url)}' targets a non-public address.")
    if hostname_resolves_to_private(host):
        raise DiscoveryInvalidUrlError(f"URL '{_trim(url)}' resolves to a non-public address.")
    if parsed.username or parsed.password:
        raise DiscoveryInvalidUrlError("URL must not contain embedded credentials.")
    return parsed.geturl()


def _trim(value: str, limit: int = 120) -> str:
    return value if len(value) <= limit else value[:limit] + "..."

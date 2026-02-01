from __future__ import annotations

from typing import Dict, Optional
from urllib.parse import urlparse
import socket
import ipaddress

import httpx

from app.core.config import settings
from app.core.errors import AppException, ErrorCodes


def _is_private_host(hostname: str) -> bool:
    """
    Mitigación SSRF básica: bloquea hosts que resuelven a IPs privadas/loopback/link-local.
    En entornos internos puedes habilitar ALLOW_PRIVATE_NETWORKS=true.
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
        for family, *_rest, sockaddr in infos:
            ip = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip)
            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_reserved
                or ip_obj.is_multicast
            ):
                return True
        return False
    except Exception:
        return True


def _default_headers(url: str) -> Dict[str, str]:
    # “Agente” tipo browser: ayuda con sitios que bloquean clients “vacíos”
    p = urlparse(url)
    origin = f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else ""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": origin or "",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }


async def fetch_image_bytes(image_url: str, extra_headers: Optional[Dict[str, str]] = None) -> bytes:
    if not image_url or not image_url.strip():
        raise AppException(400, ErrorCodes.OCR_FETCH_400, "Invalid request", "image_url es requerido")

    url = image_url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise AppException(400, ErrorCodes.OCR_FETCH_400, "Invalid URL", "Solo se permite http/https")

    if not parsed.netloc:
        raise AppException(400, ErrorCodes.OCR_FETCH_400, "Invalid URL", "URL inválida (sin host)")

    if not settings.allow_private_networks and _is_private_host(parsed.hostname or ""):
        raise AppException(
            400,
            ErrorCodes.OCR_FETCH_400,
            "Invalid URL",
            "El host resuelve a una red privada/loopback (bloqueado por seguridad)",
        )

    headers = _default_headers(url)
    if extra_headers:
        # Permite que el caller pase cookies/token/referer custom si una web es especial.
        headers.update({str(k): str(v) for k, v in extra_headers.items()})

    timeout = httpx.Timeout(settings.fetch_timeout_seconds, connect=10.0)
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            limits=limits,
            max_redirects=settings.fetch_max_redirects,
        ) as client:
            async with client.stream("GET", url, headers=headers) as resp:
                if resp.status_code >= 400:
                    raise AppException(
                        502,
                        ErrorCodes.OCR_FETCH_502,
                        "Upstream fetch failed",
                        f"No se pudo descargar la imagen (status {resp.status_code})",
                    )

                ctype = (resp.headers.get("content-type") or "").lower()
                if "image" not in ctype:
                    raise AppException(
                        400,
                        ErrorCodes.OCR_FETCH_400,
                        "Invalid content",
                        "La URL no parece apuntar a una imagen (content-type no es image/*)",
                    )

                # Si content-length ya excede, corta rápido
                clen = resp.headers.get("content-length")
                if clen and clen.isdigit() and int(clen) > settings.max_bytes:
                    raise AppException(
                        413,
                        ErrorCodes.OCR_TOO_LARGE_413,
                        "Payload too large",
                        f"La imagen excede {settings.max_file_mb}MB",
                    )

                chunks = []
                total = 0
                async for chunk in resp.aiter_bytes(chunk_size=64 * 1024):
                    total += len(chunk)
                    if total > settings.max_bytes:
                        raise AppException(
                            413,
                            ErrorCodes.OCR_TOO_LARGE_413,
                            "Payload too large",
                            f"La imagen excede {settings.max_file_mb}MB",
                        )
                    chunks.append(chunk)

                return b"".join(chunks)

    except AppException:
        raise
    except httpx.RequestError as e:
        raise AppException(
            502,
            ErrorCodes.OCR_FETCH_502,
            "Upstream fetch failed",
            f"Error descargando la imagen: {str(e)}",
        )
"""Object storage (R2/S3-compatible): presigned audio URLs.

Presigning is local HMAC — no network call — so this is fully testable with
dummy credentials. The mobile client asks the API for a short-lived URL and
hands it straight to the audio player.
"""

import hashlib
import hmac
import time
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import boto3
from botocore.config import Config
from katha_core.config import settings

AUDIO_URL_TTL_SECONDS = 600


def _r2_configured() -> bool:
    s = settings()
    return bool(s.r2_endpoint and s.r2_access_key_id and s.r2_secret_access_key)


def _local_dir() -> Path | None:
    d = settings().local_audio_dir
    return Path(d).resolve() if d else None


def configured() -> bool:
    """Audio can be served if either the cloud bucket (R2) or a local recordings
    directory is set. R2 wins when both are present."""
    return _r2_configured() or _local_dir() is not None


# --- Local dev backend: HMAC-signed, short-lived links to real recordings ----


def _sign(key: str, exp: int) -> str:
    msg = f"{key}:{exp}".encode()
    return hmac.new(settings().audio_sign_secret.encode(), msg, hashlib.sha256).hexdigest()


def verify_local(key: str, exp: int, sig: str) -> bool:
    """A local audio link is valid only if unexpired and signed by us."""
    if exp < int(time.time()):
        return False
    return hmac.compare_digest(sig, _sign(key, exp))


def _resolve_local(key: str) -> Path | None:
    """Resolve a key under the audio dir, refusing anything that escapes it."""
    d = _local_dir()
    if d is None:
        return None
    p = (d / key).resolve()
    try:
        p.relative_to(d)
    except ValueError:
        return None  # path traversal attempt
    return p


def local_audio_path(key: str) -> Path | None:
    p = _resolve_local(key)
    return p if (p is not None and p.is_file()) else None


@lru_cache
def _client():
    s = settings()
    return boto3.client(
        "s3",
        endpoint_url=s.r2_endpoint,
        aws_access_key_id=s.r2_access_key_id,
        aws_secret_access_key=s.r2_secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def presigned_audio_url(audio_key: str) -> str:
    if _r2_configured():
        return _client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings().r2_bucket, "Key": audio_key},
            ExpiresIn=AUDIO_URL_TTL_SECONDS,
        )
    # Local dev: a short-lived signed link the /audio-file route will honour.
    exp = int(time.time()) + AUDIO_URL_TTL_SECONDS
    base = settings().public_base_url.rstrip("/")
    return f"{base}/audio-file/{quote(audio_key)}?exp={exp}&sig={_sign(audio_key, exp)}"


def delete_audio(audio_key: str) -> None:
    if _r2_configured():
        _client().delete_object(Bucket=settings().r2_bucket, Key=audio_key)
        return
    p = _resolve_local(audio_key)
    if p is not None and p.is_file():
        p.unlink()


def reset() -> None:
    """Tests re-point credentials."""
    _client.cache_clear()

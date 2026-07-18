"""Object storage (R2/S3-compatible): presigned audio URLs.

Presigning is local HMAC — no network call — so this is fully testable with
dummy credentials. The mobile client asks the API for a short-lived URL and
hands it straight to the audio player.
"""

from functools import lru_cache

import boto3
from botocore.config import Config
from katha_core.config import settings

AUDIO_URL_TTL_SECONDS = 600


def configured() -> bool:
    s = settings()
    return bool(s.r2_endpoint and s.r2_access_key_id and s.r2_secret_access_key)


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
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings().r2_bucket, "Key": audio_key},
        ExpiresIn=AUDIO_URL_TTL_SECONDS,
    )


def reset() -> None:
    """Tests re-point credentials."""
    _client.cache_clear()

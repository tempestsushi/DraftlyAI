from __future__ import annotations

import base64
import re
from uuid import uuid4

import requests

from ...config import settings

DATA_URL_PATTERN = re.compile(r"^data:(?P<mime>[-\w.+/]+)(?:;charset=[-\w.]+)?;base64,(?P<data>.+)$", re.S)
EXTENSIONS_BY_MIME = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


def persist_generated_image_url(image_url: str, *, provider: str) -> str:
    if not image_url.startswith("data:"):
        return image_url
    if not settings.supabase_image_bucket:
        raise ValueError("SUPABASE_IMAGE_BUCKET is required to persist generated images")
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required to persist generated images")

    content_type, raw_bytes = _decode_data_url(image_url)
    extension = EXTENSIONS_BY_MIME.get(content_type, "bin")
    object_path = f"generated/{provider}/{uuid4().hex}.{extension}"
    upload_url = (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/"
        f"{settings.supabase_image_bucket}/{object_path}"
    )
    response = requests.post(
        upload_url,
        headers={
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "apikey": settings.supabase_service_role_key,
            "Content-Type": content_type,
            "x-upsert": "false",
        },
        data=raw_bytes,
        timeout=settings.image_storage_timeout_seconds,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:500]
        raise ValueError(f"Supabase image upload failed: {detail}") from exc
    return (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
        f"{settings.supabase_image_bucket}/{object_path}"
    )


def _decode_data_url(image_url: str) -> tuple[str, bytes]:
    match = DATA_URL_PATTERN.match(image_url)
    if not match:
        raise ValueError("Generated image was not a valid base64 data URL")
    content_type = match.group("mime")
    try:
        return content_type, base64.b64decode(match.group("data"), validate=True)
    except ValueError as exc:
        raise ValueError("Generated image data URL could not be decoded") from exc

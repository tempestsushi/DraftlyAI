from __future__ import annotations

import secrets
import hashlib
import re
from datetime import timedelta
from urllib.parse import urlparse, urlencode

import requests

from ..config import settings
from ..models import (
    DraftImageRecord,
    DraftRecord,
    DraftStatus,
    IntegrationStatus,
    LinkedInAccountRecord,
    LinkedInPublishResponse,
    LinkedInStatusResponse,
    LogSource,
    utc_now,
)
from ..store import Store

AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
ACCESS_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/rest/posts"
URL_PATTERN = re.compile(r"https?://[^\s<>)\]]+")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def build_connect_url(store: Store) -> str:
    if not settings.linkedin_client_id or not settings.linkedin_client_secret:
        raise ValueError("LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET are required")

    state = secrets.token_urlsafe(32)
    store.create_linkedin_oauth_state(state, utc_now() + timedelta(minutes=10))
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.linkedin_client_id,
            "redirect_uri": settings.linkedin_redirect_uri,
            "state": state,
            "scope": settings.linkedin_scope,
        }
    )
    return f"{AUTHORIZATION_URL}?{query}"


def complete_oauth_callback(store: Store, *, code: str, state: str) -> LinkedInAccountRecord:
    oauth_state = store.consume_linkedin_oauth_state(state)
    if oauth_state is None or oauth_state.expires_at < utc_now():
        raise ValueError("LinkedIn sign-in state is invalid or expired")

    token_payload = _exchange_code_for_token(code)
    access_token = str(token_payload["access_token"])
    profile = _fetch_userinfo(access_token)
    now = utc_now()
    expires_in = int(token_payload.get("expires_in") or 0)
    refresh_expires_in = int(token_payload.get("refresh_token_expires_in") or 0)
    account = LinkedInAccountRecord(
        provider_user_id=_optional_string(profile.get("sub")),
        name=_optional_string(profile.get("name")),
        email=_optional_string(profile.get("email")),
        picture_url=_optional_string(profile.get("picture")),
        access_token=access_token,
        refresh_token=_optional_string(token_payload.get("refresh_token")),
        scope=_optional_string(token_payload.get("scope")) or settings.linkedin_scope,
        expires_at=now + timedelta(seconds=expires_in) if expires_in else None,
        refresh_expires_at=now + timedelta(seconds=refresh_expires_in) if refresh_expires_in else None,
        connected_at=now,
        updated_at=now,
    )
    saved = store.save_linkedin_account(account)
    store.update_integration("linkedin-publish", status=IntegrationStatus.connected, connected_at=saved.connected_at)
    return saved


def get_linkedin_status(store: Store) -> LinkedInStatusResponse:
    account = store.get_linkedin_account()
    if account is None:
        return LinkedInStatusResponse(connected=False)
    return LinkedInStatusResponse(
        connected=True,
        name=account.name,
        email=account.email,
        picture_url=account.picture_url,
        connected_at=account.connected_at,
        expires_at=account.expires_at,
    )


def disconnect_linkedin(store: Store) -> LinkedInStatusResponse:
    store.delete_linkedin_account()
    return LinkedInStatusResponse(connected=False)


def publish_draft(store: Store, draft_id: str) -> LinkedInPublishResponse:
    draft = store.get_draft(draft_id)
    if draft is None:
        return LinkedInPublishResponse(
            ok=False,
            status="failed",
            draft_id=draft_id,
            message="Draft not found",
        )

    account = store.get_linkedin_account()
    if account is None:
        return LinkedInPublishResponse(
            ok=False,
            status="failed",
            draft_id=draft_id,
            message="LinkedIn is not connected",
        )
    if account.expires_at and account.expires_at <= utc_now():
        return LinkedInPublishResponse(
            ok=False,
            status="failed",
            draft_id=draft_id,
            message="LinkedIn access token expired. Reconnect LinkedIn in Settings.",
        )
    if not account.provider_user_id:
        return LinkedInPublishResponse(
            ok=False,
            status="failed",
            draft_id=draft_id,
            message="LinkedIn account ID is missing. Reconnect LinkedIn in Settings.",
        )

    content, preview_url, link_stats = _build_publish_content(store, draft)
    if not content:
        return LinkedInPublishResponse(
            ok=False,
            status="failed",
            draft_id=draft_id,
            message="Draft content is empty. Save the draft before posting.",
        )
    if len(content) > settings.linkedin_post_char_limit:
        return LinkedInPublishResponse(
            ok=False,
            status="failed",
            draft_id=draft_id,
            message=(
                f"Draft is {len(content)} characters, which is over the configured LinkedIn post limit "
                f"of {settings.linkedin_post_char_limit}. Shorten it before posting."
            ),
        )

    store.add_log(draft.topic_id, LogSource.linkedin, _format_publish_content_log(content))
    if link_stats:
        store.add_log(draft.topic_id, LogSource.linkedin, link_stats)
    post_urn = _publish_with_optional_preview(store, draft, account, content, preview_url)
    post_url = f"https://www.linkedin.com/feed/update/{post_urn}"
    store.update_draft_status(draft_id, status=DraftStatus.published, linkedin_post_url=post_url)
    store.add_log(draft.topic_id, LogSource.linkedin, f"LinkedIn post published ({len(content)} chars)")
    updated = store.get_draft(draft_id)
    return LinkedInPublishResponse(
        ok=True,
        status="published",
        draft_id=draft_id,
        published_at=updated.posted_at if updated else None,
        linkedin_post_url=post_url,
        message="Draft published to LinkedIn.",
    )


def _exchange_code_for_token(code: str) -> dict:
    response = requests.post(
        ACCESS_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
            "redirect_uri": settings.linkedin_redirect_uri,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("access_token"):
        raise ValueError("LinkedIn token response did not include an access token")
    return payload


def _fetch_userinfo(access_token: str) -> dict:
    response = requests.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _publish_with_optional_preview(
    store: Store,
    draft: DraftRecord,
    account: LinkedInAccountRecord,
    content: str,
    preview_url: str | None,
) -> str:
    if settings.linkedin_article_preview_enabled and preview_url:
        try:
            store.add_log(draft.topic_id, LogSource.linkedin, f"LinkedIn article preview requested: {preview_url}")
            return _create_linkedin_post(account, content, preview_url=preview_url)
        except requests.HTTPError as exc:
            store.add_log(
                draft.topic_id,
                LogSource.linkedin,
                f"LinkedIn article preview failed ({exc.response.status_code}); retrying text-only post",
            )
    return _create_linkedin_post(account, content)


def _create_linkedin_post(
    account: LinkedInAccountRecord,
    content: str,
    *,
    preview_url: str | None = None,
) -> str:
    payload = {
        "author": f"urn:li:person:{account.provider_user_id}",
        "commentary": content,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if preview_url:
        payload["content"] = {"article": {"source": preview_url}}
    response = requests.post(
        POSTS_URL,
        headers={
            "Authorization": f"Bearer {account.access_token}",
            "Content-Type": "application/json",
            "Linkedin-Version": settings.linkedin_api_version,
            "X-Restli-Protocol-Version": "2.0.0",
        },
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    post_urn = response.headers.get("x-restli-id")
    if not post_urn:
        raise ValueError("LinkedIn publish response did not include a post id")
    return post_urn


def _build_publish_content(store: Store, draft: DraftRecord) -> tuple[str, str | None, str]:
    base_content = _normalize_markdown_links(draft.content.strip())
    images = store.list_draft_images(draft.id)
    urls, skipped = _public_attachment_urls(images)
    existing_urls = _extract_urls(base_content)
    existing_url_set = set(existing_urls)
    new_urls = [url for url in urls if url not in existing_url_set]
    preview_url = _first_preview_url([*existing_urls, *new_urls])
    if not new_urls:
        return base_content, preview_url, _format_attachment_log(0, skipped)
    label = "Attached link" if len(new_urls) == 1 else "Attached links"
    attachment_block = "\n\n" + label + ":\n" + "\n".join(new_urls)
    return f"{base_content}{attachment_block}".strip(), preview_url, _format_attachment_log(len(new_urls), skipped)


def _normalize_markdown_links(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        label = re.sub(r"[*_`]", "", match.group(1)).strip()
        url = match.group(2).strip()
        if not label or _labels_same_url(label, url):
            return url
        return f"{label} ({url})"

    return MARKDOWN_LINK_PATTERN.sub(replace, text)


def _labels_same_url(label: str, url: str) -> bool:
    normalized_label = label.rstrip("/").lower()
    normalized_url = url.rstrip("/").lower()
    return normalized_label == normalized_url


def _public_attachment_urls(images: list[DraftImageRecord]) -> tuple[list[str], int]:
    urls: list[str] = []
    skipped = 0
    for image in images:
        if _is_public_url(image.image_url):
            urls.append(image.image_url.strip())
        elif _is_public_url(image.source_url) and not _is_provider_docs_url(image.source_url):
            urls.append(image.source_url.strip())
        else:
            skipped += 1
    deduped: list[str] = []
    for url in urls:
        if url not in deduped:
            deduped.append(url)
    return deduped, skipped


def _extract_urls(text: str) -> list[str]:
    return [match.group(0).rstrip(".,);]") for match in URL_PATTERN.finditer(text)]


def _first_preview_url(urls: list[str]) -> str | None:
    for url in urls:
        if _is_public_url(url) and not _is_image_url(url) and not _is_provider_docs_url(url):
            return url
    return None


def _is_public_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_provider_docs_url(value: str) -> bool:
    domain = urlparse(value).netloc.lower()
    path = urlparse(value).path.lower()
    provider_domains = {"ai.google.dev", "openrouter.ai"}
    return domain in provider_domains and ("image" in path or "docs" in path)


def _is_image_url(value: str) -> bool:
    path = urlparse(value).path.lower()
    return path.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"))


def _format_attachment_log(attached_count: int, skipped_count: int) -> str:
    if attached_count == 0 and skipped_count == 0:
        return ""
    parts = [f"public attachment links added: {attached_count}"]
    if skipped_count:
        parts.append(f"skipped non-public/generated attachment links: {skipped_count}")
    return "LinkedIn attachment handling: " + "; ".join(parts)


def _format_publish_content_log(content: str) -> str:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    normalized = " ".join(content.split())
    tail = normalized[-160:] if len(normalized) > 160 else normalized
    return (
        f"Publishing saved draft to LinkedIn ({len(content)} chars, sha256={digest})\n"
        f"Ending preview: {tail}"
    )


def _optional_string(value) -> str | None:
    return str(value) if value else None

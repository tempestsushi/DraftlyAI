from __future__ import annotations

import requests

from ...config import settings
from ...models import ImageResult, ImageUseCase
from .storage import persist_generated_image_url

GEMINI_IMAGE_MODEL_URL = "https://ai.google.dev/gemini-api/docs/image-generation"
OPENROUTER_IMAGE_API_URL = "https://openrouter.ai/api/v1/images"
OPENROUTER_IMAGE_DOCS_URL = "https://openrouter.ai/docs/guides/overview/multimodal/image-generation"
USE_CASE_DIRECTIONS = {
    ImageUseCase.linkedin_post_illustration: (
        "professional LinkedIn post illustration, clean modern composition, text-free, no logos"
    ),
    ImageUseCase.blog_hero: "wide blog hero image, editorial style, clean focal point, text-free, no logos",
    ImageUseCase.technical_concept: (
        "technical concept visual, abstract infographic composition, clean shapes, text-free"
    ),
    ImageUseCase.abstract_topic: "abstract conceptual image, polished, minimal, text-free, no logos",
    ImageUseCase.product_mockup: "product mockup style visual, modern interface-inspired composition, text-free, no logos",
}


def generate_images(
    prompt: str,
    *,
    use_case: ImageUseCase = ImageUseCase.linkedin_post_illustration,
    count: int = 4,
) -> list[ImageResult]:
    provider = settings.image_generation_provider
    if provider not in {"gemini", "openrouter"}:
        raise ValueError("IMAGE_GENERATION_PROVIDER must be either 'gemini' or 'openrouter'")

    safe_count = max(1, min(count, 1))
    results: list[ImageResult] = []
    for index in range(safe_count):
        generation_prompt = _build_generation_prompt(prompt, use_case)
        generated = (
            _run_openrouter_image(generation_prompt)
            if provider == "openrouter"
            else _run_gemini_image(generation_prompt)
        )
        generated["image_url"] = persist_generated_image_url(generated["image_url"], provider=generated["provider"])
        results.append(
            ImageResult(
                title=f"Generated {use_case.value.replace('_', ' ')} #{index + 1}",
                image_url=generated["image_url"],
                thumbnail_url=generated["image_url"],
                source_url=generated["source_url"],
                source_domain=generated["source_domain"],
                provider=generated["provider"],
                score=1,
            )
        )
    return results


def _build_generation_prompt(prompt: str, use_case: ImageUseCase) -> str:
    cleaned = " ".join(prompt.split())[:420]
    direction = USE_CASE_DIRECTIONS[use_case]
    concept_direction = _concept_visual_direction(cleaned, use_case)
    return (
        f"Create a polished {direction} about: {cleaned}. "
        f"{concept_direction} "
        "Use simple geometric objects, subtle depth, soft lighting, high contrast, and a clean 16:9 composition. "
        "Important: no readable text; do not render words, letters, numbers, captions, labels, UI text, watermarks, or logos. "
        "If the concept needs explanation, show it through icons, arrows, panels, layers, particles, and visual flow only."
    )[:2048]


def _concept_visual_direction(prompt: str, use_case: ImageUseCase) -> str:
    lowered = prompt.lower()
    if "text" in lowered and "image" in lowered or "prompt" in lowered and "image" in lowered:
        return (
            "Show a text prompt becoming an image as a visual pipeline: a glowing input card on the left, "
            "small token blocks moving into stacked neural-network layers, a latent/noise grid transforming through "
            "several denoising stages, and a finished picture frame on the right. Use arrows and visual symbols only."
        )
    if "token" in lowered or "transformer" in lowered or "model" in lowered:
        return (
            "Show the idea as an AI processing pipeline with small blocks entering layered model modules, "
            "attention-like connections, data particles, and a final output panel. Keep every panel symbolic and unlabeled."
        )
    if use_case == ImageUseCase.product_mockup:
        return "Show a clean product-style scene with abstract interface panels and realistic device-like surfaces."
    return "Show the topic as a clear metaphorical scene with an obvious beginning, processing middle, and useful result."


def _run_gemini_image(prompt: str) -> dict[str, str]:
    if not settings.gemini_image_api_key:
        raise ValueError("GEMINI_API_KEY_2 is required for Gemini image generation")

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        headers={
            "x-goog-api-key": settings.gemini_image_api_key or "",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.gemini_image_model,
            "input": prompt,
            "response_format": {
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": settings.gemini_image_aspect_ratio,
                "image_size": settings.gemini_image_size,
            },
        },
        timeout=settings.image_generation_timeout_seconds,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:500]
        if response.status_code == 403:
            raise ValueError(
                "Gemini rejected the request. Check that GEMINI_API_KEY_2 is a valid Google AI Studio API key "
                "and that the Gemini API is enabled for that key."
            ) from exc
        raise ValueError(f"Gemini image generation request failed: {detail}") from exc
    payload = response.json()
    image = _extract_gemini_image(payload)
    if not image:
        raise ValueError("Gemini image generation response did not include an image")
    return {
        "image_url": f"data:image/jpeg;charset=utf-8;base64,{image}",
        "source_url": GEMINI_IMAGE_MODEL_URL,
        "source_domain": "ai.google.dev",
        "provider": "gemini-image",
    }


def _run_openrouter_image(prompt: str) -> dict[str, str]:
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is required for OpenRouter image generation")
    if not settings.openrouter_image_model:
        raise ValueError("OPENROUTER_IMAGE_MODEL is required for OpenRouter image generation")

    payload: dict[str, object] = {
        "model": settings.openrouter_image_model,
        "prompt": prompt,
    }
    if settings.openrouter_image_size:
        payload["size"] = settings.openrouter_image_size
    if settings.openrouter_image_aspect_ratio:
        payload["aspect_ratio"] = settings.openrouter_image_aspect_ratio

    response = requests.post(
        OPENROUTER_IMAGE_API_URL,
        headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        },
        json=payload,
        timeout=settings.image_generation_timeout_seconds,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:500]
        raise ValueError(f"OpenRouter image generation request failed: {detail}") from exc

    image_url = _extract_openrouter_image(response.json())
    if not image_url:
        raise ValueError("OpenRouter image generation response did not include an image")
    return {
        "image_url": image_url,
        "source_url": OPENROUTER_IMAGE_DOCS_URL,
        "source_domain": "openrouter.ai",
        "provider": "openrouter-image",
    }


def _extract_openrouter_image(payload: dict) -> str | None:
    data = payload.get("data")
    if not isinstance(data, list):
        return None
    for item in data:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("image_url") or item.get("imageUrl")
        if isinstance(url, str) and url:
            return url
        b64_json = item.get("b64_json") or item.get("b64Json")
        if isinstance(b64_json, str) and b64_json:
            media_type = item.get("media_type") or item.get("mediaType") or "image/png"
            return f"data:{media_type};charset=utf-8;base64,{b64_json}"
    return None


def _extract_gemini_image(payload: dict) -> str | None:
    direct = payload.get("output_image") or payload.get("outputImage")
    if isinstance(direct, dict):
        data = direct.get("data") or direct.get("image")
        if isinstance(data, str) and data:
            return data

    for key in ("output", "outputs", "candidates", "steps"):
        found = _find_image_data(payload.get(key))
        if found:
            return found
    return _find_image_data(payload)


def _find_image_data(value) -> str | None:
    if isinstance(value, list):
        for item in value:
            found = _find_image_data(item)
            if found:
                return found
    if isinstance(value, dict):
        if value.get("type") in {"image", "inline_data", "inlineData"}:
            data = value.get("data")
            if isinstance(data, str) and data:
                return data
        inline_data = value.get("inline_data") or value.get("inlineData")
        if isinstance(inline_data, dict):
            data = inline_data.get("data")
            if isinstance(data, str) and data:
                return data
        for nested in value.values():
            found = _find_image_data(nested)
            if found:
                return found
    return None

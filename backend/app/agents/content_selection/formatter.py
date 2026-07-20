from __future__ import annotations

from urllib.parse import urlparse

from .models import SelectedContext


def format_selected_context(context: SelectedContext) -> str:
    if not context.selected_items:
        return "No useful external source material was selected. Answer cautiously and avoid unsupported current claims."

    lines = [f"Evidence for: {context.topic}", ""]
    for index, item in enumerate(context.selected_items, start=1):
        supporting = ", ".join(_source_label(source_id) for source_id in item.supporting_source_ids)
        source_label = item.source_title or _source_label(item.source_url or item.primary_source_id)
        if supporting and supporting != item.primary_source_id:
            source_label = f"{source_label}; supporting: {supporting}"
        lines.append(f"[Idea {index}] {item.text}")
        lines.append(f"Sources: {source_label}")
        lines.append("")
    return "\n".join(lines).strip()


def _source_label(value: str) -> str:
    parsed = urlparse(value)
    if parsed.netloc:
        return parsed.netloc.replace("www.", "")
    return value

from __future__ import annotations

from ...agents import AgentIntent
from ...models import ResearchDepth


def should_update_conversation_summary(
    research_depth: ResearchDepth,
    decision: AgentIntent,
    user_message_count: int,
) -> bool:
    if decision != AgentIntent.research:
        return True
    if research_depth != ResearchDepth.quick:
        return True
    return user_message_count > 0 and user_message_count % 5 == 0

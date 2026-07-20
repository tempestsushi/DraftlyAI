from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class TopicStatus(str, Enum):
    pending = "pending"
    searching = "searching"
    drafting = "drafting"
    review = "review"
    complete = "complete"
    error = "error"


class ResearchDepth(str, Enum):
    quick = "quick"
    moderate = "moderate"
    deep = "deep"


class LogSource(str, Enum):
    ollama = "ollama"
    web_search = "web_search"
    web_fetch = "web_fetch"
    linkedin = "linkedin"
    system = "system"


class DraftStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    published = "published"


class IntegrationStatus(str, Enum):
    connected = "connected"
    disconnected = "disconnected"
    active = "active"
    inactive = "inactive"


class TopicRecord(BaseModel):
    id: str = Field(default_factory=new_id)
    topic: str
    status: TopicStatus = TopicStatus.pending
    response_content: str | None = None
    conversation_summary: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class MessageRecord(BaseModel):
    id: str = Field(default_factory=new_id)
    topic_id: str
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class MessageSourceRecord(BaseModel):
    id: str = Field(default_factory=new_id)
    topic_id: str
    message_id: str
    title: str
    url: str
    domain: str | None = None
    snippet: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class TerminalLogRecord(BaseModel):
    id: str = Field(default_factory=new_id)
    topic_id: str | None = None
    source: LogSource
    message: str
    created_at: datetime = Field(default_factory=utc_now)


class DraftRecord(BaseModel):
    id: str = Field(default_factory=new_id)
    topic_id: str | None = None
    source_message_id: str | None = None
    title: str
    content: str
    source: Literal["research"] = "research"
    status: DraftStatus = DraftStatus.pending
    linkedin_post_url: str | None = None
    posted_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DraftVersionRecord(BaseModel):
    id: str = Field(default_factory=new_id)
    draft_id: str
    version_number: int
    content: str
    reason: Literal["created", "edited", "regenerated"] = "edited"
    created_at: datetime = Field(default_factory=utc_now)


class DraftImageRecord(BaseModel):
    id: str = Field(default_factory=new_id)
    draft_id: str
    topic_id: str | None = None
    title: str
    image_url: str
    thumbnail_url: str | None = None
    source_url: str
    source_domain: str | None = None
    provider: str = "gemini-image"
    width: int | None = None
    height: int | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ImageResult(BaseModel):
    title: str
    image_url: str
    thumbnail_url: str | None = None
    source_url: str
    source_domain: str | None = None
    provider: str = "gemini-image"
    width: int | None = None
    height: int | None = None
    score: float = 0


class ImageUseCase(str, Enum):
    linkedin_post_illustration = "linkedin_post_illustration"
    blog_hero = "blog_hero"
    technical_concept = "technical_concept"
    abstract_topic = "abstract_topic"
    product_mockup = "product_mockup"


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=500)
    use_case: ImageUseCase = ImageUseCase.linkedin_post_illustration
    count: int = Field(default=1, ge=1, le=1)


class DraftTone(str, Enum):
    professional = "professional"
    casual = "casual"
    thought_leadership = "thought_leadership"


class DraftLength(str, Enum):
    short = "short"
    medium = "medium"
    long = "long"


class IntegrationRecord(BaseModel):
    id: str = Field(default_factory=new_id)
    type: Literal["linkedin_publish"]
    name: str
    status: IntegrationStatus
    connected_at: datetime | None = None


class LinkedInAccountRecord(BaseModel):
    id: str = "primary"
    provider_user_id: str | None = None
    name: str | None = None
    email: str | None = None
    picture_url: str | None = None
    access_token: str
    refresh_token: str | None = None
    scope: str | None = None
    expires_at: datetime | None = None
    refresh_expires_at: datetime | None = None
    connected_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class LinkedInOAuthStateRecord(BaseModel):
    state: str
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime


class AgentStreamPayload(BaseModel):
    topic: str
    topic_id: str | None = None
    research_depth: ResearchDepth = ResearchDepth.moderate


class RagEvaluationRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=500)
    research_depth: ResearchDepth = ResearchDepth.moderate
    include_responses: bool = True


class LinkedInPublishRequest(BaseModel):
    draft_id: str
    content: str | None = None


class DraftUpdateRequest(BaseModel):
    content: str | None = None
    status: DraftStatus | None = None
    clear_linkedin_post: bool = False


class DraftRegenerateRequest(BaseModel):
    tone: DraftTone = DraftTone.professional
    length: DraftLength = DraftLength.medium
    include_cta: bool = True
    include_hashtags: bool = True


class DraftImageSaveRequest(BaseModel):
    title: str
    image_url: str
    thumbnail_url: str | None = None
    source_url: str
    source_domain: str | None = None
    provider: str = "gemini-image"
    width: int | None = None
    height: int | None = None


class IntegrationUpdateRequest(BaseModel):
    status: IntegrationStatus
    connected_at: datetime | None = None


class TopicDraftRequest(BaseModel):
    title: str | None = None
    message_id: str | None = None
    tone: DraftTone = DraftTone.professional
    length: DraftLength = DraftLength.medium
    include_cta: bool = True
    include_hashtags: bool = True


class MessageUpdateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=300)


class LinkedInPublishResponse(BaseModel):
    ok: bool
    status: Literal["published", "failed"]
    draft_id: str
    published_at: datetime | None = None
    linkedin_post_url: str | None = None
    message: str


class LinkedInStatusResponse(BaseModel):
    connected: bool
    name: str | None = None
    email: str | None = None
    picture_url: str | None = None
    connected_at: datetime | None = None
    expires_at: datetime | None = None

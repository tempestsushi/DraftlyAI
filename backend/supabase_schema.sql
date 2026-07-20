create table if not exists public.topics (
    id text primary key,
    topic text not null,
    status text not null,
    response_content text null,
    conversation_summary text null,
    created_at timestamptz not null,
    updated_at timestamptz not null
);

create table if not exists public.messages (
    id text primary key,
    topic_id text not null references public.topics(id) on delete cascade,
    role text not null,
    content text not null,
    created_at timestamptz not null
);

create index if not exists messages_topic_created_idx on public.messages(topic_id, created_at);

create table if not exists public.message_sources (
    id text primary key,
    topic_id text not null references public.topics(id) on delete cascade,
    message_id text not null references public.messages(id) on delete cascade,
    title text not null,
    url text not null,
    domain text null,
    snippet text null,
    created_at timestamptz not null
);

create index if not exists message_sources_topic_created_idx on public.message_sources(topic_id, created_at);

create table if not exists public.logs (
    id text primary key,
    topic_id text null references public.topics(id) on delete cascade,
    source text not null,
    message text not null,
    created_at timestamptz not null
);

create index if not exists logs_topic_created_idx on public.logs(topic_id, created_at);

create table if not exists public.drafts (
    id text primary key,
    topic_id text null references public.topics(id) on delete set null,
    source_message_id text null references public.messages(id) on delete set null,
    title text not null,
    content text not null,
    source text not null,
    status text not null,
    linkedin_post_url text null,
    posted_at timestamptz null,
    created_at timestamptz not null,
    updated_at timestamptz not null
);

create index if not exists drafts_topic_created_idx on public.drafts(topic_id, created_at);

create table if not exists public.draft_versions (
    id text primary key,
    draft_id text not null references public.drafts(id) on delete cascade,
    version_number integer not null,
    content text not null,
    reason text not null,
    created_at timestamptz not null,
    unique (draft_id, version_number)
);

create index if not exists draft_versions_draft_version_idx on public.draft_versions(draft_id, version_number desc);

create table if not exists public.draft_images (
    id text primary key,
    draft_id text not null references public.drafts(id) on delete cascade,
    topic_id text null references public.topics(id) on delete set null,
    title text not null,
    image_url text not null,
    thumbnail_url text null,
    source_url text not null,
    source_domain text null,
    provider text not null,
    width integer null,
    height integer null,
    created_at timestamptz not null,
    unique (draft_id, image_url)
);

create index if not exists draft_images_draft_created_idx on public.draft_images(draft_id, created_at);

create table if not exists public.integrations (
    id text primary key,
    type text not null unique,
    name text not null,
    status text not null,
    connected_at timestamptz null
);

insert into public.integrations (id, type, name, status, connected_at)
values ('linkedin-publish', 'linkedin_publish', 'LinkedIn Publishing', 'disconnected', null)
on conflict (type) do nothing;

create table if not exists public.linkedin_accounts (
    id text primary key,
    provider_user_id text null,
    name text null,
    email text null,
    picture_url text null,
    access_token text not null,
    refresh_token text null,
    scope text null,
    expires_at timestamptz null,
    refresh_expires_at timestamptz null,
    connected_at timestamptz not null,
    updated_at timestamptz not null
);

create table if not exists public.linkedin_oauth_states (
    state text primary key,
    created_at timestamptz not null,
    expires_at timestamptz not null
);

create index if not exists linkedin_oauth_states_expires_idx on public.linkedin_oauth_states(expires_at);

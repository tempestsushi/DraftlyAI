from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

from app.main import app
from tests.fake_store import InMemoryStore


def _swap_store(test_store: InMemoryStore) -> None:
    import app.main as main_module
    import app.routes.agent as agent_routes
    import app.routes.drafts as drafts_routes
    import app.routes.images as images_routes
    import app.routes.integrations as integrations_routes
    import app.routes.linkedin as linkedin_routes
    import app.routes.logs as logs_routes
    import app.routes.topics as topics_routes
    import app.services.linkedin as linkedin_service

    main_module.store = test_store
    agent_routes.store = test_store
    drafts_routes.store = test_store
    images_routes.store = test_store
    integrations_routes.store = test_store
    linkedin_routes.store = test_store
    logs_routes.store = test_store
    topics_routes.store = test_store
    linkedin_service.store = test_store


@pytest.fixture
def test_store() -> InMemoryStore:
    store = InMemoryStore()
    store.initialize()
    _swap_store(store)
    return store


@pytest.fixture
def client(test_store: InMemoryStore) -> TestClient:
    _ = test_store
    with TestClient(app) as test_client:
        yield test_client

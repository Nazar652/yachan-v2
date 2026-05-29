from fastapi.testclient import TestClient

from src import create_app


def test_protected_mod_endpoint_requires_auth():
    client = TestClient(create_app())
    response = client.get("/api/mod/reports")
    assert response.status_code == 401


def test_app_registers_expected_routes():
    app = create_app()
    paths = {getattr(route, "path", None) for route in app.routes}

    assert "/api/boards" in paths
    assert "/api/boards/{slug}" in paths
    assert "/api/{board_slug}/threads" in paths
    assert "/api/{board_slug}/threads/{thread_id}" in paths
    assert "/api/{board_slug}/threads/{thread_id}/posts" in paths
    assert "/api/{board_slug}/posts/{post_number}" in paths
    assert "/api/{board_slug}/posts/{post_number}/history" in paths
    assert "/api/{board_slug}/posts/{post_number}/report" in paths
    assert "/api/{board_slug}/posts/{post_number}/attachments" in paths
    assert "/api/captcha" in paths
    assert "/api/mod/login" in paths
    assert "/api/mod/boards" in paths

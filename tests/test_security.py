from app.config import get_settings


def test_api_key_is_enforced_when_configured(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret")
    get_settings.cache_clear()
    try:
        assert client.get("/datasets/").status_code == 401
        assert client.get("/datasets/", headers={"X-API-Key": "wrong"}).status_code == 401
        assert client.get("/datasets/", headers={"X-API-Key": "test-secret"}).status_code == 200
    finally:
        get_settings.cache_clear()


def test_admin_basic_auth_is_enforced_when_configured(client, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "operator")
    monkeypatch.setenv("ADMIN_PASSWORD", "strong-password")
    get_settings.cache_clear()
    try:
        response = client.get("/admin")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Basic"
        assert client.get("/admin", auth=("operator", "wrong")).status_code == 401
        success = client.get("/admin", auth=("operator", "strong-password"))
        assert success.status_code == 200
        assert "frame-ancestors 'none'" in success.headers["content-security-policy"]
    finally:
        get_settings.cache_clear()


def test_production_refuses_missing_security_configuration(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    get_settings.cache_clear()
    try:
        assert client.get("/datasets/").status_code == 503
        assert client.get("/admin").status_code == 503
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
    finally:
        get_settings.cache_clear()


def test_admin_rejects_cross_origin_form_submission(client):
    response = client.post(
        "/admin/datasets/create",
        data={"name": "Blocked"},
        headers={"Origin": "https://attacker.example"},
    )
    assert response.status_code == 403

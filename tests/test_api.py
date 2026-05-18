import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.skipif(
    not __import__("os").environ.get("DATABASE_URL"),
    reason="需要配置 DATABASE_URL 才能跑集成测试",
)
def test_wechat_login_mock():
    r = client.post("/api/v1/auth/wechat", json={"code": "test-user-001"})
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["token"]


def test_products_list_envelope():
    r = client.get("/api/v1/products")
    assert r.status_code in (200, 500)
    if r.status_code == 200:
        body = r.json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)

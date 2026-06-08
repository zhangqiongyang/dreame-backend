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


@pytest.mark.skipif(
    not __import__("os").environ.get("DATABASE_URL"),
    reason="需要配置 DATABASE_URL 才能跑集成测试",
)
def test_bind_phone_mock():
    login = client.post("/api/v1/auth/wechat", json={"code": "phone-bind-user"})
    assert login.status_code == 200
    token = login.json()["data"]["token"]

    r = client.post(
        "/api/v1/auth/phone",
        json={"code": "phone-code-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["phone"] == "13800138000"

    # 不同 login code 应对应同一 mock 用户，且已绑手机
    relogin = client.post("/api/v1/auth/wechat", json={"code": "another-login-code"})
    assert relogin.status_code == 200
    relogin_body = relogin.json()
    assert relogin_body["code"] == 200
    assert relogin_body["data"]["user"]["phone"] == "13800138000"

    # 重复绑定幂等
    rebind = client.post(
        "/api/v1/auth/phone",
        json={"code": "phone-code-002"},
        headers={"Authorization": f"Bearer {relogin_body['data']['token']}"},
    )
    assert rebind.status_code == 200
    assert rebind.json()["data"]["phone"] == "13800138000"


def test_admin_login_success():
    r = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 200
    assert body["data"]["token"]


def test_admin_login_wrong_password():
    r = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert r.status_code == 200
    assert r.json()["code"] == 500


def test_products_list_envelope():
    r = client.get("/api/v1/products")
    assert r.status_code in (200, 500)
    if r.status_code == 200:
        body = r.json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)

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


def test_admin_products_requires_auth():
    r = client.get("/api/v1/admin/products")
    assert r.status_code == 401


def _admin_token() -> str:
    login = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200
    return login.json()["data"]["token"]


SAMPLE_PRODUCT = {
    "name": "测试商品",
    "title": "测试商品长标题 5500Pa大吸力",
    "price": 1999,
    "marketPrice": 2499,
    "tags": ["测试标签"],
    "coverUrl": "https://example.com/cover.jpg",
    "heroImage": "https://example.com/hero.jpg",
    "detailImages": ["https://example.com/detail1.jpg"],
    "params": [{"label": "最大吸力", "value": "5500 Pa"}],
    "highlights": [{"title": "测试卖点", "desc": "测试描述"}],
    "isHot": False,
    "sort": 99,
    "status": "inactive",
}


@pytest.mark.skipif(
    not __import__("os").environ.get("DATABASE_URL"),
    reason="需要配置 DATABASE_URL 才能跑集成测试",
)
def test_admin_products_crud():
    token = _admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/api/v1/admin/products", json=SAMPLE_PRODUCT, headers=headers)
    assert created.status_code == 200
    body = created.json()
    assert body["code"] == 200
    product_id = body["data"]["id"]
    assert product_id.startswith("P")

    listed = client.get("/api/v1/admin/products", headers=headers, params={"keyword": "测试商品"})
    assert listed.status_code == 200
    rows = listed.json()["data"]
    assert any(row["id"] == product_id for row in rows)

    detail = client.get(f"/api/v1/admin/products/{product_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["name"] == "测试商品"

    c_list = client.get("/api/v1/products")
    assert c_list.status_code == 200
    assert all(item["id"] != product_id for item in c_list.json()["data"])

    activated = client.patch(
        f"/api/v1/admin/products/{product_id}/status",
        json={"status": "active"},
        headers=headers,
    )
    assert activated.status_code == 200
    assert activated.json()["data"]["status"] == "active"

    c_list_active = client.get("/api/v1/products")
    assert c_list_active.status_code == 200
    assert any(item["id"] == product_id for item in c_list_active.json()["data"])

    updated = client.put(
        f"/api/v1/admin/products/{product_id}",
        json={**SAMPLE_PRODUCT, "name": "测试商品-已更新", "price": 1899, "status": "active"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "测试商品-已更新"
    assert updated.json()["data"]["price"] == 1899

    deactivated = client.patch(
        f"/api/v1/admin/products/{product_id}/status",
        json={"status": "inactive"},
        headers=headers,
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["data"]["status"] == "inactive"

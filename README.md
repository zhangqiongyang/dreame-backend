# Dreame Backend（dreame-backend）

追觅电商后端：**Python 3 + FastAPI**，数据库 **MySQL 8（utf8mb4）**。

## 新手从哪里开始

0. **必读**：[教学路线（假支付阶段）](docs/教学路线-假支付阶段.md)（按天做什么）。  
1. 阅读并动手完成：**[数据库安装与配置](docs/数据库安装与配置.md)**（含本机 / Docker / 云库简述）。
2. 复制环境变量：`cp .env.example .env`，填写 `DATABASE_URL`（异步）与 `DATABASE_URL_SYNC`（迁移用）。
3. 安装依赖并启动：

```bash
cd dreame-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. 打开 API 文档：`http://127.0.0.1:8000/docs`

## 本地一键起 MySQL（可选）

在 `dreame-backend` 目录：

```bash
docker compose up -d db
```

详见 `docker-compose.yml` 与数据库教学文档中的说明。

## 目录说明

| 路径 | 作用 |
|------|------|
| `app/main.py` | FastAPI 入口、异常处理、定时关单 |
| `app/core/` | 配置、JWT、统一响应 `code` 200/500 |
| `app/models/` | SQLAlchemy 模型 |
| `app/services/` | 业务逻辑（订单状态机、退款等） |
| `app/api/v1/endpoints/` | REST 路由 |
| `alembic/` | 数据库迁移（含 3 款商品种子） |
| `docs/后端开发方案-v5.md` | 完整 API 与领域设计 |
| `docs/数据库安装与配置.md` | **MySQL 安装与连接教学** |
| `docs/教学路线-假支付阶段.md` | 按天学习计划（假支付） |

## 首次初始化数据库

```bash
cd dreame-backend
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

## 管理端鉴权

- 登录：`POST /api/v1/admin/auth/login`（body: `username` / `password`，默认见 `.env.example`）
- 登录后请求头：`Authorization: Bearer <token>`
- 仍兼容直接传 `ADMIN_TOKEN` 作为 Bearer（脚本/调试）

## 小程序登录（开发）

未配置 `WECHAT_APPID` 时自动 **Mock**：`POST /api/v1/auth/wechat` 的 `code` 会映射为 `mock_<code>` 的 openid。

## 与前端项目

- 小程序：`dreame-web-mini` 的 `VITE_API_BASE_URL` 指向本服务（需 HTTPS 域名后再配小程序合法域名）。
- 管理后台：`dreame-web-support` 同上。

## 约定（与前端统一）

- 业务 JSON：`{ "code": 200, "message": "ok", "data": ... }` 表示成功；`code: 500` 表示业务失败（详见 [后端开发方案-v5](docs/后端开发方案-v5.md)）。
- 小程序一期需 **微信授权登录**；收货地址在 **下单请求体** 中提交并快照到订单。

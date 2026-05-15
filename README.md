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
| `app/main.py` | FastAPI 入口 |
| `app/core/config.py` | 配置（含 `DATABASE_URL`） |
| `app/db/session.py` | 异步 SQLAlchemy 引擎与 Session |
| `app/api/` | 路由与依赖（`get_db`） |
| `alembic/` | 数据库迁移 |
| `docs/数据库安装与配置.md` | **MySQL 安装与连接教学** |
| `docs/教学路线-假支付阶段.md` | 按天学习计划（假支付） |

## 与前端项目

- 小程序：`dreame-web-mini` 的 `VITE_API_BASE_URL` 指向本服务（需 HTTPS 域名后再配小程序合法域名）。
- 管理后台：`dreame-web-support` 同上。

## 约定（与前端统一）

- 业务 JSON：`{ "code": 0, "message": "ok", "data": ... }`，`code != 0` 表示失败（后续接口会统一封装）。

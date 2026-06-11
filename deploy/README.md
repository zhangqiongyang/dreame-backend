# Dreame 服务器部署指南

支持 **测试环境** 与 **生产环境** 两套域名，通过 `.env` 切换。

| 环境 | 域名 | 用途 |
|------|------|------|
| 测试 staging | `cuteyam.com` | 联调、预发布 |
| 生产 production | `dreamewindowcleaningrobot.com` | 正式上线 |

---

## 架构

```
https://<SITE_DOMAIN>
        │
   nginx :443
   ├── /admin/    管理后台
   ├── /api/      FastAPI
   └── /uploads/  图片
```

小程序 `VITE_API_BASE_URL` = `PUBLIC_BASE_URL`（**不要**加 `/admin`）。

---

## 快速开始

### 1. 服务器初始化（仅一次）

```bash
ssh root@服务器IP
cd /opt/zhuimi/dreame-backend/deploy
chmod +x setup-server.sh deploy.sh
./setup-server.sh
```

### 2. 选择环境并创建配置

```bash
# 测试环境（当前服务器 152.136.63.163）
./deploy.sh init staging
vim .env

# 生产环境（新服务器）
./deploy.sh init production
vim .env
```

### 3. 上传对应域名的 SSL 证书

证书域名须与 `SITE_DOMAIN` 一致，放到 `deploy/ssl/`：

```
fullchain.pem
privkey.pem
```

Mac 上传示例（测试环境）：

```bash
scp cuteyam.com_bundle.crt root@152.136.63.163:/opt/zhuimi/dreame-backend/deploy/ssl/fullchain.pem
scp cuteyam.com.key root@152.136.63.163:/opt/zhuimi/dreame-backend/deploy/ssl/privkey.pem
```

### 4. 启动

```bash
./deploy.sh check
./deploy.sh up
./deploy.sh verify
```

- 测试后台：https://cuteyam.com/admin/
- 生产后台：https://dreamewindowcleaningrobot.com/admin/

---

## 环境配置对照

### 服务器 `deploy/.env`

| 变量 | 测试 staging | 生产 production |
|------|--------------|-----------------|
| `SITE_DOMAIN` | `cuteyam.com` | `dreamewindowcleaningrobot.com` |
| `PUBLIC_BASE_URL` | `https://cuteyam.com` | `https://dreamewindowcleaningrobot.com` |
| `CORS_ORIGINS` | `https://cuteyam.com,https://www.cuteyam.com` | `https://dreamewindowcleaningrobot.com,https://www.dreamewindowcleaningrobot.com` |

模板文件：`.env.staging.example` / `.env.production.example`

### 管理后台 `dreame-web-support`

| 文件 | API 地址 |
|------|----------|
| `.env.staging` | `https://cuteyam.com` |
| `.env.production` | `https://dreamewindowcleaningrobot.com` |

服务器 Docker 构建时通过 `PUBLIC_BASE_URL` 注入，**以服务器 `.env` 为准**。

本地构建（一般不需要，仅调试）：

```bash
npm run build:staging      # 测试
npm run build:production   # 生产
```

### 小程序 `dreame-web-mini`

| 文件 | API 地址 |
|------|----------|
| `.env.staging` | `https://cuteyam.com` |
| `.env.production` | `https://dreamewindowcleaningrobot.com` |

```bash
# 测试版小程序
npm run build:mp-weixin:staging

# 正式版小程序
npm run build:mp-weixin:production
```

微信公众平台 → 服务器域名须与构建环境一致。

---

## 目录结构

```
/opt/zhuimi/
├── dreame-backend/deploy/
│   ├── .env                 # 当前服务器环境配置
│   ├── deploy.sh
│   ├── ssl/                 # 与 SITE_DOMAIN 匹配的证书
│   └── nginx/
│       ├── nginx.conf.template
│       └── generated.conf   # deploy.sh 自动生成
└── dreame-web-support/
```

Gitee clone：

```bash
git clone https://gitee.com/zhangqiongyang/dreame-backend.git
git clone https://gitee.com/zhangqiongyang/dreame-web-support.git
```

---

## deploy.sh 命令

| 命令 | 说明 |
|------|------|
| `./deploy.sh init staging` | 创建测试环境 .env |
| `./deploy.sh init production` | 创建生产环境 .env |
| `./deploy.sh check` | 检查配置、证书、生成 nginx |
| `./deploy.sh up` | 构建并启动 |
| `./deploy.sh update` | git pull + 重新构建 |
| `./deploy.sh verify` | 验证 health / admin / api |

---

## 两台服务器部署建议

| 服务器 | 环境 | .env | 证书 |
|--------|------|------|------|
| 152.136.63.163（现有） | 测试 | `init staging` | cuteyam.com |
| 新 CVM | 生产 | `init production` | dreamewindowcleaningrobot.com |

测试与生产应使用 **不同的数据库密码、JWT_SECRET**，互不影响。

---

## 日常更新

```bash
cd /opt/zhuimi/dreame-backend/deploy
./deploy.sh update
```

---

## 故障排查

| 现象 | 处理 |
|------|------|
| nginx 证书错误 | 确认 SSL 域名与 `SITE_DOMAIN` 一致 |
| API 404 | 确认 `nginx/generated.conf` 已生成，`./deploy.sh up` |
| 管理后台请求错域名 | 重建 nginx：`./deploy.sh up`（会按 `.env` 重新构建前端） |

```bash
./deploy.sh logs api
./deploy.sh logs nginx
grep SITE_DOMAIN .env
```

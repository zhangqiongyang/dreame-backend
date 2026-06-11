# Docker 部署（腾讯云 OpenCloudOS · 单域名 cuteyam.com）

## 架构

| 路径 | 服务 |
|------|------|
| `https://cuteyam.com/admin/` | 管理后台 |
| `https://cuteyam.com/api/v1/...` | 后端 API |
| `https://cuteyam.com/uploads/...` | 商品图片 |
| `https://cuteyam.com/health` | 健康检查 |

访问根路径 `https://cuteyam.com/` 会自动跳转到 `/admin/`。

小程序 `VITE_API_BASE_URL` 填：`https://cuteyam.com`（与 `PUBLIC_BASE_URL` 一致，**不要**加 `/admin`）。

## 服务器目录结构

只需 clone **两个仓库**，且必须为**同级目录**：

```
/opt/zhuimi/                      # 父目录，名称可自定
├── dreame-backend/               # 含本 deploy 目录
│   └── deploy/
└── dreame-web-support/           # 管理后台源码（构建进 nginx 镜像）
```

小程序 `dreame-web-mini` **不必**部署到服务器，在本机构建后上传微信即可。

### 首次 clone

```bash
sudo mkdir -p /opt/zhuimi
sudo chown $USER:$USER /opt/zhuimi
cd /opt/zhuimi

git clone https://github.com/zhangqiongyang/dreame-backend.git
git clone https://github.com/zhangqiongyang/dreame-web-support.git
```

私有仓库请使用 SSH 或 HTTPS + Token。

## 前置条件

1. 腾讯云 CVM（建议 2核4G+），系统 **OpenCloudOS 9**（或其他支持 Docker 的 Linux）
2. 域名 `cuteyam.com` 已备案，A 记录指向服务器公网 IP
3. 安全组放行 **80、443**
4. 已安装 Docker 与 Compose 插件

### OpenCloudOS 安装 Docker

```bash
sudo yum install -y docker docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# 重新登录后
docker compose version
```

若官方源无 compose 插件，可参考 [Docker 官方安装文档](https://docs.docker.com/engine/install/centos/) 使用 `docker-ce` 源。

## 一、SSL 证书

将腾讯云证书放到 `dreame-backend/deploy/ssl/`：

```
deploy/ssl/fullchain.pem
deploy/ssl/privkey.pem
```

腾讯云：SSL 证书 → 下载 Nginx 证书 → `xxx_bundle.crt` → `fullchain.pem`，`xxx.key` → `privkey.pem`。

## 二、配置环境变量

```bash
cd dreame-backend/deploy
cp .env.example .env
vim .env
```

## 三、启动

```bash
cd dreame-backend/deploy
docker compose up -d --build
```

验证：

```bash
curl https://cuteyam.com/health
curl -I https://cuteyam.com/admin/
```

管理后台：**https://cuteyam.com/admin/** ，使用 `.env` 中 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 登录。

## 四、发布微信小程序

在本机构建：

```bash
cd dreame-web-mini
npm run build:mp-weixin
```

微信公众平台 → 服务器域名：`https://cuteyam.com`（request / downloadFile / uploadFile）。

## 五、更新部署

```bash
cd /opt/zhuimi/dreame-backend && git pull
cd /opt/zhuimi/dreame-web-support && git pull
cd /opt/zhuimi/dreame-backend/deploy && docker compose up -d --build
```

## 六、故障排查

| 现象 | 处理 |
|------|------|
| `/admin/` 白屏 | 重新 `docker compose up -d --build nginx`，确认静态资源路径含 `/admin/assets/` |
| 502 | `docker compose logs api` |
| 登录后 401 跳错路径 | 确认已用最新代码构建（登录页在 `/admin/login`） |
| 图片不显示 | `PUBLIC_BASE_URL=https://cuteyam.com`，微信 downloadFile 域名已配置 |
| build 找不到 dreame-web-support | 确认两个仓库在同一父目录下，见「服务器目录结构」 |

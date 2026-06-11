#!/usr/bin/env bash
# 腾讯云 OpenCloudOS 首次环境初始化（仅需执行一次）

set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/zhuimi}"
GITEE_USER="${GITEE_USER:-zhangqiongyang}"
USE_SSH="${USE_SSH:-false}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[setup]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }

if [[ "$(id -u)" -ne 0 ]]; then
  warn "建议使用 root 执行，或确保有 sudo 权限"
fi

info "安装 Git..."
if ! command -v git >/dev/null 2>&1; then
  yum install -y git
fi

info "安装 Docker..."
if ! command -v docker >/dev/null 2>&1; then
  yum install -y docker docker-compose-plugin
fi
systemctl enable --now docker
docker compose version

info "停用系统自带 Nginx（避免占用 80 端口）..."
if systemctl is-active nginx >/dev/null 2>&1; then
  systemctl stop nginx
  systemctl disable nginx
  info "已停用系统 nginx"
fi

info "创建目录 $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

clone_repo() {
  local name="$1"
  local url
  if [[ "$USE_SSH" == "true" ]]; then
    url="git@gitee.com:${GITEE_USER}/${name}.git"
  else
    url="https://gitee.com/${GITEE_USER}/${name}.git"
  fi
  if [[ -d "$name/.git" ]]; then
    info "$name 已存在，执行 git pull"
    git -C "$name" pull
  else
    info "clone $name ..."
    git clone "$url"
  fi
}

clone_repo "dreame-backend"
clone_repo "dreame-web-support"

info "初始化部署配置..."
cd "$INSTALL_DIR/dreame-backend/deploy"
chmod +x deploy.sh setup-server.sh 2>/dev/null || true
./deploy.sh init staging

cat <<EOF

========================================
服务器环境已就绪，请继续以下步骤:

1. 上传 SSL 证书到:
   $INSTALL_DIR/dreame-backend/deploy/ssl/fullchain.pem
   $INSTALL_DIR/dreame-backend/deploy/ssl/privkey.pem

   Mac 上传示例:
   scp 证书.crt root@服务器IP:$INSTALL_DIR/dreame-backend/deploy/ssl/fullchain.pem
   scp 证书.key root@服务器IP:$INSTALL_DIR/dreame-backend/deploy/ssl/privkey.pem

2. 编辑环境变量:
   vim $INSTALL_DIR/dreame-backend/deploy/.env

3. 检查并启动:
   cd $INSTALL_DIR/dreame-backend/deploy
   ./deploy.sh check
   ./deploy.sh up
   ./deploy.sh verify

========================================
EOF

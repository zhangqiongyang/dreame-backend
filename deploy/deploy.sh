#!/usr/bin/env bash
# Dreame 生产部署脚本（在 dreame-backend/deploy 目录执行）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ROOT_DIR="$(cd .. && pwd)"
WORKSPACE_DIR="$(cd ../.. && pwd)"
SUPPORT_DIR="$WORKSPACE_DIR/dreame-web-support"
ENV_FILE="$SCRIPT_DIR/.env"
SSL_DIR="$SCRIPT_DIR/ssl"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[deploy]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
err()  { echo -e "${RED}[error]${NC} $*" >&2; }

usage() {
  cat <<'EOF'
用法: ./deploy.sh <命令>

命令:
  check      部署前检查（目录、.env、SSL、端口）
  init       创建 .env，例: ./deploy.sh init staging | init production
  up         构建并启动全部服务
  update     拉取代码并重新构建（需在 /opt/zhuimi 布局下）
  status     查看容器状态与健康检查
  logs       查看日志，例: ./deploy.sh logs api
  restart    重启服务，例: ./deploy.sh restart nginx
  reset-db   清空数据库卷并重新部署（会删除所有数据）
  verify     验证 HTTPS 端点是否可用

示例:
  ./deploy.sh check && ./deploy.sh up
  ./deploy.sh update
  ./deploy.sh logs nginx
EOF
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    err "未安装 Docker，请先运行 setup-server.sh"
    exit 1
  fi
  docker compose version >/dev/null 2>&1 || {
    err "未安装 docker compose 插件"
    exit 1
  }
}

check_layout() {
  if [[ ! -f "$ROOT_DIR/Dockerfile" ]]; then
    err "未找到后端 Dockerfile，请确认在 dreame-backend/deploy 目录执行"
    exit 1
  fi
  if [[ ! -f "$SUPPORT_DIR/package.json" ]]; then
    err "未找到 dreame-web-support（期望路径: $SUPPORT_DIR）"
    err "请确保两个仓库为同级目录，例如:"
    err "  /opt/zhuimi/dreame-backend"
    err "  /opt/zhuimi/dreame-web-support"
    exit 1
  fi
  info "目录结构 OK"
}

check_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    err "缺少 .env，请执行: ./deploy.sh init 后编辑 .env"
    exit 1
  fi
  # shellcheck disable=SC1090
  source "$ENV_FILE"

  local missing=0
  local placeholders=("请设置" "change-me" "你的AppID" "你的AppSecret")
  local keys=(SITE_DOMAIN MYSQL_ROOT_PASSWORD MYSQL_PASSWORD JWT_SECRET ADMIN_PASSWORD WECHAT_APPID WECHAT_SECRET PUBLIC_BASE_URL)

  for key in "${keys[@]}"; do
    local val="${!key:-}"
    if [[ -z "$val" ]]; then
      err ".env 中 $key 为空"
      missing=1
      continue
    fi
    for ph in "${placeholders[@]}"; do
      if [[ "$val" == *"$ph"* ]]; then
        err ".env 中 $key 仍为示例占位符，请修改"
        missing=1
      fi
    done
  done

  if [[ $missing -ne 0 ]]; then
    exit 1
  fi
  if [[ -z "${SITE_DOMAIN:-}" ]]; then
    SITE_DOMAIN="${PUBLIC_BASE_URL#https://}"
    SITE_DOMAIN="${SITE_DOMAIN#http://}"
    SITE_DOMAIN="${SITE_DOMAIN%%/*}"
    export SITE_DOMAIN
    warn "SITE_DOMAIN 未设置，已从 PUBLIC_BASE_URL 推导: $SITE_DOMAIN"
  fi
  info ".env 配置 OK（$SITE_DOMAIN）"
}

generate_nginx_conf() {
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  local domain="${SITE_DOMAIN:-}"
  if [[ -z "$domain" ]]; then
    domain="${PUBLIC_BASE_URL#https://}"
    domain="${domain#http://}"
    domain="${domain%%/*}"
  fi
  local template="$SCRIPT_DIR/nginx/nginx.conf.template"
  local output="$SCRIPT_DIR/nginx/generated.conf"
  if [[ ! -f "$template" ]]; then
    err "缺少 nginx 模板: $template"
    exit 1
  fi
  sed "s/__SITE_DOMAIN__/$domain/g" "$template" > "$output"
  info "已生成 nginx 配置: SITE_DOMAIN=$domain"
}

check_ssl() {
  local cert="$SSL_DIR/fullchain.pem"
  local key="$SSL_DIR/privkey.pem"
  if [[ ! -s "$cert" || ! -s "$key" ]]; then
    err "SSL 证书缺失或为空，请放到 deploy/ssl/:"
    err "  fullchain.pem  privkey.pem"
    err "腾讯云 Nginx 证书: xxx_bundle.crt → fullchain.pem, xxx.key → privkey.pem"
    exit 1
  fi
  chmod 644 "$cert" 2>/dev/null || true
  chmod 600 "$key" 2>/dev/null || true
  info "SSL 证书 OK"
}

check_port80() {
  if ss -tlnp 2>/dev/null | grep -q ':80 '; then
    if ! ss -tlnp 2>/dev/null | grep ':80 ' | grep -q docker-proxy; then
      warn "80 端口被非 Docker 进程占用，nginx 可能启动失败"
      warn "可执行: systemctl stop nginx && systemctl disable nginx"
    fi
  fi
}

cmd_check() {
  require_docker
  check_layout
  check_env
  check_ssl
  check_port80
  generate_nginx_conf
  info "全部检查通过，可执行 ./deploy.sh up"
}

cmd_init() {
  local profile="${1:-staging}"
  local example="$SCRIPT_DIR/.env.${profile}.example"
  if [[ ! -f "$example" ]]; then
    err "未知环境: $profile（可选: staging | production）"
    exit 1
  fi
  if [[ -f "$ENV_FILE" ]]; then
    warn ".env 已存在，跳过"
  else
    cp "$example" "$ENV_FILE"
    info "已创建 .env（$profile），请编辑后执行 ./deploy.sh check"
    if command -v openssl >/dev/null 2>&1; then
      local secret
      secret="$(openssl rand -hex 32)"
      sed -i "s/JWT_SECRET=.*/JWT_SECRET=$secret/" "$ENV_FILE" 2>/dev/null \
        || sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=$secret/" "$ENV_FILE"
      info "已自动生成 JWT_SECRET"
    fi
  fi
}

cmd_up() {
  require_docker
  check_layout
  check_env
  check_ssl
  check_port80
  generate_nginx_conf
  info "构建并启动服务..."
  docker compose up -d --build
  info "等待服务就绪..."
  sleep 15
  cmd_status || true
}

cmd_update() {
  require_docker
  check_layout
  info "拉取 dreame-backend..."
  git -C "$ROOT_DIR" pull
  info "拉取 dreame-web-support..."
  git -C "$SUPPORT_DIR" pull
  cmd_up
}

cmd_status() {
  require_docker
  docker compose ps
  echo ""
  if [[ -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    local base="${PUBLIC_BASE_URL:-}"
    [[ -z "$base" ]] && base="https://${SITE_DOMAIN:-cuteyam.com}"
    base="${base%/}"
    if curl -sf --max-time 5 "$base/health" >/dev/null 2>&1; then
      info "健康检查 OK: $base/health"
    else
      warn "健康检查失败: $base/health"
    fi
  fi
}

cmd_logs() {
  require_docker
  local service="${1:-}"
  if [[ -n "$service" ]]; then
    docker compose logs -f --tail=100 "$service"
  else
    docker compose logs -f --tail=50
  fi
}

cmd_restart() {
  require_docker
  local service="${1:-}"
  if [[ -n "$service" ]]; then
    docker compose restart "$service"
  else
    docker compose restart
  fi
  cmd_status || true
}

cmd_reset_db() {
  require_docker
  warn "将删除 MySQL 数据卷及所有业务数据！"
  read -r -p "输入 yes 确认: " confirm
  if [[ "$confirm" != "yes" ]]; then
    info "已取消"
    exit 0
  fi
  docker compose down -v
  cmd_up
}

cmd_verify() {
  require_docker
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  local base="${PUBLIC_BASE_URL:-}"
  [[ -z "$base" ]] && base="https://${SITE_DOMAIN:-cuteyam.com}"
  base="${base%/}"

  info "检查 $base/health"
  curl -sf "$base/health" | head -c 200
  echo ""

  info "检查 $base/admin/"
  curl -sI "$base/admin/" | head -5

  info "检查 $base/api/v1/products"
  curl -sf "$base/api/v1/products" | head -c 120
  echo ""
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    check)    cmd_check ;;
    init)     cmd_init "$@" ;;
    up)       cmd_up ;;
    update)   cmd_update ;;
    status)   cmd_status ;;
    logs)     cmd_logs "$@" ;;
    restart)  cmd_restart "$@" ;;
    reset-db) cmd_reset_db ;;
    verify)   cmd_verify ;;
    -h|--help|help|"") usage ;;
    *)
      err "未知命令: $cmd"
      usage
      exit 1
      ;;
  esac
}

main "$@"

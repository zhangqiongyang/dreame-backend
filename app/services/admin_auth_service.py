from app.core.config import settings
from app.core.exceptions import BusinessError
from app.core.security import create_access_token
from app.schemas.admin import AdminLoginIn, AdminLoginOut, AdminUserOut


def admin_user_out() -> AdminUserOut:
    return AdminUserOut(
        username=settings.admin_username,
        displayName=settings.admin_display_name,
        role="super_admin",
    )


def admin_login(body: AdminLoginIn) -> AdminLoginOut:
    if body.username != settings.admin_username or body.password != settings.admin_password:
        raise BusinessError("用户名或密码错误")
    token = create_access_token("admin", extra={"role": "admin"})
    return AdminLoginOut(
        token=token,
        expiresIn=settings.jwt_expire_seconds,
        user=admin_user_out(),
    )

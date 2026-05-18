class BusinessError(Exception):
    def __init__(self, message: str, *, http_status: int = 200) -> None:
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class UnauthorizedError(BusinessError):
    def __init__(self, message: str = "未登录或登录已过期") -> None:
        super().__init__(message, http_status=401)

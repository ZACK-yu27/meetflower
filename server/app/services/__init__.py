"""服务层：recognition / garden / resource / house / bouquet / order。"""


class DomainError(Exception):
    """业务错误：API 层统一转换为 {"detail": ...} JSON 响应。

    status_code 约定（API.md §0）：409 状态冲突，404 不存在，422 参数错。
    """

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)

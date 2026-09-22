"""领域级异常。"""


class ConflictError(Exception):
    """业务冲突（如多条启用规则）；由 main.py 统一转 409。"""

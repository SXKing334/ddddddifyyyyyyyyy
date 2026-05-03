from fastapi import Depends, HTTPException, Request

from novel.core.config.security import get_role_permissions
from novel.utils.token_util import JwtUtil


async def get_current_user(request: Request) -> dict:
    """
    从请求头/Token中解析出当前用户信息
    返回格式：
    {
        "tenant_id": str,
        "user_id": int,
        "role": str
    }
    """
    # 1. 获取token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="未提供令牌")

    # 2. 格式校验
    if " " not in auth_header:
        raise HTTPException(status_code=401, detail="令牌格式错误")

    token_type, token = auth_header.split(" ", 1)
    if token_type.lower() != "bearer":
        raise HTTPException(status_code=401, detail="令牌类型错误")

    # 3. 验证并解析 token
    payload = JwtUtil.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")

    # 4. 必须包含的字段
    if "tenant_id" not in payload or "user_id" not in payload or "role" not in payload:
        raise HTTPException(status_code=401, detail="令牌信息不完整")

    return payload


def require_permission(permission: str):
    """权限校验装饰器"""

    def wrapper(user: dict = Depends(get_current_user)):
        # 如果用户解析失败（理论不会到这里，因为get_current_user会直接抛异常）
        if not user:
            raise HTTPException(status_code=401, detail="未登录")

        # 获取当前角色的权限列表
        perms = get_role_permissions(user["role"])

        # 超级管理员 直接放行
        if perms == ["*"]:
            return True

        # 判断是否拥有该权限
        if permission not in perms:
            raise HTTPException(status_code=403, detail="无权限执行此操作")

        return True

    return wrapper

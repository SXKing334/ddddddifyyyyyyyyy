# novel\utils\orm_to_dict
from datetime import datetime


def orm_to_dict(obj) -> dict | list[dict] | None:
    if obj is None:
        return None

    # 如果是列表，递归转换
    if isinstance(obj, list):
        return [orm_to_dict(item) for item in obj]

    # 如果已经是字典，直接返回
    if isinstance(obj, dict):
        return obj

    res = {}

    # 遍历 ORM 模型字段
    for c in obj.__class__.__table__.columns:
        key = c.name
        value = getattr(obj, key)

        # 时间格式化
        if isinstance(value, datetime):
            value = value.strftime("%Y-%m-%d %H:%M:%S")

        res[key] = value

    return res
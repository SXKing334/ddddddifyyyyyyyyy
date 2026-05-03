def get_role_permissions(role: str):
    # 平台管理员
    if role == "super_admin":
        return ["*"]

    # 租户管理员
    if role == "admin":
        return [
            # 流程
            "flow:list", "flow:create", "flow:edit", "flow:delete", "flow:publish",
            # 对话
            "chat:list", "chat:reply", "chat:transfer", "chat:delete",
            # 知识库
            "doc:list", "doc:upload", "doc:delete", "doc:update",
            # 员工管理
            "user:list", "user:create", "user:edit", "user:delete",
            # 租户配置
            "tenant:config",
            # 统计
            "stat:view",
            # 技能
            "skill:list", "skill:create", "skill:edit"
        ]

    # 租户下的技术员工
    if role == "tech":
        return [
            "flow:list", "flow:create", "flow:edit", "flow:publish",
            "chat:list", "chat:reply",
            "doc:list", "doc:upload", "doc:edit",
            "skill:list", "skill:create", "skill:edit",
            "mcp:list", "mcp:create", "mcp:edit",
            "stat:view"
        ]

    # 租户下的工作流人工节点的接待员工
    if role == "agent":
        return [
            "chat:list", "chat:reply", "chat:transfer",
            "flow:list",
            "doc:list",
            "stat:view"
        ]

    # 租户下的观察者状态
    if role == "viewer":
        return [
            "flow:list",
            "chat:list",
            "doc:list",
            "stat:view",
            "user:list"
        ]

    return []
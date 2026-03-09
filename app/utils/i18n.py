from __future__ import annotations


ACTION_LABELS: dict[str, str] = {
    "login": "登录",
    "logout": "退出登录",
    "register": "注册账号",
    "profile_update": "更新基本信息",
    "storage_create": "新增储存信息",
    "storage_update": "编辑储存信息",
    "storage_delete": "删除储存信息",
    "evaluate": "生成辨识与评估",
    "admin_user_update": "维护用户",
    "admin_chemical_create": "新增化学品",
    "admin_chemical_update": "编辑化学品",
    "admin_chemical_delete": "删除化学品",
    "admin_rule_create": "新增评估规则",
    "admin_rule_update": "编辑评估规则",
    "admin_storage_update": "维护储存信息",
    "admin_storage_delete": "删除储存信息",
    "admin_result_review": "审核评估结果",
    "admin_backup_export": "导出备份（JSON）",
    "admin_backup_export_xlsx": "导出备份（Excel）",
    "admin_backup_import": "恢复备份",
    "seed_demo": "导入示例数据",
}


def label_action(action: str | None) -> str:
    if not action:
        return "-"
    return ACTION_LABELS.get(action, action)


def label_review_status(status: str | None) -> str:
    if status == "pending":
        return "待审核"
    if status == "approved":
        return "已通过"
    if status == "rejected":
        return "已驳回"
    return status or "-"

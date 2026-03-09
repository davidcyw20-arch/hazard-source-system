# 危险化学品重大危险源自动辨识与等级评估系统（Flask + MySQL）

## 功能概览

- 用户端：注册/登录、维护基本信息、录入企业储存信息、自动辨识与等级评估（R 值）、查看结果与计算依据、导出报告（HTML/PDF）、个人操作记录追溯
- 管理端：管理员登录、用户管理（角色/启停/重置密码）、化学品基础信息与临界量维护、评估规则/等级区间维护、企业储存信息集中管理、评估结果审核、数据备份/恢复（JSON）
- 接口：`/api/v1/*` 提供化学品/储存/结果查询（需要登录；部分仅管理员）

## 快速启动

1) 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果你看到 `Activate.ps1` “无法识别”的报错，通常是少了前缀路径，请确保在项目目录执行 `.\.venv\Scripts\Activate.ps1`（而不是只输入 `Activate.ps1`）。

2) 配置数据库（MySQL）

- 新建数据库：`hazard_source_system`（字符集建议 `utf8mb4`）
- 复制环境变量：将 `.env.example` 复制为 `.env` 并修改 `DATABASE_URL`

3) 初始化数据（建表 + 示例数据 + 默认管理员）

```powershell
$env:FLASK_APP="wsgi.py"
flask init-db
```

已有数据库升级（不丢数据）：使用 Alembic 执行迁移（会新增字段与参数表）

```powershell
pip install -r requirements.txt
.\.venv\Scripts\python -m flask db-upgrade
```

可选：导入更多预置示例（演示用的用户/储存记录/评估结果）

```powershell
flask seed-demo
```

## 备份导出格式

- 管理端“备份/恢复”支持导出 `backup.xlsx`（便于查看）和 `backup.json`（用于恢复）。

4) 运行

```powershell
python wsgi.py
```

浏览器打开：`http://127.0.0.1:5000`

## 默认账号

- 管理员：`admin` / `admin123`
- 可重置：`flask create-admin --username admin --password admin123`

## 评估逻辑（示例实现）

- 标准依据：GB 18218（示例）
- 计算：`R = Σ(Qi / Q0i)`
- 判定：`R ≥ 1` 视为重大危险源
- 等级：按管理端“评估规则”配置区间自动划分（内置常用区间示例，可修改）

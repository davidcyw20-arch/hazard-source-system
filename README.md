# 危险化学品重大危险源自动辨识与等级评估系统（Flask + MySQL）

本系统面向**监管管理端**与**企业用户端**，围绕《危险化学品重大危险源辨识》（GB 18218）构建完整闭环：
**数据维护 → 储存信息录入 → 自动辨识 → 等级评估 → 审核统计 → 报告导出**。

---

## 1. 核心功能（按角色）

## （1）管理端（Admin）

1. **管理员账号登录与后台安全管理**
   - 支持管理员身份认证、角色鉴权、账号启停与密码重置。
   - 审计日志记录关键管理操作，保障系统运行安全与可追溯。

2. **危险化学品基础信息与临界量维护（GB 18218）**
   - 统一维护化学品名称、类别、CAS、临界量、单位等标准参数。
   - 支持 GB18218 全量 SQL 导入、校验、去重、参数更新，作为辨识计算标准数据源。

3. **重大危险源判定与等级评估参数维护**
   - 维护判定规则（如 `R = Σ(Qi/Q0i)`）及等级划分区间。
   - 支持规则启停与版本切换，确保评估逻辑和法规标准一致。

4. **企业储存信息集中管理**
   - 对企业储存场所、储存方式、储存量等信息进行集中查询与维护。
   - 支持按管理员视角统一查看全量储存台账，提升规范化管理效率。

5. **评估结果审核与统计分析**
   - 查看系统自动生成的辨识与等级评估结果，执行通过/驳回审核。
   - 支持结果状态筛选、关键字检索、统计概览卡片（总数/待审/通过/重大危险源）。
   - 支持审核备注记录，便于监管留痕与复核。

6. **数据备份与恢复**
   - 支持 JSON 备份恢复与 XLSX 导出。
   - 用于系统迁移、归档留存和风险应急恢复。

## （2）用户端（User）

1. **注册与登录**
   - 完成用户身份认证后进入业务功能界面。

2. **危险化学品储存信息录入**
   - 录入企业名称、化学品、储存量、储存场所（单元）及相关属性。
   - 为系统自动辨识与评估提供基础数据。

3. **自动辨识重大危险源**
   - 基于录入储存信息，自动计算并判断是否构成重大危险源。

4. **等级评估与 R 值计算**
   - 自动计算 `R` 值，结合 GB 18218 参数输出等级判定（含兼容等级展示）。

5. **结果查看与依据说明**
   - 查看判定结论、计算依据、风险等级、审核状态与审核备注。
   - 支持按企业名、审核状态快速筛选结果。

6. **报告导出**
   - 支持导出辨识与等级评估报告（HTML/PDF）。
   - 便于企业安全管理、监管报送与应急资料留存。

---

## 2. 评估逻辑说明（示例实现）

- 标准依据：GB 18218（当前内置 2018 版本参数）
- 核心计算：`R = Σ(Qi / Q0i)`
  - `Qi`：企业实际储存量
  - `Q0i`：标准临界量
- 判定规则：`R ≥ 1` 判定为重大危险源
- 等级划分：依据管理端配置规则区间自动判定
- 可扩展项：500m 暴露人口 `α` 参数参与计算

---

## 3. 界面与体验升级（本次完善）

- 统一现代化视觉风格（渐变色、玻璃质感、卡片阴影、统一圆角组件）。
- 管理端结果页面新增统计概览卡片与高级筛选（状态 + 关键字）。
- 审核流程支持备注输入与结果页备注展示。
- 用户端结果页面新增筛选区（状态 + 企业名称）与更清晰的信息层级。

---

## 4. 快速启动

### 4.1 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> 如果提示 `Activate.ps1` 无法识别，请确认在项目根目录执行 `\.venv\Scripts\Activate.ps1`。

### 4.2 配置数据库（推荐先用 SQLite，再切 MySQL）

1. 复制环境变量模板：将 `.env.example` 复制为 `.env`
2. **首次运行推荐直接使用默认 SQLite**（无需安装 MySQL）
3. 需要接入 MySQL 时，再设置 `DATABASE_URL`

SQLite 示例：

```env
DATABASE_URL=sqlite:///instance/hazard_source_system.db
SECRET_KEY=replace-this-with-a-random-string
```

MySQL 示例（请替换真实账号密码）：

```env
DATABASE_URL=mysql+pymysql://your_user:your_password@127.0.0.1:3306/hazard_source_system?charset=utf8mb4
SECRET_KEY=replace-this-with-a-random-string
```

### 4.3 初始化数据库与基础数据

```powershell
$env:FLASK_APP="wsgi.py"
flask init-db
```

#### 一键导入你提到的 4 个 SQL 文件

项目已内置命令，按以下顺序自动导入：
- `db_schema.sql`
- `GB18218_full_seed.sql`
- `GB18218_full_seed_fixed.sql`
- `db_init_gb18218.sql`

执行命令：

```powershell
flask import-all-sql --root .
```

> 如果你的项目在 `E:\hazard-source-system`，请先 `cd E:\hazard-source-system` 再执行上述命令。

已有库升级（保留数据）：

```powershell
.\.venv\Scripts\python -m flask db-upgrade
```

可选：导入演示数据

```powershell
flask seed-demo
```

### 4.4 运行系统

```powershell
python wsgi.py
```

访问地址：`http://127.0.0.1:5000`

---

## 5. 默认账号

- 管理员：`admin` / `admin123`
- 如需重置：

```powershell
flask create-admin --username admin --password admin123
```

---

## 6. 备份/恢复格式

- 备份导出支持：
  - `backup.json`（用于恢复）
  - `backup.xlsx`（用于查阅与归档）

---

## 7. API 概览

系统提供 `/api/v1/*` 查询接口（需登录；部分接口仅管理员可用），覆盖：
- 化学品信息
- 储存记录
- 评估结果

---

## 8. 典型业务流程（推荐）

1. 管理员维护 GB 18218 化学品与规则参数。
2. 企业用户录入储存信息（建议按企业多化学品分条录入）。
3. 用户触发自动辨识与评估，生成 R 值与等级。
4. 管理员审核结果并给出备注。
5. 企业导出 PDF 报告用于归档与监管报送。

---

## 9. 注意事项

- 生产环境务必修改 `SECRET_KEY`、数据库账号密码。
- 建议启用 HTTPS、数据库定时备份与审计日志保留策略。
- 如果导入 GB 全量数据，请优先使用系统提供的“校验/去重/参数更新”流程。


## 10. 常见问题排查

### 10.1 登录后报错：`OperationalError (1045) Access denied for user 'root'@'localhost'`

原因：`DATABASE_URL` 使用了错误的 MySQL 用户名/密码，或 MySQL 未授权该用户。

处理方式（任选其一）：

1. **最快方案：切换到 SQLite（推荐开发环境）**
   - 在 `.env` 中设置：
   - `DATABASE_URL=sqlite:///instance/hazard_source_system.db`
   - 重新执行 `flask init-db` 后启动系统。

2. **继续使用 MySQL**
   - 确认数据库已创建：`hazard_source_system`
   - 将 `.env` 中的 `DATABASE_URL` 改为真实账号密码
   - 确认该用户有目标库权限（`SELECT/INSERT/UPDATE/DELETE/CREATE/ALTER`）

> 从本版本开始，系统默认数据库已改为 SQLite，未配置 `DATABASE_URL` 时不会再默认连接 `root:root@localhost`。


### 10.2 提示“数据库连接失败”但你已经改成 SQLite

这通常是 SQLite 文件已创建但表结构尚未初始化（或首次启动尚未建表）。

建议顺序：
1. 执行 `flask init-db` 初始化默认数据（管理员、规则、示例化学品）。
2. 若仅做快速本地体验，也可直接重启应用（系统会在 SQLite 下自动建表）。
3. 然后使用管理员账号登录：`admin / admin123`。



### 10.3 仍然提示数据库连接失败（常见隐藏原因）

请重点检查 `.env` 中是否出现下面情况：
- `DATABASE_URL=`（等号后是空值）
- `DATABASE_URL` 格式拼写错误（例如少了 `sqlite:///` 或 `mysql+pymysql://`）

建议直接复制 `.env.example` 中任一完整示例再修改。



### 10.4 导入 `GB18218_full_seed.sql` 报错：`SQLiteCompiler ... OnDuplicateClause`

这是旧版本仅按 MySQL `ON DUPLICATE KEY` 语法导入导致的兼容问题。

请升级到当前版本后重新执行：

```powershell
flask import-all-sql --root .
```

当前版本已改为跨数据库 upsert（SQLite/MySQL 均可导入）。


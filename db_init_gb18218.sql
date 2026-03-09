-- GB 18218-2018 参数初始化（可执行）
-- 说明：
-- 1) α（表5）与等级（表6）按你提供的工程化描述写入，可直接使用。
-- 2) 表1/表3 仅写入你在描述中明确给出的“示例物质”；其它物质请继续补全。
-- 3) 表2/表4（按类别确定 Qi/β）的完整数值未在本段描述中给出，本文件仅保留可选的类别参数表示例占位。

SET NAMES utf8mb4;

-- 表 1（示例）：明确列名危险化学品临界量 Qi
-- 注意：若库中已存在同名化学品，则更新其 Qi/来源；若不存在则插入。
INSERT INTO chemicals (gb_version, name, category, cas_no, critical_quantity, unit, source_standard, hazard_category_symbol, beta, beta_source, created_at, updated_at)
VALUES
  ('GB 18218-2018', '氨', '毒性气体', NULL, 10, 't', 'GB 18218-2018 表1', NULL, 2.0, 'GB 18218-2018 表3', NOW(), NOW()),
  ('GB 18218-2018', '氯', '毒性气体', NULL, 5, 't', 'GB 18218-2018 表1', NULL, 4.0, 'GB 18218-2018 表3', NOW(), NOW()),
  ('GB 18218-2018', '甲醇', '易燃液体', NULL, 500, 't', 'GB 18218-2018 表1', NULL, NULL, NULL, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  gb_version=VALUES(gb_version),
  category=VALUES(category),
  cas_no=VALUES(cas_no),
  critical_quantity=VALUES(critical_quantity),
  unit=VALUES(unit),
  source_standard=VALUES(source_standard),
  hazard_category_symbol=VALUES(hazard_category_symbol),
  beta=VALUES(beta),
  beta_source=VALUES(beta_source),
  updated_at=NOW();

-- 表 3（示例）：毒性气体 β 值（优先采用）
-- 仅对库中已存在同名记录进行更新（避免插入缺少 Qi 的行）；你可先把表1补齐后再执行本段。
UPDATE chemicals SET beta=2.0, beta_source='GB 18218-2018 表3', gb_version='GB 18218-2018'
WHERE name IN ('一氧化碳','CO');
UPDATE chemicals SET beta=2.0, beta_source='GB 18218-2018 表3', gb_version='GB 18218-2018'
WHERE name IN ('氨','液氨');
UPDATE chemicals SET beta=4.0, beta_source='GB 18218-2018 表3', gb_version='GB 18218-2018'
WHERE name IN ('氯','液氯');
UPDATE chemicals SET beta=5.0, beta_source='GB 18218-2018 表3', gb_version='GB 18218-2018'
WHERE name IN ('硫化氢','H2S');
UPDATE chemicals SET beta=3.0, beta_source='GB 18218-2018 表3', gb_version='GB 18218-2018'
WHERE name IN ('氯化氢','氯化氢（无水）','HCl');
UPDATE chemicals SET beta=10.0, beta_source='GB 18218-2018 表3', gb_version='GB 18218-2018'
WHERE name IN ('氰化氢','HCN');
UPDATE chemicals SET beta=20.0, beta_source='GB 18218-2018 表3', gb_version='GB 18218-2018'
WHERE name IN ('碳酰氯','光气','COCl2');

-- 表 5：α 规则（按 500m 暴露人口分段）
INSERT INTO alpha_rules (gb_version, min_people, max_people, alpha, source, note)
VALUES
  ('GB 18218-2018', 0, 1, 0.5, 'GB 18218-2018 表5', '0人：α=0.5'),
  ('GB 18218-2018', 1, 30, 1.0, 'GB 18218-2018 表5', '1–29人：α=1.0'),
  ('GB 18218-2018', 30, 50, 1.2, 'GB 18218-2018 表5', '30–49人：α=1.2'),
  ('GB 18218-2018', 50, 100, 1.5, 'GB 18218-2018 表5', '50–99人：α=1.5'),
  ('GB 18218-2018', 100, NULL, 2.0, 'GB 18218-2018 表5', '≥100人：α=2.0');

-- 表 6：等级规则（按 R 值区间）
INSERT INTO level_rules (gb_version, min_r, max_r, level, source, note)
VALUES
  ('GB 18218-2018', 0, 10, '四级', 'GB 18218-2018 表6', 'R < 10：四级'),
  ('GB 18218-2018', 10, 50, '三级', 'GB 18218-2018 表6', '10 ≤ R < 50：三级'),
  ('GB 18218-2018', 50, 100, '二级', 'GB 18218-2018 表6', '50 ≤ R < 100：二级'),
  ('GB 18218-2018', 100, NULL, '一级', 'GB 18218-2018 表6', 'R ≥ 100：一级');

-- 表 4（可选占位）：类别符号 -> β（用于化学品未单独配置 β 或混合物兜底）
-- 这里仅给出占位示例，你需要按 GB 18218-2018 表4 或项目采用的分类体系补全。
INSERT INTO category_betas (gb_version, category_symbol, beta, beta_source, source, note)
VALUES
  ('GB 18218-2018', 'A', 1.0, '占位', 'GB 18218-2018 表4', '占位示例：请按表4补全'),
  ('GB 18218-2018', 'B', 1.2, '占位', 'GB 18218-2018 表4', '占位示例：请按表4补全'),
  ('GB 18218-2018', 'C', 1.5, '占位', 'GB 18218-2018 表4', '占位示例：请按表4补全');

-- 表 2（可选占位）：类别符号 -> 临界量 Qi（用于混合物/类别计算兜底）
-- 这里仅给出占位示例，你需要按 GB 18218-2018 表2（或你的工程分类表）补全。
INSERT INTO category_thresholds (gb_version, category_symbol, threshold_quantity, unit, source, note)
VALUES
  ('GB 18218-2018', 'A', 10, 't', 'GB 18218-2018 表2', '占位示例：请按表2补全'),
  ('GB 18218-2018', 'B', 200, 't', 'GB 18218-2018 表2', '占位示例：请按表2补全'),
  ('GB 18218-2018', 'C', 1000, 't', 'GB 18218-2018 表2', '占位示例：请按表2补全');

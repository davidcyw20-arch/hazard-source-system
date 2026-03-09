/* ===========================
   GB 18218-2018 修复版种子数据（可直接执行）
   适配：hazard_source_system（MySQL + Workbench）
   =========================== */

SET NAMES utf8mb4;
USE hazard_source_system;

-- ==================================================
-- 标准参数表（如你已用 Alembic 建过同名表，可保留本段 IF NOT EXISTS）
-- ==================================================
CREATE TABLE IF NOT EXISTS gb18218_alpha_rules (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  gb_version VARCHAR(20) NOT NULL DEFAULT 'GB18218-2018',
  min_people INT NOT NULL,
  max_people INT NULL,
  alpha DOUBLE NOT NULL,
  UNIQUE KEY uq_alpha (gb_version, min_people, max_people)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gb18218_level_rules (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  gb_version VARCHAR(20) NOT NULL DEFAULT 'GB18218-2018',
  level VARCHAR(20) NOT NULL,
  r_min DOUBLE NOT NULL,
  r_max DOUBLE NULL,
  UNIQUE KEY uq_level (gb_version, level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gb18218_category_thresholds (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  gb_version VARCHAR(20) NOT NULL DEFAULT 'GB18218-2018',
  symbol VARCHAR(20) NOT NULL,
  threshold_qty DOUBLE NOT NULL,
  unit VARCHAR(10) NOT NULL DEFAULT 't',
  UNIQUE KEY uq_cat_q (gb_version, symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gb18218_category_betas (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  gb_version VARCHAR(20) NOT NULL DEFAULT 'GB18218-2018',
  symbol VARCHAR(20) NOT NULL,
  beta DOUBLE NOT NULL,
  source ENUM('TABLE4') NOT NULL DEFAULT 'TABLE4',
  UNIQUE KEY uq_cat_beta (gb_version, symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================================================
-- 表5：暴露人员校正系数 α
-- ==================================================
INSERT INTO gb18218_alpha_rules (gb_version, min_people, max_people, alpha) VALUES
('GB18218-2018',100,NULL,2.0),
('GB18218-2018',50,99,1.5),
('GB18218-2018',30,49,1.2),
('GB18218-2018',1,29,1.0),
('GB18218-2018',0,0,0.5)
ON DUPLICATE KEY UPDATE alpha=VALUES(alpha);

-- ==================================================
-- 表6：R 值分级规则
-- ==================================================
INSERT INTO gb18218_level_rules (gb_version, level, r_min, r_max) VALUES
('GB18218-2018','一级',100,NULL),
('GB18218-2018','二级',50,100),
('GB18218-2018','三级',10,50),
('GB18218-2018','四级',0,10)
ON DUPLICATE KEY UPDATE r_min=VALUES(r_min), r_max=VALUES(r_max);

-- ==================================================
-- 表2：危险化学品类别临界量（未列名时使用）
-- ==================================================
INSERT INTO gb18218_category_thresholds (gb_version, symbol, threshold_qty, unit) VALUES
('GB18218-2018','J1',5.0,'t'),
('GB18218-2018','J2',50.0,'t'),
('GB18218-2018','J3',50.0,'t'),
('GB18218-2018','J4',50.0,'t'),
('GB18218-2018','J5',500.0,'t'),
('GB18218-2018','W1.1',1.0,'t'),
('GB18218-2018','W1.2',10.0,'t'),
('GB18218-2018','W1.3',50.0,'t'),
('GB18218-2018','W10',200.0,'t'),
('GB18218-2018','W11',200.0,'t'),
('GB18218-2018','W2',10.0,'t'),
('GB18218-2018','W3',150.0,'t'),
('GB18218-2018','W4',50.0,'t'),
('GB18218-2018','W5.1',10.0,'t'),
('GB18218-2018','W5.2',50.0,'t'),
('GB18218-2018','W5.3',1000.0,'t'),
('GB18218-2018','W5.4',5000.0,'t'),
('GB18218-2018','W6.1',10.0,'t'),
('GB18218-2018','W6.2',50.0,'t'),
('GB18218-2018','W7.1',10.0,'t'),
('GB18218-2018','W7.2',50.0,'t'),
('GB18218-2018','W8',50.0,'t'),
('GB18218-2018','W9.1',50.0,'t'),
('GB18218-2018','W9.2',200.0,'t')
ON DUPLICATE KEY UPDATE threshold_qty=VALUES(threshold_qty), unit=VALUES(unit);

-- ==================================================
-- 表4：危险化学品类别 β（表3未覆盖时使用）
-- ==================================================
INSERT INTO gb18218_category_betas (gb_version, symbol, beta, source) VALUES
('GB18218-2018','J1',4.0,'TABLE4'),
('GB18218-2018','J2',1.0,'TABLE4'),
('GB18218-2018','J3',2.0,'TABLE4'),
('GB18218-2018','J4',2.0,'TABLE4'),
('GB18218-2018','J5',1.0,'TABLE4'),
('GB18218-2018','W1.1',2.0,'TABLE4'),
('GB18218-2018','W1.2',2.0,'TABLE4'),
('GB18218-2018','W1.3',2.0,'TABLE4'),
('GB18218-2018','W10',1.0,'TABLE4'),
('GB18218-2018','W11',1.0,'TABLE4'),
('GB18218-2018','W2',1.5,'TABLE4'),
('GB18218-2018','W3',1.0,'TABLE4'),
('GB18218-2018','W4',1.0,'TABLE4'),
('GB18218-2018','W5.1',1.5,'TABLE4'),
('GB18218-2018','W5.2',1.0,'TABLE4'),
('GB18218-2018','W5.3',1.0,'TABLE4'),
('GB18218-2018','W5.4',1.0,'TABLE4'),
('GB18218-2018','W6.1',1.5,'TABLE4'),
('GB18218-2018','W6.2',1.0,'TABLE4'),
('GB18218-2018','W7.1',1.5,'TABLE4'),
('GB18218-2018','W7.2',1.0,'TABLE4'),
('GB18218-2018','W8',1.0,'TABLE4'),
('GB18218-2018','W9.1',1.0,'TABLE4'),
('GB18218-2018','W9.2',1.0,'TABLE4')
ON DUPLICATE KEY UPDATE beta=VALUES(beta), source=VALUES(source);

-- ==================================================
-- rule_sets：写入 GB18218-2018 等级规则（兼容你现有 rule_sets.levels JSON）
-- 你的 rule_sets.levels 是 JSON 类型：这里用 CAST 更稳
-- ==================================================
INSERT INTO rule_sets (name, is_active, levels, created_at, updated_at)
VALUES (
  'GB18218-2018',
  1,
  CAST('[{"level":"一级","min":100,"max":null},{"level":"二级","min":50,"max":100},{"level":"三级","min":10,"max":50},{"level":"四级","min":0,"max":10}]' AS JSON),
  NOW(), NOW()
)
ON DUPLICATE KEY UPDATE
is_active=VALUES(is_active),
levels=VALUES(levels),
updated_at=NOW();

-- ==================================================
-- 表1：危险化学品名称及其临界量 -> chemicals
-- 说明：本脚本将“名称+别名”整体写入 chemicals.name，CAS 可能为多值用分号分隔。
-- ==================================================
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氨 液氨;氨气', NULL, '7664-41-7', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('二氟化氧 一氧化二氟', NULL, '7783-41-7', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('二氧化氮', NULL, '10102-44-0', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('二氧化硫 亚硫酸酐', NULL, '7446-09-5', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氟', NULL, '7782-41-4', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('碳酰氯 光气', NULL, '75-44-5', 0.3, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('环氧乙烷 氧化乙烯', NULL, '75-21-8', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('甲醛(含量>90%) 蚁醛', NULL, '50-00-0', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('磷化氢 磷化三氢;膦', NULL, '7803-51-2', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硫化氢', NULL, '7783-06-4', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氯化氢(无水)', NULL, '7647-01-0', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氯 液氯;氯气', NULL, '7782-50-5', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 煤气属于混合物概念，表1通常不提供 CAS：这里保留原样（Q=20）
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('煤气(CO,CO和H2、CH4的混合物等)', NULL, NULL, 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('砷化氢 砷化三氢;胂', NULL, '7784-42-1', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('锑化氢 三氢化锑;锑化三氢', NULL, '7803-52-3', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硒化氢', NULL, '7783-07-5', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 丙烯醛（已修复）
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('丙烯醛 烯丙醛;败脂醛', NULL, '107-02-8', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 丙酮氰醇（CAS 75-86-5，Q=20）已修复：Q 不允许 NULL
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('丙酮氰醇 2-羟基异丁腈;氰丙醇', NULL, '75-86-5', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 氟化氢（CAS 7664-39-3，Q=1）已修复：原文本把“1”拼进 name，且 Q=NULL
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氟化氢', NULL, '7664-39-3', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 环氧氯丙烷（CAS 106-89-8，Q=20）已修复：原 Q=NULL
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('环氧氯丙烷 1-氯-2,3-环氧丙烷;3-氯-1,2-环氧丙烷', NULL, '106-89-8', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 环氧溴丙烷（CAS 3132-64-7，Q=20）已修复：原 Q=NULL
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('环氧溴丙烷 3-溴-1,2-环氧丙烷;溴甲基环氧乙烷;表溴醇', NULL, '3132-64-7', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('甲苯二异氰酸酯 二异氰酸甲苯酯;TDI', NULL, '26471-62-5', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('一氯化硫 氯化硫', NULL, '10025-67-9', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氰化氢 无水氢氰酸', NULL, '74-90-8', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('三氧化硫 硫酸酐', NULL, '7446-11-9', 75.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('3-氨基丙烯 烯丙胺', NULL, '107-11-9', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('溴 溴素', NULL, '7726-95-6', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('乙撑亚胺 吖丙啶;1-氮杂环丙烷;氮丙啶', NULL, '151-56-4', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('异氰酸甲酯 甲基异氰酸酯', NULL, '624-83-9', 0.75, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('叠氮化钡 叠氮钡', NULL, '18810-58-7', 0.5, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('叠氮化铅', NULL, '13424-46-9', 0.5, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('雷汞 二雷酸汞;雷酸汞', NULL, '628-86-4', 0.5, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('三硝基苯甲醚 三硝基茴香醚', NULL, '28653-16-9', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 2,4,6-三硝基甲苯（TNT，CAS 118-96-7，Q=5）已修复：原 Q=NULL
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('2,4,6-三硝基甲苯 梯恩梯;TNT', NULL, '118-96-7', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 硝化甘油（CAS 55-63-0，Q=1）已修复：原 Q=NULL
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硝化甘油 甘油三硝酸酯', NULL, '55-63-0', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- ========= 下面这几条属于 PDF 抽取跨行断裂（CAS/名称/Q 混在一起），会导致持续报错/脏数据 =========
-- 建议：先跳过，后续按 GB 表1手工补齐成“干净的单条记录”
-- INSERT INTO chemicals (...) VALUES ('硝化纤维素[干的或含水(或乙醇)<25%] 1 硝化纤维素(未改型的', NULL, NULL, NULL, 't', ...);
-- INSERT INTO chemicals (...) VALUES ('1 或增塑的,含增塑剂<18%) 硝化棉', NULL, '9004-70-0', NULL, 't', ...);
-- INSERT INTO chemicals (...) VALUES ('硝化纤维素(含水≥25%) 50 硝化纤维素溶液', NULL, NULL, NULL, 't', ...);
-- INSERT INTO chemicals (...) VALUES ('硝化棉溶液 50 ... 硝酸铵(含可燃物>0.2%', NULL, '9004-70-0', NULL, 't', ...);
-- INSERT INTO chemicals (...) VALUES ('包括以碳计算的任何有机物, 5 但不包括任何其他添加剂)', NULL, '6484-52-2', NULL, 't', ...);

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硝化纤维素(含乙醇≥25%)', NULL, NULL, 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硝化纤维素(含氮≤12.6%)', NULL, NULL, 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硝酸铵(含可燃物≤0.2%)', NULL, '6484-52-2', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硝酸铵肥料(含可燃物≤0.4%)', NULL, NULL, 200.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硝酸钾', NULL, '7757-79-1', 1000.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('1,3-丁二烯 联乙烯', NULL, '106-99-0', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 二甲醚（Q=50）+ 甲烷（Q=50）原抽取拼接导致 Q=NULL，这里拆成两条干净记录
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('二甲醚 甲醚', NULL, '115-10-6', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('甲烷', NULL, '74-82-8', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 天然气（Q=50）原抽取 Q=NULL，这里修复
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('甲烷,天然气', NULL, '8006-14-2', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氯乙烯 乙烯基氯', NULL, '75-01-4', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 氢（Q=5）原抽取把 5 拼到 name 且 Q=NULL，这里修复
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氢 氢气', NULL, '1333-74-0;68476-85-7', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 液化石油气（Q=50）原抽取 Q=NULL，这里修复（CAS 可能为丙烷/丁烷）
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('液化石油气(含丙烷、丁烷及其混合物) 石油气(液化的)', NULL, '74-98-6;106-97-8', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('一甲胺 氨基甲烷;甲胺', NULL, '74-89-5', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('乙炔 电石气', NULL, '74-86-2', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('乙烯', NULL, '74-85-1', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氧(压缩的或液化的) 液氧;氧气', NULL, '7782-44-7', 200.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('苯 纯苯', NULL, '71-43-2', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('苯乙烯 乙烯苯', NULL, '100-42-5', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('丙酮 二甲基酮', NULL, '67-64-1', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('2-丙烯腈 丙烯腈;乙烯基氰;氰基乙烯', NULL, '107-13-1', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('二硫化碳', NULL, '75-15-0', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('环己烷 六氢化苯', NULL, '110-82-7', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('1,2-环氧丙烷 氧化丙烯;甲基环氧乙烷', NULL, '75-56-9', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('甲苯 甲基苯;苯基甲烷', NULL, '108-88-3', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('甲醇 木醇;木精', NULL, '67-56-1', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('汽油(乙醇汽油、甲醇汽油) (汽油)', NULL, '86290-81-5', 200.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('乙醇 酒精', NULL, '64-17-5', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('乙醚 二乙基醚', NULL, '60-29-7', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('乙酸乙酯 醋酸乙酯', NULL, '141-78-6', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('正己烷 己烷', NULL, '110-54-3', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 过乙酸（CAS 79-21-0，Q=10）已修复：原 Q=NULL
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('过乙酸 过醋酸;过氧乙酸;乙酰过氧化氢', NULL, '79-21-0', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- 过氧化甲基乙基酮（MEKP，CAS 1338-23-4）原抽取 Q=NULL 且跨行描述，这里先按“有效氧含量10%~10.7%”的项 Q=10 处理
-- 如果你希望更严格区分（A型稀释剂≥48% 等），建议拆成多条标准记录
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('过氧化甲基乙基酮(有效氧含量10%~10.7%)', NULL, '1338-23-4', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('白磷 黄磷', NULL, '12185-10-3', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('烷基铝 三烷基铝', NULL, NULL, 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('戊硼烷 五硼烷', NULL, '19624-22-7', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('过氧化钾', NULL, '17014-71-0', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('过氧化钠 双氧化钠;二氧化钠', NULL, '1313-60-6', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氯酸钾', NULL, '3811-04-9', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('氯酸钠', NULL, '7775-09-9', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('发烟硝酸', NULL, '52583-42-3', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硝酸(发红烟的除外,含硝酸>70%)', NULL, '7697-37-2', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('硝酸胍 硝酸亚氨脲', NULL, '506-93-4', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('碳化钙 电石', NULL, '75-20-7', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('钾 金属钾', NULL, '7440-09-7', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('钠 金属钠', NULL, '7440-23-5', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- ==================================================
-- 表3：毒性气体 β -> 回填 chemicals.beta（可选）
-- 重要：仅当你 chemicals 已新增 beta/beta_source/gb_version 字段才执行！
-- 如果你还没迁移字段，请把下面整段注释掉。
-- ==================================================
/*
UPDATE chemicals SET beta=2.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '一氧化碳%';
UPDATE chemicals SET beta=2.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '二氧化硫%';
UPDATE chemicals SET beta=2.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '氨%';
UPDATE chemicals SET beta=2.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '环氧乙烷%';
UPDATE chemicals SET beta=3.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '氯化氢%';
UPDATE chemicals SET beta=3.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '溴甲烷%';
UPDATE chemicals SET beta=4.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '氯%';
UPDATE chemicals SET beta=5.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '硫化氢%';
UPDATE chemicals SET beta=5.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '氟化氢%';
UPDATE chemicals SET beta=10.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '二氧化氮%';
UPDATE chemicals SET beta=10.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '氰化氢%';
UPDATE chemicals SET beta=20.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '碳酰氯%';
UPDATE chemicals SET beta=20.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '磷化氢%';
UPDATE chemicals SET beta=20.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '异氰酸甲酯%';
*/

-- 完成

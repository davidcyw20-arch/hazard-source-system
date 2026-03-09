SET NAMES utf8mb4;
-- GB 18218-2018 鍏ㄩ噺绉嶅瓙鏁版嵁锛堣嚜鍔ㄤ粠 PDF 鎶藉彇鐢熸垚锛?-- 鐢熸垚鏃堕棿: 2026-01-05 14:58:31

-- === 鏍囧噯鍙傛暟琛紙濡備綘宸茬敤 Alembic 寤鸿繃鍚屽悕琛紝鍙垹闄ゆ湰娈?CREATE TABLE锛?===
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

-- === 琛?锛氭毚闇蹭汉鍛樻牎姝ｇ郴鏁?伪 ===
INSERT INTO gb18218_alpha_rules (gb_version, min_people, max_people, alpha) VALUES
('GB18218-2018',100,NULL,2.0),
('GB18218-2018',50,99,1.5),
('GB18218-2018',30,49,1.2),
('GB18218-2018',1,29,1.0),
('GB18218-2018',0,0,0.5)
ON DUPLICATE KEY UPDATE alpha=VALUES(alpha);

-- === 琛?锛歊 鍊煎垎绾ц鍒?===
INSERT INTO gb18218_level_rules (gb_version, level, r_min, r_max) VALUES
('GB18218-2018','涓€绾?,100,NULL),
('GB18218-2018','浜岀骇',50,100),
('GB18218-2018','涓夌骇',10,50),
('GB18218-2018','鍥涚骇',0,10)
ON DUPLICATE KEY UPDATE r_min=VALUES(r_min), r_max=VALUES(r_max);

-- === 琛?锛氬嵄闄╁寲瀛﹀搧绫诲埆涓寸晫閲忥紙鏈垪鍚嶆椂浣跨敤锛?===
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

-- === 琛?锛氬嵄闄╁寲瀛﹀搧绫诲埆 尾锛堣〃3鏈鐩栨椂浣跨敤锛?===
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

-- === rule_sets锛氬啓鍏?GB18218-2018 绛夌骇瑙勫垯锛堝吋瀹逛綘鐜版湁 rule_sets.levels JSON锛?===
INSERT INTO rule_sets (name, is_active, levels, created_at, updated_at)
VALUES ('GB18218-2018', 1, '[{"level":"涓€绾?,"min":100,"max":null},{"level":"浜岀骇","min":50,"max":100},{"level":"涓夌骇","min":10,"max":50},{"level":"鍥涚骇","min":0,"max":10}]', NOW(), NOW())
ON DUPLICATE KEY UPDATE is_active=VALUES(is_active), levels=VALUES(levels), updated_at=NOW();

-- === 琛?锛氬嵄闄╁寲瀛﹀搧鍚嶇О鍙婂叾涓寸晫閲?-> chemicals ===
-- 璇存槑锛氭湰鑴氭湰灏嗏€滃悕绉?鍒悕鈥濇暣浣撳啓鍏?chemicals.name锛堜笉鎷嗗垎鍒悕鍒楋級锛孋AS 鍙兘涓哄鍊肩敤鍒嗗彿鍒嗛殧銆?INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘?娑叉皑;姘ㄦ皵', NULL, '7664-41-7', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('浜屾盁鍖栨哀 涓€姘у寲浜屾盁', NULL, '7783-41-7', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('浜屾哀鍖栨爱', NULL, '10102-44-0', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('浜屾哀鍖栫～ 浜氱～閰搁厫', NULL, '7446-09-5', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘?, NULL, '7782-41-4', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纰抽叞姘?鍏夋皵', NULL, '75-44-5', 0.3, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐜哀涔欑兎 姘у寲涔欑儻', NULL, '75-21-8', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐢查啗(鍚噺>90%) 铓侀啗', NULL, '50-00-0', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纾峰寲姘?纾峰寲涓夋阿;鑶?, NULL, '7803-51-2', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭寲姘?, NULL, '7783-06-4', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘寲姘?鏃犳按)', NULL, '7647-01-0', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘?娑叉隘;姘皵', NULL, '7782-50-5', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐓ゆ皵(CO,CO鍜孒 銆丆H 鐨勬贩鍚堢墿绛?', NULL, NULL, 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐮峰寲姘?鐮峰寲涓夋阿銆佽儌', NULL, '7784-42-1', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('閿戝寲姘?涓夋阿鍖栭攽;閿戝寲涓夋阿', NULL, '7803-52-3', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭掑寲姘?, NULL, '7783-07-5', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at)
VALUES ('涓欑儻閱?, NULL, '107-02-8', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW())
ON DUPLICATE KEY UPDATE
critical_quantity=VALUES(critical_quantity),
unit=VALUES(unit),
source_standard=VALUES(source_standard),
updated_at=NOW();

INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涓欓叜姘伴唶 20 2-缇熷熀寮備竵鑵?姘颁笝閱?, NULL, '75-86-5', NULL, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涓欑儻閱?鐑笝閱?璐ヨ剛閱?, NULL, '107-02-8', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘熷寲姘?1 鐜哀姘笝鐑?, NULL, '7664-39-3', NULL, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('1-姘?2,3-鐜哀涓欑兎 20 (3-姘?1,2-鐜哀涓欑兎) 鐜哀婧翠笝鐑?, NULL, '106-89-8', NULL, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('3-婧?1,2-鐜哀涓欑兎 20 婧寸敳鍩虹幆姘т箼鐑?琛ㄦ捍閱?, NULL, '3132-64-7', NULL, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐢茶嫰浜屽紓姘伴吀閰?浜屽紓姘伴吀鐢茶嫰閰?TDI', NULL, '26471-62-5', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涓€姘寲纭?姘寲纭?, NULL, '10025-67-9', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘板寲姘?鏃犳按姘㈡鞍閰?, NULL, '74-90-8', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涓夋哀鍖栫～ 纭吀閰?, NULL, '7446-11-9', 75.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('3-姘ㄥ熀涓欑儻 鐑笝鑳?, NULL, '107-11-9', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('婧?婧寸礌', NULL, '7726-95-6', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涔欐拺浜氳兒 鍚栦笝鍟?1-姘潅鐜笝鐑?姘笝鍟?, NULL, '151-56-4', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('寮傛鞍閰哥敳閰?鐢插熀寮傛鞍閰搁叝', NULL, '624-83-9', 0.75, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鍙犳爱鍖栭挕 鍙犳爱閽?, NULL, '18810-58-7', 0.5, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鍙犳爱鍖栭搮', NULL, '13424-46-9', 0.5, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('闆锋睘 浜岄浄閰告睘;闆烽吀姹?, NULL, '628-86-4', 0.5, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涓夌鍩鸿嫰鐢查啔 涓夌鍩鸿尨棣欓啔', NULL, '28653-16-9', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('2,4,6-涓夌鍩虹敳鑻?姊仼姊?TNT 5 纭濆寲涓欎笁閱?, NULL, '118-96-7', NULL, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) $11, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭濆寲绾ょ淮绱燵骞茬殑鎴栧惈姘?鎴栦箼閱?<25%] 1 纭濆寲绾ょ淮绱?鏈敼鍨嬬殑', NULL, NULL, NULL, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('1 鎴栧濉戠殑,鍚濉戝墏<18%) 纭濆寲妫?, NULL, '9004-70-0', NULL, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭濆寲绾ょ淮绱?鍚箼閱団墺25%)', NULL, NULL, 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭濆寲绾ょ淮绱?鍚爱鈮?2.6%)', NULL, NULL, 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭濆寲绾ょ淮绱?鍚按鈮?5%) 50 纭濆寲绾ょ淮绱犳憾娑?, NULL, NULL, NULL, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) $150, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) $15, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭濋吀閾?鍚彲鐕冪墿鈮?.2%)', NULL, '6484-52-2', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭濋吀閾佃偉鏂?鍚彲鐕冪墿鈮?.4%)', NULL, NULL, 200.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭濋吀閽?, NULL, '7757-79-1', 1000.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('1,3-涓佷簩鐑?鑱斾箼鐑?, NULL, '106-99-0', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) $150, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) $150, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘箼鐑?涔欑儻鍩烘隘', NULL, '75-01-4', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) $15, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) $150, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涓€鐢茶兒 姘ㄥ熀鐢茬兎;鐢茶兒', NULL, '74-89-5', 5.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涔欑倲 鐢电煶姘?, NULL, '74-86-2', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涔欑儻', NULL, '74-85-1', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘?鍘嬬缉鐨勬垨娑插寲鐨? 娑叉哀;姘ф皵', NULL, '7782-44-7', 200.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鑻?绾嫰', NULL, '71-43-2', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鑻箼鐑?涔欑儻鑻?, NULL, '100-42-5', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涓欓叜 浜岀敳鍩洪叜', NULL, '67-64-1', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('2-涓欑儻鑵?涓欑儻鑵?涔欑儻鍩烘鞍;姘板熀涔欑儻', NULL, '107-13-1', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('浜岀～鍖栫⒊', NULL, '75-15-0', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐜繁鐑?鍏阿鍖栬嫰', NULL, '110-82-7', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('1,2-鐜哀涓欑兎 姘у寲涓欑儻;鐢插熀鐜哀涔欑兎', NULL, '75-56-9', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐢茶嫰 鐢插熀鑻?鑻熀鐢茬兎', NULL, '108-88-3', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐢查唶 鏈ㄩ唶;鏈ㄧ簿', NULL, '67-56-1', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姹芥补(涔欓唶姹芥补銆佺敳閱囨苯娌? (姹芥补)', NULL, '86290-81-5', 200.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涔欓唶 閰掔簿', NULL, '64-17-5', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涔欓啔 浜屼箼鍩洪啔', NULL, '60-29-7', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('涔欓吀涔欓叝 閱嬮吀涔欓叝', NULL, '141-78-6', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姝ｅ繁鐑?宸辩兎', NULL, '110-54-3', 500.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) $110, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) $110, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐧界７ 榛勭７', NULL, '12185-10-3', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鐑峰熀閾?涓夌兎鍩洪摑', NULL, NULL, 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鎴婄〖鐑?浜旂〖鐑?, NULL, '19624-22-7', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('杩囨哀鍖栭捑', NULL, '17014-71-0', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('杩囨哀鍖栭挔 鍙屾哀鍖栭挔;浜屾哀鍖栭挔', NULL, '1313-60-6', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘吀閽?, NULL, '3811-04-9', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('姘吀閽?, NULL, '7775-09-9', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('鍙戠儫纭濋吀', NULL, '52583-42-3', 20.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭濋吀(鍙戠孩鐑熺殑闄ゅ,鍚閰?70%)', NULL, '7697-37-2', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纭濋吀鑳?纭濋吀浜氭皑鑴?, NULL, '506-93-4', 50.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('纰冲寲閽?鐢电煶', NULL, '75-20-7', 100.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('閽?閲戝睘閽?, NULL, '7440-09-7', 1.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();
INSERT INTO chemicals (name, category, cas_no, critical_quantity, unit, source_standard, created_at, updated_at) VALUES ('閽?閲戝睘閽?, NULL, '7440-23-5', 10.0, 't', 'GB18218-2018 Table1', NOW(), NOW()) ON DUPLICATE KEY UPDATE critical_quantity=VALUES(critical_quantity), unit=VALUES(unit), source_standard=VALUES(source_standard), updated_at=NOW();

-- === 琛?锛氭瘨鎬ф皵浣?尾 -> 鍥炲～ chemicals.beta锛堣嫢浣犲凡鍦?chemicals 澧炲姞 beta/beta_source/gb_version 瀛楁锛?===
-- 鑻ヤ綘鐨?chemicals 琛ㄨ繕鏈姞 beta 瀛楁锛岃鍏堟墽琛屾暟鎹簱杩佺Щ鎴栧垹闄ゆ湰娈?UPDATE銆?UPDATE chemicals SET beta=2.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '涓€姘у寲纰?';
UPDATE chemicals SET beta=2.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '浜屾哀鍖栫～%';
UPDATE chemicals SET beta=2.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '姘?';
UPDATE chemicals SET beta=2.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '鐜哀涔欑兎%';
UPDATE chemicals SET beta=3.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '姘寲姘?';
UPDATE chemicals SET beta=3.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '婧寸敳鐑?';
UPDATE chemicals SET beta=4.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '姘?';
UPDATE chemicals SET beta=5.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '纭寲姘?';
UPDATE chemicals SET beta=5.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '姘熷寲姘?';
UPDATE chemicals SET beta=10.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '浜屾哀鍖栨爱%';
UPDATE chemicals SET beta=10.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '姘板寲姘?';
UPDATE chemicals SET beta=20.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '纰抽叞姘?';
UPDATE chemicals SET beta=20.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '纾峰寲姘?';
UPDATE chemicals SET beta=20.0, beta_source='TABLE3', gb_version='GB18218-2018' WHERE name LIKE '寮傛鞍閰哥敳閰?';

-- 瀹屾垚

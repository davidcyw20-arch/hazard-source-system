from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..extensions import db
from ..models import CategoryBeta, CategoryThreshold, Chemical, GB_18218_2018


GB_VERSION_ALIASES = (GB_18218_2018, "GB18218-2018")


@dataclass(frozen=True)
class GB18218BetaSeedSummary:
    category_betas_upserted: int
    category_thresholds_upserted: int
    chemicals_table3_beta_updated: int
    chemicals_table4_beta_filled: int


def seed_gb18218_beta_and_thresholds(*, gb_version: str = GB_18218_2018) -> GB18218BetaSeedSummary:
    """
    写入 GB 18218-2018 的 β/阈值参数，并为 chemicals 填充 β：
    - 表3（毒性气体专用 β）：按 CAS 更新 chemicals.beta/beta_source（仅填充 beta 为空的记录）
    - 表4（通用类别 β）：upsert 到 category_betas
    - 类别阈值（用户提供的列表）：upsert 到 category_thresholds
    - chemicals 若 beta 为空且 hazard_category_symbol 可匹配，则按表4补齐 beta（beta_source=TABLE4）
    """

    now = datetime.utcnow()

    # 表4：通用类别 β
    table4_category_betas = [
        ("J1", 4.0, "急性毒性-类别1（气体）"),
        ("J2", 2.0, "急性毒性-类别1（固体/液体）"),
        ("J3", 2.0, "急性毒性-类别2/3（气体）"),
        ("J4", 2.0, "急性毒性-类别2/3（吸入途径液体，沸点≤35℃）"),
        ("J5", 1.0, "急性毒性-类别2（液体/固体）"),
        ("W1.1", 2.0, "爆炸物-不稳定爆炸物/1.1 项"),
        ("W1.2", 2.0, "爆炸物-1.2/1.3/1.5/1.6 项"),
        ("W1.3", 2.0, "爆炸物-1.4 项"),
        ("W2", 1.5, "易燃气体-类别1/2"),
        ("W3", 1.0, "气溶胶-类别1/2"),
        ("W4", 1.0, "氧化性气体-类别1"),
        ("W5.1", 1.5, "易燃液体-类别1；类别2/3（工作温度高于沸点）"),
        ("W5.2", 1.0, "易燃液体-类别2/3（特殊工艺条件）"),
        ("W5.3", 1.0, "易燃液体-其他类别2"),
        ("W5.4", 1.0, "易燃液体-其他类别3"),
        ("W6.1", 1.5, "自反应物质和混合物-A/B 型"),
        ("W6.2", 1.0, "自反应物质和混合物-C/D/E 型"),
        ("W7.1", 1.5, "有机过氧化物-A/B 型"),
        ("W7.2", 1.0, "有机过氧化物-C/D/E/F 型"),
        ("W8", 1.0, "自燃液体和自燃固体-类别1"),
        ("W9.1", 1.0, "氧化性固体和液体-类别1"),
        ("W9.2", 1.0, "氧化性固体和液体-类别2/3"),
        ("W10", 1.0, "易燃固体-类别1"),
        ("W11", 1.0, "遇水放出易燃气体-类别1/2"),
    ]

    # 类别 -> 阈值（t）
    category_thresholds = [
        ("J1", 5.0, "t", "急性毒性-类别1（气体）"),
        ("J2", 50.0, "t", "急性毒性-类别1（固体/液体）"),
        ("J3", 50.0, "t", "急性毒性-类别2/3（气体）"),
        ("J4", 50.0, "t", "急性毒性-类别2/3（吸入途径液体，沸点≤35℃）"),
        ("J5", 500.0, "t", "急性毒性-类别2（液体/固体）"),
        ("W1.1", 1.0, "t", "爆炸物-不稳定爆炸物/1.1 项"),
        ("W1.2", 10.0, "t", "爆炸物-1.2/1.3/1.5/1.6 项"),
        ("W1.3", 50.0, "t", "爆炸物-1.4 项"),
        ("W2", 10.0, "t", "易燃气体-类别1/2"),
        ("W3", 150.0, "t", "气溶胶-类别1/2（净重）"),
        ("W4", 50.0, "t", "氧化性气体-类别1"),
        ("W5.1", 10.0, "t", "易燃液体-类别1；类别2/3（工作温度高于沸点）"),
        ("W5.2", 50.0, "t", "易燃液体-类别2/3（特殊工艺条件）"),
        ("W5.3", 1000.0, "t", "易燃液体-其他类别2"),
        ("W5.4", 5000.0, "t", "易燃液体-其他类别3"),
        ("W6.1", 10.0, "t", "自反应物质和混合物-A/B 型"),
        ("W6.2", 50.0, "t", "自反应物质和混合物-C/D/E 型"),
        ("W7.1", 10.0, "t", "有机过氧化物-A/B 型"),
        ("W7.2", 50.0, "t", "有机过氧化物-C/D/E/F 型"),
        ("W8", 50.0, "t", "自燃液体和自燃固体-类别1"),
        ("W9.1", 50.0, "t", "氧化性固体和液体-类别1"),
        ("W9.2", 200.0, "t", "氧化性固体和液体-类别2/3"),
        ("W10", 200.0, "t", "易燃固体-类别1"),
        ("W11", 200.0, "t", "遇水放出易燃气体-类别1/2"),
    ]

    # 表3：毒性气体专用 β（按 CAS）
    table3_cas_betas = [
        ("630-08-0", 2.0, "一氧化碳"),
        ("7446-09-5", 2.0, "二氧化硫"),
        ("7664-41-7", 2.0, "氨"),
        ("75-21-8", 2.0, "环氧乙烷"),
        ("7647-01-0", 3.0, "氯化氢"),
        ("74-83-9", 3.0, "溴甲烷"),
        ("7782-50-5", 4.0, "氯"),
        ("7783-06-4", 5.0, "硫化氢"),
        ("7664-39-3", 5.0, "氟化氢"),
        ("10102-44-0", 10.0, "二氧化氮"),
        ("74-90-8", 10.0, "氰化氢"),
        ("75-44-5", 20.0, "碳酰氯/光气"),
        ("7803-51-2", 20.0, "磷化氢"),
        ("624-83-9", 20.0, "异氰酸甲酯"),
    ]

    upserted_betas = 0
    upserted_thresholds = 0
    updated_table3 = 0
    filled_table4 = 0

    with db.session.begin_nested():
        for symbol, beta, note in table4_category_betas:
            existing_b = CategoryBeta.query.filter_by(
                gb_version=gb_version, category_symbol=symbol
            ).first()
            if existing_b:
                existing_b.beta = float(beta)
                existing_b.beta_source = "TABLE4"
                existing_b.source = f"{gb_version} 表4"
                existing_b.note = note
            else:
                db.session.add(
                    CategoryBeta(
                        gb_version=gb_version,
                        category_symbol=symbol,
                        beta=float(beta),
                        beta_source="TABLE4",
                        source=f"{gb_version} 表4",
                        note=note,
                    )
                )
            upserted_betas += 1

        for symbol, qty, unit, note in category_thresholds:
            existing_q = CategoryThreshold.query.filter_by(
                gb_version=gb_version, category_symbol=symbol
            ).first()
            if existing_q:
                existing_q.threshold_quantity = float(qty)
                existing_q.unit = unit
                existing_q.source = f"{gb_version} 表2"
                existing_q.note = note
            else:
                db.session.add(
                    CategoryThreshold(
                        gb_version=gb_version,
                        category_symbol=symbol,
                        threshold_quantity=float(qty),
                        unit=unit,
                        source=f"{gb_version} 表2",
                        note=note,
                    )
                )
            upserted_thresholds += 1

        for cas_no, beta, name in table3_cas_betas:
            updated_table3 += (
                Chemical.query.filter(
                    Chemical.cas_no == cas_no,
                    Chemical.gb_version.in_(GB_VERSION_ALIASES),
                    Chemical.beta.is_(None),
                )
                .update(
                    {
                        Chemical.beta: float(beta),
                        Chemical.beta_source: "TABLE3",
                        Chemical.updated_at: now,
                    },
                    synchronize_session=False,
                )
                or 0
            )

        # Fill remaining chemicals.beta from Table4 when hazard_category_symbol is present.
        # Use raw SQL for an efficient JOIN update (still within the same transaction).
        res = db.session.execute(
            text(
                """
                UPDATE chemicals c
                JOIN category_betas b
                  ON b.gb_version = :gb_version
                 AND b.category_symbol = c.hazard_category_symbol
                SET c.beta = b.beta,
                    c.beta_source = COALESCE(c.beta_source, b.beta_source, 'TABLE4'),
                    c.updated_at = :now
                WHERE c.gb_version IN (:gb_v1, :gb_v2)
                  AND c.beta IS NULL
                  AND c.hazard_category_symbol IS NOT NULL
                """
            ),
            {"gb_version": gb_version, "gb_v1": GB_VERSION_ALIASES[0], "gb_v2": GB_VERSION_ALIASES[1], "now": now},
        )
        filled_table4 = int(res.rowcount or 0)

    return GB18218BetaSeedSummary(
        category_betas_upserted=upserted_betas,
        category_thresholds_upserted=upserted_thresholds,
        chemicals_table3_beta_updated=updated_table3,
        chemicals_table4_beta_filled=filled_table4,
    )


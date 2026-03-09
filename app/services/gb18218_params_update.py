from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import or_

from ..extensions import db
from ..models import CategoryBeta, CategoryThreshold, Chemical, GB_18218_2018


@dataclass(frozen=True)
class GB18218UpdateSummary:
    category_betas_upserted: int
    category_thresholds_upserted: int
    chemicals_beta_updated: int


def apply_gb18218_table2_table3_table4_updates(
    *,
    gb_version: str = GB_18218_2018,
) -> GB18218UpdateSummary:
    """
    根据 GB 18218-2018（用户提供的工程化整理）写入：
    - 表2：类别 -> 临界量（category_thresholds）
    - 表4：类别 -> β（category_betas）
    - 表3：部分毒性气体 β（写入 chemicals.beta/beta_source，按 CAS 匹配）
    """

    now = datetime.utcnow()
    category_betas = [
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
        ("W8", 1.0, "自燃液体/固体-类别1"),
        ("W9.1", 1.0, "氧化性固体和液体-类别1"),
        ("W9.2", 1.0, "氧化性固体和液体-类别2/3"),
        ("W10", 1.0, "易燃固体-类别1"),
        ("W11", 1.0, "遇水放出易燃气体的物质和混合物-类别1/2"),
    ]

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
        ("W8", 50.0, "t", "自燃液体/固体-类别1"),
        ("W9.1", 50.0, "t", "氧化性固体和液体-类别1"),
        ("W9.2", 200.0, "t", "氧化性固体和液体-类别2/3"),
        ("W10", 200.0, "t", "易燃固体-类别1"),
        ("W11", 200.0, "t", "遇水放出易燃气体的物质和混合物-类别1/2"),
    ]

    # 表3：毒性气体 β（优先采用，按 CAS 匹配；若库内未填 CAS，可对“非歧义名称”做回退匹配）
    table3 = [
        ("630-08-0", "一氧化碳", 2.0, True),
        ("7446-09-5", "二氧化硫", 2.0, True),
        ("7664-41-7", "氨", 2.0, True),  # 可能写成“液氨/氨气”，用包含匹配
        ("75-21-8", "环氧乙烷", 2.0, True),
        ("7647-01-0", "氯化氢", 3.0, True),
        ("74-83-9", "溴甲烷", 3.0, True),
        ("7782-50-5", "氯", 4.0, False),  # “氯”歧义较大，仅按 CAS 更新
        ("7783-06-4", "硫化氢", 5.0, True),
        ("7664-39-3", "氟化氢", 5.0, True),
        ("10102-44-0", "二氧化氮", 10.0, True),
        ("74-90-8", "氰化氢", 10.0, True),
        ("75-44-5", "碳酰氯", 20.0, True),  # 光气
        ("7803-51-2", "磷化氢", 20.0, True),
        ("624-83-9", "异氰酸甲酯", 20.0, True),
    ]

    upserted_betas = 0
    upserted_thresholds = 0
    updated_chem = 0

    with db.session.begin_nested():
        for symbol, beta, note in category_betas:
            stmt = mysql_insert(CategoryBeta.__table__).values(
                gb_version=gb_version,
                category_symbol=symbol,
                beta=float(beta),
                beta_source="TABLE4",
                source=f"{gb_version} 表4",
                note=note,
            )
            result = db.session.execute(
                stmt.on_duplicate_key_update(
                    beta=stmt.inserted.beta,
                    beta_source=stmt.inserted.beta_source,
                    source=stmt.inserted.source,
                    note=stmt.inserted.note,
                )
            )
            upserted_betas += int(result.rowcount or 0)

        for symbol, qty, unit, note in category_thresholds:
            stmt = mysql_insert(CategoryThreshold.__table__).values(
                gb_version=gb_version,
                category_symbol=symbol,
                threshold_quantity=float(qty),
                unit=unit,
                source=f"{gb_version} 表2",
                note=note,
            )
            result = db.session.execute(
                stmt.on_duplicate_key_update(
                    threshold_quantity=stmt.inserted.threshold_quantity,
                    unit=stmt.inserted.unit,
                    source=stmt.inserted.source,
                    note=stmt.inserted.note,
                )
            )
            upserted_thresholds += int(result.rowcount or 0)

        for cas_no, name_keyword, beta, allow_name_fallback in table3:
            updated = (
                Chemical.query.filter(Chemical.cas_no == cas_no)
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
            updated_chem += updated

            if updated == 0 and allow_name_fallback:
                # Fallback for data sets where CAS is missing but names contain the keyword.
                updated_chem += (
                    Chemical.query.filter(
                        or_(
                            Chemical.name == name_keyword,
                            Chemical.name.like(f"%{name_keyword}%"),
                        )
                    )
                    .update(
                        {
                            Chemical.beta: float(beta),
                            Chemical.beta_source: "TABLE3(name)",
                            Chemical.updated_at: now,
                        },
                        synchronize_session=False,
                    )
                    or 0
                )

    return GB18218UpdateSummary(
        category_betas_upserted=upserted_betas,
        category_thresholds_upserted=upserted_thresholds,
        chemicals_beta_updated=updated_chem,
    )

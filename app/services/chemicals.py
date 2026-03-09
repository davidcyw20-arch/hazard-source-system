from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func

from ..extensions import db
from ..models import Chemical, StorageRecord


@dataclass(frozen=True)
class DedupSummary:
    groups: int
    merged_rows: int
    updated_storage_records: int


def dedup_chemicals_keep_latest() -> DedupSummary:
    """
    去重规则：
    - 以 (name, cas_no) 分组（MySQL 下 cas_no=NULL 也会被分为同组）
    - 每组保留 updated_at/id 最新的一条
    - 将 storage_records.chemical_id 指向保留行，再删除多余行
    """

    group_count = 0
    merged_rows = 0
    updated_storage = 0

    dups = (
        db.session.query(Chemical.name, Chemical.cas_no, func.count(Chemical.id).label("cnt"))
        .group_by(Chemical.name, Chemical.cas_no)
        .having(func.count(Chemical.id) > 1)
        .all()
    )

    for name, cas_no, _cnt in dups:
        group_count += 1
        query = Chemical.query.filter(Chemical.name == name)
        if cas_no is None:
            query = query.filter(Chemical.cas_no.is_(None))
        else:
            query = query.filter(Chemical.cas_no == cas_no)

        rows = query.order_by(Chemical.updated_at.desc(), Chemical.id.desc()).all()
        if len(rows) <= 1:
            continue

        keep = rows[0]
        drop_ids = [r.id for r in rows[1:]]
        merged_rows += len(drop_ids)

        updated_storage += (
            StorageRecord.query.filter(StorageRecord.chemical_id.in_(drop_ids))
            .update({StorageRecord.chemical_id: keep.id}, synchronize_session=False)
            or 0
        )
        Chemical.query.filter(Chemical.id.in_(drop_ids)).delete(synchronize_session=False)

    return DedupSummary(groups=group_count, merged_rows=merged_rows, updated_storage_records=updated_storage)

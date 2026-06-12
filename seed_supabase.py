"""Supabase 최초 시드 스크립트.

실행 전제: supabase_schema.sql을 SQL Editor에서 실행해 테이블이 존재해야 함.
실행: ./venv/Scripts/python.exe seed_supabase.py  (프로젝트 루트에서)

- 각 테이블이 비어 있을 때만 시드를 넣는다 (재실행 안전).
- 조치 사진 Storage 버킷(action-photos)도 없으면 생성한다.
"""
from __future__ import annotations

import sys
import tomllib

from supabase import create_client

from lib import data


def main() -> int:
    cfg = tomllib.load(open(".streamlit/secrets.toml", "rb"))["supabase"]
    db = create_client(cfg["url"], cfg["service_role_key"])

    # 1) Storage 버킷
    try:
        db.storage.create_bucket(data.ACTION_PHOTO_BUCKET)
        print(f"bucket created: {data.ACTION_PHOTO_BUCKET}")
    except Exception as e:
        if "already exists" in str(e).lower() or "Duplicate" in str(e):
            print(f"bucket exists: {data.ACTION_PHOTO_BUCKET}")
        else:
            print(f"bucket error: {e}")

    # 2) 테이블 시드 (비어 있을 때만)
    def seed_table(table: str, rows: list[dict]) -> None:
        try:
            existing = db.table(table).select("*", count="exact").limit(1).execute()
        except Exception as e:
            print(f"[ERROR] {table}: 테이블 조회 실패 — supabase_schema.sql을 먼저 실행하세요. ({e})")
            raise SystemExit(1)
        if (existing.count or 0) > 0:
            print(f"skip {table}: {existing.count} rows already")
            return
        db.table(table).insert(rows).execute()
        print(f"seeded {table}: {len(rows)} rows")

    seed_table("equipment", [{
        "equipment_id": e.equipment_id, "location_id": e.location_id,
        "category": e.category, "equipment_name": e.equipment_name,
        "serial": e.serial, "qr_status": e.qr_status,
        "last_inspection": e.last_inspection.isoformat() if e.last_inspection else None,
        "health_status": e.health_status, "floor": e.floor, "zone": e.zone,
        "pixel_x": e.pixel_x, "pixel_y": e.pixel_y,
        "inspection_types": e.inspection_types or [],
    } for e in data._seed_equipment()])

    seed_table("inspection_tasks", [{
        "task_id": t.task_id, "equipment_label": t.equipment_label,
        "task_type": t.task_type, "assignee": t.assignee,
        "due_date": t.due_date.isoformat(), "status": t.status,
        "floor": t.floor, "zone": t.zone, "note": t.note,
    } for t in data._seed_tasks()])

    seed_table("deficiencies", [{
        "deficiency_id": d.deficiency_id,
        "inspection_date": d.inspection_date.isoformat(),
        "inspector": d.inspector, "floor": d.floor, "zone": d.zone,
        "inspection_types": list(d.inspection_types or []),
        "issue": d.issue, "resolution": d.resolution,
        "confirmer": d.confirmer, "notice_no": d.notice_no,
    } for d in data._seed_deficiencies()])

    seed_table("notices", [{
        "notice_no": n.notice_no,
        "inspection_date": n.inspection_date.isoformat(),
        "floor": n.floor, "zone": n.zone,
        "inspection_type": n.inspection_type, "issue": n.issue,
        "photo_path": n.photo_path, "submitter": n.submitter,
        "confirmer": n.confirmer, "action_done": n.action_done,
        "action_at": n.action_at.isoformat() if n.action_at else None,
        "action_note": n.action_note, "action_photo_path": None,
    } for n in data._seed_notices()])

    seed_table("malfunctions", [{
        "malfunction_id": m.malfunction_id, "category": m.category,
        "occurred_on": m.occurred_on.isoformat(), "detail": m.detail,
        "action": m.action, "confirmer": m.confirmer,
    } for m in data._seed_malfunctions()])

    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

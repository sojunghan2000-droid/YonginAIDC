# PRD — "최근 점검" KPI 카드 (시설 관리)

| 항목 | 내용 |
|---|---|
| 대상 | 시설 관리 페이지 KPI 2번째 카드 "최근 점검" |
| 관련 코드 | `lib/data.py` `equipment_kpis()` · `pages_app/equipment_inventory.py` · `lib/ui.py` `kpi_card()` |
| 작성일 | 2026-06-12 |
| 상위 문서 | [PRD.md](PRD.md) §10 R3·R4 (데모 보정값 · TODAY 고정) |

---

## 1. 카드의 목적

시설 관리 화면에서 **"점검 활동이 살아있는가"** 를 보여주는 카드.
관리자가 페이지에 들어왔을 때 최근 48시간 동안 현장에서 점검이 실제로
돌고 있는지를 숫자 하나로 확인하는 것이 목적이다.

## 2. 현재 구현 (As-Is)

### 표시 구조

```
┌──────────────────┐
│ 최근 점검          │  ← .kpi-label  (data: 카드 튜플 1번째)
│ 430              │  ← .kpi-value  (equipment_kpis()['recently_inspected'])
│ 지난 48시간        │  ← .kpi-hint   (카드 튜플 3번째, 고정 문구)
└──────────────────┘     variant="default" (흰 배경)
```

- UI 조립: `lib/ui.py` `kpi_card(label, value, hint, variant)` → HTML 문자열
- 페이지 전달: `equipment_inventory.py` `render_kpi_row([...])` 2번째 튜플

### 값 계산식 (`lib/data.py`)

```python
recent_threshold = TODAY - timedelta(hours=48)   # ← 선언만 되고 미사용 (dead code)
...
"recently_inspected":
    sum(1 for e in eq if e.last_inspection and e.last_inspection >= TODAY - timedelta(days=2))
    + 430                                        # ← 데모 보정값 (하드코딩)
```

### 문제점

| # | 문제 | 상세 |
|---|---|---|
| P1 | **표시값이 사실상 전부 가짜** | 시드 12대의 최근 점검일이 모두 48시간 밖 → 실제 카운트 0건. 화면의 "430"은 하드코딩 `+430`이 전부 |
| P2 | **기준 시점 고정** | `TODAY = date(2026, 5, 27)` 고정 → "지난 48시간"이 흐르지 않음 |
| P3 | **단위 불일치** | `last_inspection`은 `date`(일 단위)인데 힌트는 "48시간". 시간 단위 판정이 불가능한 데이터로 시간 문구를 표시 |
| P4 | 죽은 코드 | `recent_threshold` 변수 미사용 — 계산식과 분리되어 혼동 유발 |

## 3. 목표 (To-Be)

> **카드 숫자는 실제 점검 기록만으로 계산하고, 데이터가 영구 저장소로
> 전환되면 코드 수정 없이 그대로 실값이 나오게 한다.**

### 요구사항

| ID | 요구사항 | 우선순위 |
|---|---|---|
| R1 | 표시값 = 기준 시점에서 48시간(2일) 이내 `last_inspection`을 가진 장비 수. **보정값(+430) 제거** | P0 |
| R2 | 기준 시점은 단일 소스(`TODAY` 또는 `date.today()`)에서 가져오되, 운영 전환 시 `date.today()`로 일괄 교체 가능해야 함 | P0 |
| R3 | 힌트 문구와 계산 단위 일치 — `date` 단위 데이터를 유지한다면 힌트를 "최근 2일"로, 시간 단위가 필요하면 `last_inspection`을 datetime으로 승격 | P1 |
| R4 | 점검 입력(신규 점검 모달) 시 해당 장비의 `last_inspection`이 갱신되어 카드에 즉시 반영 | P1 |
| R5 | 0건일 때도 "0"을 정직하게 표시 (현장 점검이 없었음을 숨기지 않는 것이 카드의 존재 이유) | P0 |
| R6 | `recent_threshold` 죽은 코드 정리 — 계산식이 이 변수를 실제로 사용하도록 통합 | P2 |

### 비요구사항

- 시간대(타임존) 처리 — 단일 현장, 일 단위 데이터라 v1에서는 불필요
- 추세 표시(전주 대비 증감) — 별도 카드/차트 과제

## 4. 구현 계획

1. **`lib/data.py`** — `equipment_kpis()` 수정:
   ```python
   recent_threshold = TODAY - timedelta(days=2)
   "recently_inspected": sum(
       1 for e in eq
       if e.last_inspection and e.last_inspection >= recent_threshold
   ),
   ```
   (`+430` 제거, dead code였던 `recent_threshold`를 실제 사용)
2. **`pages_app/equipment_inventory.py`** — 힌트 문구 "지난 48시간" → "최근 2일" (R3)
3. **점검 입력 → `last_inspection` 갱신** (R4): `lib/inspection_dialog.py`의
   점검 저장 시 대상 장비의 `last_inspection = 점검일` 오버라이드를
   세션(`eq_types_edits`와 같은 패턴)에 기록하고 `load_equipment()`에서 병합
4. **검증**: 시드 기준 카드가 "0"으로 표시 → 신규 점검 1건 입력 → "1"로
   바뀌는지 미리보기에서 확인

## 5. 영향 범위

- 같은 함수의 다른 키(`pending_issues`도 `+14` 보정 있음)는 이 PRD 범위 밖
  — 단, 같은 원칙(보정값 제거)을 적용할 후속 과제로 [PRD.md](PRD.md) §11 v1.1에 이미 등재
- 대시보드는 `recently_inspected`를 사용하지 않으므로 영향 없음
- 데모 시연 관점: 보정값 제거 시 카드가 "0"으로 보이는 것이 어색하면,
  시드 장비 1~2대의 `last_inspection`을 `TODAY - 1일`로 조정하는 방식을 권장
  (가짜 합산이 아니라 가짜 *데이터*로 — 계산 로직은 정직하게 유지)

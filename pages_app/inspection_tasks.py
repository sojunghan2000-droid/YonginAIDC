"""Inspection Tasks 페이지."""
from __future__ import annotations

import streamlit as st

from lib import data
from lib.inspection_dialog import task_dialog
from lib.ui import TASK_STATUS_KO, badge, fmt_date, page_header, render_kpi_row


# 탭 라벨 ↔ data 모델의 영문 status 매핑
TAB_TO_STATUS = {
    "진행 중": "In Progress",
    "예정": "Scheduled",
    "지연": "Overdue",
}


def render() -> None:
    tasks = data.load_tasks()
    kpi = data.task_kpis()

    title_col, action_col = st.columns([2.5, 1.5])
    with title_col:
        page_header(
            "점검 일정",
            "시설 안전점검 일정을 등록하고 진행 상황을 관리합니다.",
        )
    new_task_clicked = False
    with action_col:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("신규 일정 등록", type="primary",
                         use_container_width=True, key="open_new_task"):
                new_task_clicked = True
        with b2:
            st.button("감사 로그 내보내기", use_container_width=True)

    submitted_ids = st.session_state.pop("just_submitted_tasks", None)
    if submitted_ids:
        if len(submitted_ids) == 1:
            st.success(f"점검 일정 1건 등록 완료 ({submitted_ids[0]}).")
        else:
            st.success(
                f"점검 일정 {len(submitted_ids)}건 등록 완료 "
                f"({submitted_ids[0]} ~ {submitted_ids[-1]})."
            )

    if new_task_clicked:
        task_dialog()

    render_kpi_row([
        ("전체 일정", f"{kpi['total']}", "이번 주 활성", "default"),
        ("지연", f"{kpi['overdue']}", "즉시 조치 필요", "alert"),
        ("진행 중", f"{kpi['in_progress']}", "현재 활성", "default"),
        ("완료", f"{kpi['completed']}", "최근 7일", "default"),
    ])

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    filter_col, _, tab_col = st.columns([2.5, 2, 3])
    with tab_col:
        view = st.radio(
            "tab",
            ["전체", "진행 중", "예정", "지연"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with filter_col:
        type_filter = st.selectbox(
            "점검 유형",
            ["전체 유형"] + sorted({t.task_type for t in tasks}),
            label_visibility="collapsed",
        )

    rows = tasks
    target_status = TAB_TO_STATUS.get(view)
    if target_status:
        rows = [t for t in rows if t.status == target_status]
    if type_filter != "전체 유형":
        rows = [t for t in rows if t.task_type == type_filter]

    header_html = (
        "<table style='width:100%; border-collapse:collapse;'>"
        "<thead><tr style='color:#64748B; font-size:0.78rem; text-align:left; "
        "border-bottom:1px solid #E2E8F0;'>"
        "<th style='padding:0.6rem 0.4rem;'>작업 ID</th>"
        "<th style='padding:0.6rem 0.4rem;'>장비 / 시설</th>"
        "<th style='padding:0.6rem 0.4rem;'>점검 유형</th>"
        "<th style='padding:0.6rem 0.4rem;'>담당자</th>"
        "<th style='padding:0.6rem 0.4rem;'>마감일</th>"
        "<th style='padding:0.6rem 0.4rem;'>상태</th>"
        "<th style='padding:0.6rem 0.4rem;'>작업</th>"
        "</tr></thead><tbody>"
    )
    body = []
    for t in rows:
        due_color = "#DC2626" if t.status == "Overdue" else "#334155"
        is_unassigned = t.assignee in ("Unassigned", "미지정")
        assignee_style = "color:#94A3B8; font-style:italic;" if is_unassigned else "color:#334155;"
        assignee_label = "미지정" if is_unassigned else t.assignee
        status_label = TASK_STATUS_KO.get(t.status, t.status)
        body.append(
            "<tr style='border-bottom:1px solid #F1F5F9;'>"
            f"<td style='padding:0.85rem 0.4rem; color:#334155;'>{t.task_id}</td>"
            f"<td style='padding:0.85rem 0.4rem; font-weight:600; color:#0F172A;'>{t.equipment_label}</td>"
            f"<td style='padding:0.85rem 0.4rem; color:#334155;'>{t.task_type}</td>"
            f"<td style='padding:0.85rem 0.4rem; {assignee_style}'>{assignee_label}</td>"
            f"<td style='padding:0.85rem 0.4rem; color:{due_color}; font-weight:600;'>{fmt_date(t.due_date)}</td>"
            f"<td style='padding:0.85rem 0.4rem;'>{badge(status_label)}</td>"
            "<td style='padding:0.85rem 0.4rem; color:#94A3B8;'>보기 · 편집</td>"
            "</tr>"
        )
    st.markdown(header_html + "".join(body) + "</tbody></table>", unsafe_allow_html=True)

    foot_l, _, foot_r = st.columns([3, 3, 2])
    with foot_l:
        st.markdown(
            f"<div style='color:#64748B; font-size:0.85rem; padding-top:0.6rem;'>"
            f"{kpi['total']}개 중 1–{len(rows)} 표시</div>",
            unsafe_allow_html=True,
        )
    with foot_r:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.button("‹", key="tsk_prev", use_container_width=True)
        c2.button("1", key="tsk_1", type="primary", use_container_width=True)
        c3.button("2", key="tsk_2", use_container_width=True)
        c4.button("3", key="tsk_3", use_container_width=True)
        c5.button("›", key="tsk_next", use_container_width=True)

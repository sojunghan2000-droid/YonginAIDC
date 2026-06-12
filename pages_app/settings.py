"""설정 페이지 — 개인정보 변경 + (관리자) 사용자 관리.

상단바 아바타 메뉴에서 진입한다. 사이드바 내비게이션에는 없음.
"""
from __future__ import annotations

import streamlit as st

from lib import auth
from lib.ui import page_header


def render() -> None:
    user = auth.current_user()
    if not user:
        st.error("로그인이 필요합니다.")
        return

    page_header("설정", "계정 정보를 변경하고 사용자 권한을 관리합니다.")

    sections = ["개인정보"]
    if auth.is_admin():
        sections.append("사용자 관리")

    default_idx = 0
    if st.session_state.pop("settings_tab", None) == "admin" and len(sections) > 1:
        default_idx = 1
    section = st.radio("섹션", sections, index=default_idx, horizontal=True,
                       label_visibility="collapsed", key="settings_section")

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    if section == "사용자 관리":
        _admin_section(user)
    else:
        _profile_section(user)


# ---------- 개인정보 ----------

def _profile_section(user: dict) -> None:
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("<b style='color:#0F172A;'>이름 변경</b>", unsafe_allow_html=True)
        with st.form("profile_name_form"):
            new_name = st.text_input("이름", value=user["name"])
            if st.form_submit_button("이름 저장", use_container_width=True):
                new_name = new_name.strip()
                if not new_name:
                    st.error("이름을 입력해 주세요.")
                else:
                    try:
                        auth.user_client().auth.update_user(
                            {"data": {"name": new_name}}
                        )
                        user["name"] = new_name
                        st.success("이름이 변경되었습니다.")
                    except Exception as e:
                        st.error(f"변경 실패: {e}")

    with col_r:
        st.markdown("<b style='color:#0F172A;'>비밀번호 변경</b>", unsafe_allow_html=True)
        with st.form("profile_pw_form"):
            current_pw = st.text_input("현재 비밀번호", type="password")
            new_pw = st.text_input("새 비밀번호", type="password", help="6자 이상")
            new_pw2 = st.text_input("새 비밀번호 확인", type="password")
            if st.form_submit_button("비밀번호 변경", type="primary",
                                     use_container_width=True):
                if not current_pw or not new_pw:
                    st.error("현재/새 비밀번호를 입력해 주세요.")
                elif new_pw != new_pw2:
                    st.error("새 비밀번호가 서로 일치하지 않습니다.")
                elif len(new_pw) < 6:
                    st.error("새 비밀번호는 6자 이상이어야 합니다.")
                else:
                    # 본인 확인: 현재 비밀번호로 재로그인 후 변경
                    ok, err = auth.sign_in(user["username"], current_pw)
                    if not ok:
                        st.error("현재 비밀번호가 올바르지 않습니다.")
                    else:
                        try:
                            auth.user_client().auth.update_user(
                                {"password": new_pw}
                            )
                            st.success("비밀번호가 변경되었습니다.")
                        except Exception as e:
                            st.error(f"변경 실패: {e}")


# ---------- 사용자 관리 (관리자) ----------

def _admin_section(me: dict) -> None:
    if not auth.is_admin():
        st.error("관리자만 접근할 수 있습니다.")
        return

    admin = auth.admin_client()
    try:
        users = admin.auth.admin.list_users()
    except Exception as e:
        st.error(f"사용자 목록 조회 실패: {e}")
        return

    admin_count = sum(
        1 for u in users if (u.app_metadata or {}).get("role") == "admin"
    )
    st.markdown(
        f"<div style='color:#64748B; font-size:0.88rem; margin-bottom:0.6rem;'>"
        f"전체 사용자 {len(users)}명 · 관리자 {admin_count}명</div>",
        unsafe_allow_html=True,
    )

    for u in users:
        meta = u.user_metadata or {}
        username = meta.get("username") or (u.email or "").split("@")[0]
        name = meta.get("name") or username
        role = (u.app_metadata or {}).get("role", "user")
        is_me = u.id == me["user_id"]
        role_label = "관리자" if role == "admin" else "일반"
        title = f"{name} ({username}) · {role_label}" + (" · 본인" if is_me else "")

        with st.expander(title):
            c1, c2, c3 = st.columns(3)

            # 권한 변경 (본인 제외, 마지막 관리자 강등 방지)
            with c1:
                st.markdown("<b style='font-size:0.88rem;'>권한 변경</b>",
                            unsafe_allow_html=True)
                if is_me:
                    st.caption("본인 권한은 변경할 수 없습니다.")
                else:
                    new_role = st.selectbox(
                        "역할", ["user", "admin"],
                        index=0 if role == "user" else 1,
                        format_func=lambda r: "일반" if r == "user" else "관리자",
                        key=f"role_{u.id}",
                    )
                    if st.button("권한 적용", key=f"role_btn_{u.id}",
                                 use_container_width=True):
                        if role == "admin" and new_role == "user" and admin_count <= 1:
                            st.error("마지막 관리자는 강등할 수 없습니다.")
                        else:
                            try:
                                admin.auth.admin.update_user_by_id(
                                    u.id, {"app_metadata": {"role": new_role}}
                                )
                                st.success("권한이 변경되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"실패: {e}")

            # 이름 수정
            with c2:
                st.markdown("<b style='font-size:0.88rem;'>이름 수정</b>",
                            unsafe_allow_html=True)
                edit_name = st.text_input("이름", value=name,
                                          key=f"name_{u.id}",
                                          label_visibility="collapsed")
                if st.button("이름 저장", key=f"name_btn_{u.id}",
                             use_container_width=True):
                    if not edit_name.strip():
                        st.error("이름을 입력해 주세요.")
                    else:
                        try:
                            admin.auth.admin.update_user_by_id(
                                u.id,
                                {"user_metadata": {**meta, "name": edit_name.strip()}},
                            )
                            st.success("이름이 변경되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"실패: {e}")

            # 비밀번호 초기화
            with c3:
                st.markdown("<b style='font-size:0.88rem;'>비밀번호 초기화</b>",
                            unsafe_allow_html=True)
                temp_pw = st.text_input("새 임시 비밀번호", type="password",
                                        key=f"pw_{u.id}",
                                        label_visibility="collapsed",
                                        placeholder="새 임시 비밀번호 (6자+)")
                if st.button("초기화 적용", key=f"pw_btn_{u.id}",
                             use_container_width=True):
                    if len(temp_pw) < 6:
                        st.error("6자 이상 입력해 주세요.")
                    else:
                        try:
                            admin.auth.admin.update_user_by_id(
                                u.id, {"password": temp_pw}
                            )
                            st.success("비밀번호가 초기화되었습니다. "
                                       "해당 사용자에게 전달 후 직접 변경하도록 안내하세요.")
                        except Exception as e:
                            st.error(f"실패: {e}")

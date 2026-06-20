"""설정 페이지 — 개인정보 변경.

상단바 아바타 메뉴에서 진입한다. 사이드바 내비게이션에는 없음.
사용자 관리는 v1.3부터 관리자 메뉴(admin_center) 로 이관됨.
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

    page_header("개인정보 변경", "이름과 비밀번호를 변경할 수 있습니다.")

    # 관리자에게는 사용자 관리로의 안내 (구 settings_tab='admin' 진입 호환)
    if st.session_state.pop("settings_tab", None) == "admin" and auth.is_admin():
        st.session_state["page"] = "admin"
        st.session_state["admin_tab"] = "사용자 관리"
        st.rerun()

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


# 사용자 관리는 v1.3부터 pages_app/admin_center.py 의 _user_admin_tab() 로 이관.

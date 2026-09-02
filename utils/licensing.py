# -*- coding: utf-8 -*-
"""
licensing.py
------------
Streamlit Secrets에 등록된 라이선스 키로 유료 접근을 게이트한다.
secrets.toml 예:

VALID_LICENSE_KEYS = ["MEDIEM-ORG-0001", "MEDIEM-ORG-0002"]
"""

from __future__ import annotations
import streamlit as st

SESSION_KEY = "license_verified"


def is_licensed() -> bool:
    return bool(st.session_state.get(SESSION_KEY, False))


def render_license_gate() -> bool:
    """라이선스 미인증 시 입력 폼을 그리고 False 반환. 인증 완료 시 True."""
    if is_licensed():
        return True

    st.title("🔒 라이선스 인증")
    st.write("이 프로그램은 주식회사 메디엄의 유료 컨설팅 도구입니다. 발급받은 라이선스 키를 입력해주세요.")

    valid_keys = set(st.secrets.get("VALID_LICENSE_KEYS", []))

    with st.form("license_form"):
        key_input = st.text_input("라이선스 키", type="password", placeholder="예: MEDIEM-ORG-0001")
        submitted = st.form_submit_button("인증", use_container_width=True)

    if submitted:
        if not valid_keys:
            st.error("서버에 등록된 라이선스 키가 없습니다. 관리자에게 문의하세요.")
        elif key_input.strip() in valid_keys:
            st.session_state[SESSION_KEY] = True
            st.success("인증되었습니다.")
            st.rerun()
        else:
            st.error("유효하지 않은 라이선스 키입니다.")

    st.caption("라이선스 관련 문의: 주식회사 메디엄")
    return False

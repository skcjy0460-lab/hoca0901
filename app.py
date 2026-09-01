# -*- coding: utf-8 -*-
"""
병원 조직도 설계 AI
====================
주식회사 메디엄 — 병원 개원·경영 컨설팅용 AI 조직도 자동 설계/진단 프로그램

실행: streamlit run app.py
"""

import streamlit as st
from utils.licensing import render_license_gate

st.set_page_config(
    page_title="병원 조직도 설계 AI | 메디엄",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 전역 세션 상태 초기화
DEFAULTS = {
    "hospital_info": {},
    "org_tree": {},
    "ai_diagnosis": None,
    "growth_stage_trees": {},
    "current_tree_source": None,  # "template" | "ai" | "manual"
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# 라이선스 게이트 (secrets에 VALID_LICENSE_KEYS 미설정 시 통과 — 로컬 개발용)
license_required = bool(st.secrets.get("VALID_LICENSE_KEYS"))
if license_required and not render_license_gate():
    st.stop()

pages = {
    "병원 조직도 설계 AI": [
        st.Page("views/1_병원정보입력.py", title="1. 병원 정보 입력", icon="🏥", default=True),
        st.Page("views/2_AI조직진단.py", title="2. AI 조직 진단", icon="🤖"),
        st.Page("views/3_조직도편집기.py", title="3. 조직도 편집기", icon="🌳"),
        st.Page("views/4_성장로드맵.py", title="4. 성장 단계 로드맵", icon="📈"),
        st.Page("views/5_내보내기.py", title="5. 내보내기", icon="📤"),
    ]
}

nav = st.navigation(pages)

with st.sidebar:
    st.markdown("### 🏥 병원 조직도 설계 AI")
    st.caption("주식회사 메디엄")
    st.divider()
    info = st.session_state.get("hospital_info") or {}
    if info:
        st.markdown(f"**{info.get('name', '(병원명 미입력)')}**")
        st.caption(f"{info.get('type','-')} · 병상 {info.get('beds','-')}개")
    else:
        st.caption("아직 병원 정보가 입력되지 않았습니다.")
    st.divider()
    st.caption("© " + "주식회사 메디엄")

nav.run()

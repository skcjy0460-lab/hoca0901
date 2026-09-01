# -*- coding: utf-8 -*-
import streamlit as st
from utils.org_data import HOSPITAL_TYPES, MEDICAL_DEPARTMENTS, GROWTH_STAGE_DEFS
from utils.org_chart_builder import build_tree_from_template

st.title("🏥 병원 정보 입력")
st.caption("조직도 설계의 기초가 되는 병원 기본 정보를 입력하세요. 이후 AI 진단 및 조직도 자동 생성에 사용됩니다.")

info = st.session_state.get("hospital_info", {}) or {}

with st.form("hospital_info_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("병원명", value=info.get("name", ""), placeholder="예: OO병원")
        hospital_type = st.selectbox(
            "병원 종별", list(HOSPITAL_TYPES.keys()),
            index=list(HOSPITAL_TYPES.keys()).index(info.get("type")) if info.get("type") in HOSPITAL_TYPES else 0,
        )
        st.caption(HOSPITAL_TYPES[hospital_type]["desc"])
    with col2:
        beds = st.number_input("병상 수", min_value=0, max_value=3000, value=int(info.get("beds", 0)), step=1)
        opening_stage = st.selectbox(
            "현재 개원 단계", list(GROWTH_STAGE_DEFS.keys()),
            index=list(GROWTH_STAGE_DEFS.keys()).index(info.get("opening_stage"))
            if info.get("opening_stage") in GROWTH_STAGE_DEFS else 0,
        )
        st.caption(GROWTH_STAGE_DEFS[opening_stage]["특징"])

    departments = st.multiselect(
        "운영(예정) 진료과목", MEDICAL_DEPARTMENTS,
        default=info.get("departments", []),
    )

    st.divider()
    st.markdown("##### 현재 인력 현황 (선택 입력 — AI 진단 정확도 향상)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        doctors = st.number_input("의사 수", min_value=0, value=int(info.get("staff", {}).get("doctors", 0)))
    with c2:
        nurses = st.number_input("간호사 수", min_value=0, value=int(info.get("staff", {}).get("nurses", 0)))
    with c3:
        admin_staff = st.number_input("행정/원무 인력", min_value=0, value=int(info.get("staff", {}).get("admin", 0)))
    with c4:
        other_staff = st.number_input("기타 인력(약제·영양·시설 등)", min_value=0,
                                       value=int(info.get("staff", {}).get("other", 0)))

    current_org_note = st.text_area(
        "현재 조직 운영상 애로사항 / 기존 조직도 설명 (선택)",
        value=info.get("current_org_note", ""),
        placeholder="예: 원장이 원무·인사·시설관리를 모두 직접 관리하고 있어 진료에 집중하기 어려움. "
                    "간호부장 공백으로 병동 파트장이 직접 원장에게 보고 중.",
        height=120,
    )

    submitted = st.form_submit_button("💾 정보 저장", use_container_width=True, type="primary")

if submitted:
    if not name.strip():
        st.error("병원명을 입력해주세요.")
    else:
        st.session_state["hospital_info"] = {
            "name": name.strip(),
            "type": hospital_type,
            "beds": int(beds),
            "opening_stage": opening_stage,
            "departments": departments,
            "staff": {
                "doctors": int(doctors), "nurses": int(nurses),
                "admin": int(admin_staff), "other": int(other_staff),
            },
            "current_org_note": current_org_note,
        }
        st.success("병원 정보가 저장되었습니다. 왼쪽 메뉴에서 'AI 조직 진단' 또는 '조직도 편집기'로 이동하세요.")

st.divider()

info = st.session_state.get("hospital_info", {}) or {}
if info.get("name"):
    st.markdown("### 🧩 빠른 시작: 기본 템플릿으로 조직도 생성")
    st.caption(
        f"{info['type']} · 병상 {info['beds']}개 기준의 일반적인 조직 구조 템플릿을 즉시 생성합니다. "
        "이후 'AI 조직 진단'에서 더 정교하게 다듬거나, '조직도 편집기'에서 직접 수정할 수 있습니다."
    )
    if st.button("⚡ 기본 조직도 템플릿 즉시 생성", use_container_width=True):
        st.session_state["org_tree"] = build_tree_from_template(info["type"], info["beds"])
        st.session_state["current_tree_source"] = "template"
        st.success("기본 템플릿 조직도가 생성되었습니다 → '조직도 편집기' 메뉴에서 확인하세요.")
else:
    st.info("먼저 병원명을 입력하고 저장하면 빠른 시작 옵션이 나타납니다.")

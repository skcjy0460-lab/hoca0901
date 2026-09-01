# -*- coding: utf-8 -*-
import datetime as dt
import streamlit as st

from utils.org_chart_builder import tree_to_dot, span_of_control_warnings, total_headcount
from utils.export_utils import build_excel_report, build_pptx_org_chart, build_html_report

st.title("📤 내보내기")
st.caption("완성된 조직도를 Excel 인원표, 편집 가능한 PowerPoint 슬라이드, HTML 진단 보고서로 내보냅니다.")

info = st.session_state.get("hospital_info") or {}
tree = st.session_state.get("org_tree") or {}
diagnosis = st.session_state.get("ai_diagnosis")

if not tree:
    st.warning("먼저 '조직도 편집기'에서 조직도를 완성해주세요.")
    st.stop()

if not info.get("name"):
    st.warning("먼저 '1. 병원 정보 입력'에서 병원 정보를 저장해주세요.")
    st.stop()

st.markdown(f"#### {info['name']} · {info['type']} · 병상 {info['beds']}개 · 총 편성 인원 {total_headcount(tree)}명")

today_str = dt.date.today().strftime("%Y%m%d")
safe_name = "".join(c for c in info["name"] if c.isalnum()) or "hospital"

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("##### 📊 Excel 인원표")
    st.caption("조직 인원표, 병원 개요, 진단 체크리스트, AI 진단 결과를 포함한 워크북")
    if st.button("Excel 생성", use_container_width=True, key="gen_excel"):
        data = build_excel_report(tree, info, diagnosis)
        st.session_state["_export_excel"] = data
    if st.session_state.get("_export_excel"):
        st.download_button(
            "⬇️ Excel 다운로드", data=st.session_state["_export_excel"],
            file_name=f"{safe_name}_조직인원표_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

with col2:
    st.markdown("##### 🖼️ PowerPoint 조직도")
    st.caption("컨설팅 보고용으로 바로 편집 가능한 조직도 슬라이드 (도형/텍스트 개별 수정 가능)")
    if st.button("PPTX 생성", use_container_width=True, key="gen_pptx"):
        with st.spinner("슬라이드를 생성하는 중..."):
            data = build_pptx_org_chart(tree, info)
        st.session_state["_export_pptx"] = data
    if st.session_state.get("_export_pptx"):
        st.download_button(
            "⬇️ PPTX 다운로드", data=st.session_state["_export_pptx"],
            file_name=f"{safe_name}_조직도_{today_str}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )

with col3:
    st.markdown("##### 📄 HTML 진단 보고서")
    st.caption("조직도 이미지, AI 진단 결과, 통제범위 경고, 인원표를 포함한 브랜디드 보고서")
    if st.button("HTML 생성", use_container_width=True, key="gen_html"):
        warnings = span_of_control_warnings(tree)
        dot_str = tree_to_dot(tree, title=info.get("name", ""))
        html = build_html_report(tree, info, diagnosis, warnings, dot_str)
        st.session_state["_export_html"] = html
    if st.session_state.get("_export_html"):
        st.download_button(
            "⬇️ HTML 다운로드", data=st.session_state["_export_html"],
            file_name=f"{safe_name}_조직도진단보고서_{today_str}.html",
            mime="text/html",
            use_container_width=True,
        )

st.divider()
if st.session_state.get("_export_html"):
    st.markdown("#### 👁️ HTML 보고서 미리보기")
    st.components.v1.html(st.session_state["_export_html"], height=900, scrolling=True)

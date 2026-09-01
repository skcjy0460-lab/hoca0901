# -*- coding: utf-8 -*-
import json
import streamlit as st

from utils.ai_client import call_gemini_json, is_ai_configured
from utils.org_data import DEPT_TYPE_LIST, SPAN_OF_CONTROL
from utils.org_chart_builder import new_node_id, NODE_KINDS

st.title("🤖 AI 조직 진단 & 구조 추천")
st.caption("입력된 병원 정보를 바탕으로 AI가 조직 구조 초안과 진단 코멘트를 생성합니다. "
           "생성된 결과는 참고안이며, '조직도 편집기'에서 자유롭게 수정할 수 있습니다.")

info = st.session_state.get("hospital_info") or {}

if not info.get("name"):
    st.warning("먼저 '1. 병원 정보 입력' 화면에서 병원 정보를 저장해주세요.")
    st.stop()

if not is_ai_configured():
    st.error(
        "AI 기능이 설정되어 있지 않습니다. Streamlit Secrets에 `GEMINI_API_KEY`를 등록해주세요. "
        "(AI 없이도 '조직도 편집기'에서 수동으로 조직도를 만들 수 있습니다.)"
    )

with st.expander("📥 현재 입력된 병원 정보", expanded=False):
    st.json(info)

SYSTEM_INSTRUCTION = f"""당신은 한국 병원 개원 및 경영 컨설팅 전문가입니다.
입력된 병원 정보를 바탕으로 실무에서 바로 활용 가능한 조직 구조안과 진단 코멘트를
'오직 JSON'으로만 출력합니다. 설명 문장, 마크다운 코드펜스, 그 외 텍스트는 절대 포함하지 마세요.

[설계 원칙]
- 통제범위(관리자 1인당 직속 부하 수)는 {SPAN_OF_CONTROL['권장_최소']}~{SPAN_OF_CONTROL['권장_최대']}명 범위를 권장 기준으로 삼되, 병원 규모에 맞게 유연하게 판단하세요.
- 부서유형(dept_type)은 반드시 다음 목록 중 하나여야 합니다: {DEPT_TYPE_LIST}
- kind는 반드시 다음 중 하나여야 합니다: {NODE_KINDS}
  - "직급": 원장/부원장/부장/팀장 등 '책임자 1인' 자리. 조직도에는 이름을 적는 빈 줄이 표시됩니다.
  - "부서": 실무 인력 여러 명이 소속되는 팀/과. 조직도에는 명단을 손으로 적는 빈 칸 그리드가 표시됩니다.
  - 예: "간호부장"은 직급, 그 밑의 "외래간호팀"·"병동간호팀"·"수술실간호팀"은 부서.
- 병상 규모가 작은 의원급은 과도하게 세분화하지 말고 실용적으로 설계하세요.
- 병상 규모가 있는 병원급 이상은 아래와 같은 실무 관행을 최대한 반영해 세분화하세요 (병원 상황에 맞게 이름·구성은 조정 가능):
  - 간호부장(직급) 아래에 외래간호팀 / 병동간호팀 / 수술실간호팀 등(부서)으로 세분화
  - 진료지원 기능은 방사선과 / 임상병리과 등(부서)으로 세분화
  - 원무 기능은 접수/수납/보험청구·심사를 포괄하는 "원무&심사팀"(부서)으로 구성하거나 필요시 분리
  - 총무(인사/노무/구매 등)는 시설관리와 분리된 별도 "총무팀"(부서)으로 구성
- 청구심사(보험심사) 기능은 가능하면 원무 기능과 분리하거나 명확한 담당을 지정하세요.
- 법정 필수 인력 기준(정확한 숫자)은 병원 종별/연도별로 달라지므로 단정적인 법조문 숫자를 임의로 만들어내지 말고,
  "최신 의료법 시행규칙 확인 필요"와 같이 일반적 수준에서만 언급하세요.
- current_org_note(현재 애로사항)가 있다면 반드시 issues에 관련 진단을 반영하세요.

[출력 JSON 스키마]
{{
  "summary": "전체 진단 및 설계 방향 요약 (3~5문장)",
  "issues": ["현재 조직 운영상 문제점 또는 리스크 (문장형, 3~6개)"],
  "recommendations": ["구체적 개선 권장 조치 (문장형, 3~6개)"],
  "org_structure": [
    {{
      "title": "직책/부서명 (예: 원장, 간호부장, 외래간호팀)",
      "dept_type": "위 dept_type 목록 중 하나",
      "kind": "직급 또는 부서",
      "parent_title": "상위 직책/부서명 (최상위는 null)",
      "headcount": 숫자(정수),
      "note": "간단한 역할 설명"
    }}
  ]
}}
"""

user_prompt = f"""
[병원 정보]
- 병원명: {info.get('name')}
- 병원 종별: {info.get('type')}
- 병상 수: {info.get('beds')}
- 운영 진료과목: {', '.join(info.get('departments', [])) or '(미입력)'}
- 개원 단계: {info.get('opening_stage')}
- 현재 인력: 의사 {info.get('staff', {}).get('doctors', 0)}명, 간호사 {info.get('staff', {}).get('nurses', 0)}명, \
행정/원무 {info.get('staff', {}).get('admin', 0)}명, 기타 {info.get('staff', {}).get('other', 0)}명
- 현재 애로사항/기존 조직 설명: {info.get('current_org_note') or '(미입력)'}

위 정보를 바탕으로 이 병원에 맞는 조직 구조안과 진단 결과를 스키마에 맞춰 JSON으로만 출력하세요.
org_structure는 최상위 노드(parent_title=null)를 반드시 1개 포함해야 하며, 트리 구조가 논리적으로 연결되어야 합니다.
"""

col_a, col_b = st.columns([1, 1])
with col_a:
    run_clicked = st.button("🚀 AI 조직 진단 실행", type="primary", use_container_width=True,
                             disabled=not is_ai_configured())
with col_b:
    clear_clicked = st.button("🗑️ 진단 결과 초기화", use_container_width=True)

if clear_clicked:
    st.session_state["ai_diagnosis"] = None
    st.rerun()

if run_clicked:
    with st.spinner("AI가 조직 구조를 분석하고 있습니다... (모델 폴백 체인 시도 중)"):
        try:
            result = call_gemini_json(user_prompt, system_instruction=SYSTEM_INSTRUCTION)
            st.session_state["ai_diagnosis"] = result
            st.success("AI 진단이 완료되었습니다.")
        except Exception as e:  # noqa: BLE001
            st.error(f"AI 호출 중 오류가 발생했습니다: {e}")

diagnosis = st.session_state.get("ai_diagnosis")

if diagnosis:
    st.divider()
    st.markdown("### 📋 진단 요약")
    st.info(diagnosis.get("summary", ""))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ⚠️ 진단된 문제점")
        for item in diagnosis.get("issues", []):
            st.markdown(f"- {item}")
    with col2:
        st.markdown("#### ✅ 권장 조치")
        for item in diagnosis.get("recommendations", []):
            st.markdown(f"- {item}")

    st.divider()
    st.markdown("### 🌳 AI 추천 조직 구조 (미리보기)")
    structure = diagnosis.get("org_structure", [])
    if structure:
        st.dataframe(
            [{"직책/부서명": s.get("title"), "구분": s.get("kind", "부서"), "부서유형": s.get("dept_type"),
              "상위조직": s.get("parent_title") or "(최상위)", "인원": s.get("headcount"),
              "비고": s.get("note", "")} for s in structure],
            use_container_width=True, hide_index=True,
        )

        if st.button("📌 이 구조를 조직도 편집기에 적용", type="primary", use_container_width=True):
            # title -> node_id 매핑 후 tree 구성
            title_to_id = {}
            tree = {}
            for item in structure:
                node_id = new_node_id()
                title_to_id[item.get("title")] = node_id
                tree[node_id] = {
                    "id": node_id,
                    "title": item.get("title", "(제목없음)"),
                    "dept_type": item.get("dept_type") if item.get("dept_type") in DEPT_TYPE_LIST else "경영/관리",
                    "kind": item.get("kind") if item.get("kind") in NODE_KINDS else "부서",
                    "parent_id": None,
                    "headcount": int(item.get("headcount") or 0),
                    "note": item.get("note", ""),
                }
            for item in structure:
                parent_title = item.get("parent_title")
                node_id = title_to_id.get(item.get("title"))
                if node_id and parent_title and parent_title in title_to_id:
                    tree[node_id]["parent_id"] = title_to_id[parent_title]

            st.session_state["org_tree"] = tree
            st.session_state["current_tree_source"] = "ai"
            st.success("AI 추천 구조가 조직도에 적용되었습니다 → '조직도 편집기'로 이동해 확인·수정하세요.")
    else:
        st.warning("AI가 조직 구조를 생성하지 못했습니다. 다시 시도해주세요.")

    with st.expander("🔎 원본 JSON 보기"):
        st.code(json.dumps(diagnosis, ensure_ascii=False, indent=2), language="json")

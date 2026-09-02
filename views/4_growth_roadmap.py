# -*- coding: utf-8 -*-
import copy
import streamlit as st
import plotly.express as px

from utils.org_data import GROWTH_STAGE_DEFS
from utils.org_chart_builder import tree_to_dot, total_headcount

st.title("📈 개원 단계별 성장 로드맵")
st.caption(
    "동일한 조직 골격을 유지하면서, 개원 단계에 따라 인원 배치가 어떻게 확장되는지 미리 시뮬레이션합니다. "
    "구조(부서 구성)는 그대로 두고 인원 수만 단계별로 조정하는 방식입니다."
)

tree = st.session_state.get("org_tree") or {}
info = st.session_state.get("hospital_info") or {}

if not tree:
    st.warning("먼저 '조직도 편집기'에서 기준이 되는 조직도를 만들어주세요.")
    st.stop()


def scale_tree(base_tree: dict, multiplier: float) -> dict:
    scaled = copy.deepcopy(base_tree)
    for node in scaled.values():
        if node.get("headcount", 0) > 0:
            node["headcount"] = max(1, round(node["headcount"] * multiplier))
    return scaled


if st.button("🔄 현재 조직도 기준으로 3단계 로드맵 생성/갱신", type="primary", use_container_width=True):
    stage_trees = {}
    for stage_name, stage_def in GROWTH_STAGE_DEFS.items():
        stage_trees[stage_name] = scale_tree(tree, stage_def["headcount_multiplier"])
    st.session_state["growth_stage_trees"] = stage_trees
    st.success("단계별 로드맵이 생성되었습니다.")

stage_trees = st.session_state.get("growth_stage_trees") or {}

if not stage_trees:
    st.info("위 버튼을 눌러 현재 조직도를 기준으로 단계별 로드맵을 생성해주세요.")
    st.stop()

# 총 인원 비교 차트
summary_rows = [
    {"단계": stage, "총 인원": total_headcount(t), "기간 가이드": GROWTH_STAGE_DEFS[stage]["기간_가이드"]}
    for stage, t in stage_trees.items()
]
fig = px.bar(
    summary_rows, x="단계", y="총 인원", text="총 인원",
    title="단계별 총 편성 인원 비교", color="단계",
    color_discrete_sequence=["#64748B", "#2563EB", "#0E8A6D"],
)
fig.update_traces(textposition="outside")
fig.update_layout(showlegend=False, height=380)
st.plotly_chart(fig, use_container_width=True)

st.divider()

tabs = st.tabs(list(stage_trees.keys()))
for tab, (stage_name, stage_tree) in zip(tabs, stage_trees.items()):
    with tab:
        stage_def = GROWTH_STAGE_DEFS[stage_name]
        st.markdown(f"**기간 가이드:** {stage_def['기간_가이드']}")
        st.markdown(f"**단계 특징:** {stage_def['특징']}")
        st.markdown(f"**총 편성 인원:** {total_headcount(stage_tree)}명")
        dot_str = tree_to_dot(stage_tree, title=f"{info.get('name','')} - {stage_name}")
        try:
            st.graphviz_chart(dot_str, use_container_width=True)
        except Exception:
            st.code(dot_str, language="dot")

st.divider()
st.caption(
    "※ 단계별 인원 배수는 일반적인 성장 시나리오를 가정한 참고 수치입니다. "
    "실제 채용 계획은 진료 실적, 병상 가동률, 지역 노동시장 상황 등을 종합적으로 고려해 조정해야 합니다."
)

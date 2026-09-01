# -*- coding: utf-8 -*-
import streamlit as st

from utils.org_data import DEPT_TYPE_LIST
from utils.org_chart_builder import (
    add_node, remove_node, get_descendants, tree_to_dot, tree_to_dataframe,
    total_headcount, span_of_control_warnings, detect_cycles, orphan_department_warnings,
)

st.title("🌳 조직도 편집기")
st.caption("노드를 추가·수정·삭제하여 조직도를 자유롭게 편집하세요. 변경 사항은 즉시 아래 조직도에 반영됩니다.")

info = st.session_state.get("hospital_info") or {}
tree = st.session_state.get("org_tree") or {}

if not tree:
    st.warning(
        "아직 생성된 조직도가 없습니다. '1. 병원 정보 입력'에서 빠른 템플릿을 생성하거나, "
        "'2. AI 조직 진단'에서 AI 추천 구조를 적용하거나, 아래에서 직접 노드를 추가해 시작할 수 있습니다."
    )

# ---------------------------------------------------------------------------
# 검증 경고
# ---------------------------------------------------------------------------
warnings = span_of_control_warnings(tree) if tree else []
cycles = detect_cycles(tree) if tree else []
orphan_msgs = orphan_department_warnings(tree) if tree else []

if cycles:
    st.error(f"⚠️ 순환 참조가 감지된 노드가 있습니다: {cycles}. 상위 조직 설정을 다시 확인해주세요.")
if warnings:
    with st.expander(f"⚠️ 통제범위 경고 {len(warnings)}건", expanded=True):
        for w in warnings:
            st.markdown(f"- {w['메시지']}")
if orphan_msgs:
    with st.expander(f"ℹ️ 데이터 점검 필요 {len(orphan_msgs)}건"):
        for m in orphan_msgs:
            st.markdown(f"- {m}")

# ---------------------------------------------------------------------------
# 시각화
# ---------------------------------------------------------------------------
st.markdown(f"#### 📊 조직도 미리보기 · 총 편성 인원 {total_headcount(tree)}명 · 노드 {len(tree)}개")
if tree:
    dot_str = tree_to_dot(tree, title=info.get("name", ""))
    try:
        st.graphviz_chart(dot_str, use_container_width=True)
    except Exception:
        st.warning("Graphviz 렌더링에 실패했습니다. `packages.txt`에 graphviz가 포함되어 배포되었는지 확인해주세요.")
        st.code(dot_str, language="dot")
else:
    st.info("조직도가 비어 있습니다. 아래에서 첫 노드(원장 등 최상위 직책)를 추가해주세요.")

st.divider()

# ---------------------------------------------------------------------------
# 노드 추가
# ---------------------------------------------------------------------------
st.markdown("### ➕ 새 직책/부서 추가")
title_options = {"(최상위 — 상위 조직 없음)": None}
title_options.update({f"{n['title']}": n["id"] for n in tree.values()})

with st.form("add_node_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        new_title = st.text_input("직책/부서명", placeholder="예: 간호부장, 원무행정팀")
        new_dept_type = st.selectbox("부서유형", DEPT_TYPE_LIST)
    with c2:
        new_parent_label = st.selectbox("상위 조직", list(title_options.keys()))
        new_headcount = st.number_input("배치 인원", min_value=0, value=1)
    new_note = st.text_input("비고 (선택)", placeholder="역할, 담당 범위 등")

    add_submitted = st.form_submit_button("추가", type="primary", use_container_width=True)

if add_submitted:
    if not new_title.strip():
        st.error("직책/부서명을 입력해주세요.")
    else:
        add_node(
            tree, new_title.strip(), new_dept_type,
            title_options[new_parent_label], int(new_headcount), new_note.strip(),
        )
        st.session_state["org_tree"] = tree
        st.session_state["current_tree_source"] = "manual"
        st.success(f"'{new_title}'가 추가되었습니다.")
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# 노드 수정 / 삭제
# ---------------------------------------------------------------------------
st.markdown("### ✏️ 기존 직책/부서 수정 · 삭제")

if not tree:
    st.caption("수정할 노드가 없습니다.")
else:
    sorted_nodes = sorted(tree.values(), key=lambda n: n["title"])
    for node in sorted_nodes:
        node_id = node["id"]
        with st.expander(f"{node['title']} ({node['dept_type']}, {node['headcount']}명)"):
            forbidden_parents = set(get_descendants(tree, node_id)) | {node_id}
            parent_choices = {"(최상위 — 상위 조직 없음)": None}
            parent_choices.update({
                n["title"]: n["id"] for n in tree.values() if n["id"] not in forbidden_parents
            })
            current_parent_label = "(최상위 — 상위 조직 없음)"
            for label, pid in parent_choices.items():
                if pid == node["parent_id"]:
                    current_parent_label = label
                    break

            with st.form(f"edit_form_{node_id}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    edit_title = st.text_input("직책/부서명", value=node["title"], key=f"title_{node_id}")
                    edit_dept_type = st.selectbox(
                        "부서유형", DEPT_TYPE_LIST,
                        index=DEPT_TYPE_LIST.index(node["dept_type"]) if node["dept_type"] in DEPT_TYPE_LIST else 0,
                        key=f"dept_{node_id}",
                    )
                with ec2:
                    parent_labels = list(parent_choices.keys())
                    edit_parent_label = st.selectbox(
                        "상위 조직", parent_labels,
                        index=parent_labels.index(current_parent_label),
                        key=f"parent_{node_id}",
                    )
                    edit_headcount = st.number_input(
                        "배치 인원", min_value=0, value=int(node["headcount"]), key=f"hc_{node_id}"
                    )
                edit_note = st.text_input("비고", value=node.get("note", ""), key=f"note_{node_id}")

                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    save_clicked = st.form_submit_button("💾 저장", use_container_width=True)
                with bcol2:
                    delete_clicked = st.form_submit_button("🗑️ 삭제", use_container_width=True)

            if save_clicked:
                node["title"] = edit_title.strip() or node["title"]
                node["dept_type"] = edit_dept_type
                node["parent_id"] = parent_choices[edit_parent_label]
                node["headcount"] = int(edit_headcount)
                node["note"] = edit_note.strip()
                st.session_state["org_tree"] = tree
                st.success("저장되었습니다.")
                st.rerun()

            if delete_clicked:
                remove_node(tree, node_id)
                st.session_state["org_tree"] = tree
                st.success(f"'{node['title']}'가 삭제되었습니다. (하위 조직이 있었다면 상위 조직으로 재연결됨)")
                st.rerun()

st.divider()
st.markdown("### 📋 조직 인원표")
if tree:
    st.dataframe(tree_to_dataframe(tree), use_container_width=True, hide_index=True)

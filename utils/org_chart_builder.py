# -*- coding: utf-8 -*-
"""
org_chart_builder.py
---------------------
조직도를 '트리(dict of node_id -> node)' 구조로 관리하고,
Graphviz DOT 렌더링 / 검증 / 표 변환 기능을 제공한다.

Node 스키마:
{
    "id": str,              # 고유 키
    "title": str,           # 직책/부서명 (예: "간호부장", "원무행정부")
    "dept_type": str,       # DEPT_TYPE_LIST 중 하나
    "parent_id": str|None,  # 상위 노드 id (None = 최상위)
    "headcount": int,       # 배치 인원 수
    "note": str,            # 비고
}
"""

from __future__ import annotations
import uuid
import pandas as pd

from utils.org_data import DEPT_TYPE_COLOR, SPAN_OF_CONTROL, base_template


# ---------------------------------------------------------------------------
# 트리 생성 / 조작
# ---------------------------------------------------------------------------

def new_node_id() -> str:
    return uuid.uuid4().hex[:8]


def build_tree_from_template(hospital_type: str, beds: int) -> dict:
    """org_data.base_template 시드로부터 초기 트리를 생성."""
    seeds = base_template(hospital_type, beds)
    key_to_id = {}
    tree = {}
    for seed in seeds:
        node_id = new_node_id()
        key_to_id[seed.key] = node_id
        tree[node_id] = {
            "id": node_id,
            "title": seed.title,
            "dept_type": seed.dept_type,
            "parent_id": None,  # 아래에서 매핑
            "headcount": seed.headcount_hint,
            "note": seed.note,
        }
    for seed in seeds:
        if seed.parent_key is not None:
            tree[key_to_id[seed.key]]["parent_id"] = key_to_id[seed.parent_key]
    return tree


def add_node(tree: dict, title: str, dept_type: str, parent_id: str | None,
             headcount: int = 1, note: str = "") -> str:
    node_id = new_node_id()
    tree[node_id] = {
        "id": node_id,
        "title": title,
        "dept_type": dept_type,
        "parent_id": parent_id,
        "headcount": headcount,
        "note": note,
    }
    return node_id


def remove_node(tree: dict, node_id: str, reparent_children_to_root: bool = True) -> None:
    """노드 삭제. 자식이 있으면 조부모(또는 최상위)로 재연결하여 트리 무결성 유지."""
    if node_id not in tree:
        return
    parent_id = tree[node_id]["parent_id"]
    for n in tree.values():
        if n["parent_id"] == node_id:
            n["parent_id"] = parent_id if not reparent_children_to_root else parent_id
    del tree[node_id]


def get_children(tree: dict, node_id: str | None) -> list[dict]:
    return [n for n in tree.values() if n["parent_id"] == node_id]


def get_root_nodes(tree: dict) -> list[dict]:
    return get_children(tree, None)


def get_descendants(tree: dict, node_id: str) -> list[str]:
    """node_id의 모든 하위(자손) 노드 id 목록 (순환 참조 방지용)."""
    result = []
    stack = [c["id"] for c in get_children(tree, node_id)]
    while stack:
        current = stack.pop()
        result.append(current)
        stack.extend(c["id"] for c in get_children(tree, current))
    return result


def get_ancestors(tree: dict, node_id: str) -> list[str]:
    chain = []
    current = tree.get(node_id, {}).get("parent_id")
    while current is not None and current in tree:
        chain.append(current)
        current = tree[current]["parent_id"]
    return chain


# ---------------------------------------------------------------------------
# 검증 (순환 참조, 통제범위 등)
# ---------------------------------------------------------------------------

def detect_cycles(tree: dict) -> list[str]:
    """순환 참조가 발생하는 노드 id 목록 반환."""
    problematic = []
    for node_id in tree:
        seen = set()
        current = node_id
        while current is not None:
            if current in seen:
                problematic.append(node_id)
                break
            seen.add(current)
            current = tree.get(current, {}).get("parent_id")
    return problematic


def span_of_control_warnings(tree: dict) -> list[dict]:
    """통제범위(직속 부하 수) 권장 상한 초과 노드 경고."""
    warnings = []
    max_span = SPAN_OF_CONTROL["권장_최대"]
    for node in tree.values():
        children = get_children(tree, node["id"])
        if len(children) > max_span:
            warnings.append({
                "node": node["title"],
                "직속_하위_수": len(children),
                "권장_상한": max_span,
                "메시지": f"'{node['title']}'의 직속 보고 라인이 {len(children)}개로 "
                          f"권장 상한({max_span}개)을 초과합니다. 중간 관리 계층 추가를 검토하세요.",
            })
    return warnings


def orphan_department_warnings(tree: dict) -> list[str]:
    """제목이 비어 있거나 부서유형 미지정 등 데이터 결측 경고."""
    msgs = []
    for node in tree.values():
        if not node.get("title", "").strip():
            msgs.append(f"직책명이 비어 있는 노드가 있습니다 (id={node['id']}).")
        if node.get("headcount", 0) < 0:
            msgs.append(f"'{node.get('title')}'의 인원 수가 음수입니다.")
    return msgs


# ---------------------------------------------------------------------------
# 표 변환
# ---------------------------------------------------------------------------

def tree_to_dataframe(tree: dict) -> pd.DataFrame:
    rows = []
    for node in tree.values():
        parent_title = tree.get(node["parent_id"], {}).get("title", "") if node["parent_id"] else "(최상위)"
        depth = len(get_ancestors(tree, node["id"]))
        rows.append({
            "직책/부서명": node["title"],
            "부서유형": node["dept_type"],
            "상위조직": parent_title,
            "조직단계": depth + 1,
            "배치인원": node["headcount"],
            "비고": node.get("note", ""),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["조직단계", "상위조직", "직책/부서명"]).reset_index(drop=True)
    return df


def total_headcount(tree: dict) -> int:
    return sum(n.get("headcount", 0) for n in tree.values())


# ---------------------------------------------------------------------------
# Graphviz 렌더링
# ---------------------------------------------------------------------------

def tree_to_dot(tree: dict, title: str = "") -> str:
    """Graphviz DOT 언어 문자열 생성 (st.graphviz_chart에 바로 전달 가능)."""
    lines = [
        "digraph OrgChart {",
        '  rankdir="TB";',
        '  bgcolor="transparent";',
        '  node [shape=box, style="rounded,filled", fontname="NanumGothic", '
        'fontsize=12, fontcolor="white", margin="0.18,0.12"];',
        '  edge [color="#94A3B8", arrowsize=0.7];',
    ]
    if title:
        lines.append(f'  labelloc="t"; label="{_esc(title)}"; fontsize=16; fontname="NanumGothic";')

    for node in tree.values():
        color = DEPT_TYPE_COLOR.get(node["dept_type"], "#334155")
        label = _esc(node["title"])
        if node.get("headcount"):
            label += f"\\n({node['headcount']}명)"
        lines.append(f'  "{node["id"]}" [label="{label}", fillcolor="{color}"];')

    for node in tree.values():
        if node["parent_id"] and node["parent_id"] in tree:
            lines.append(f'  "{node["parent_id"]}" -> "{node["id"]}";')

    lines.append("}")
    return "\n".join(lines)


def _esc(text: str) -> str:
    return str(text).replace('"', '\\"')

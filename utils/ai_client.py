# -*- coding: utf-8 -*-
"""
ai_client.py
------------
Gemini API 호출 래퍼. 여러 모델을 순차 폴백하며, 구조화된 JSON 응답을 강제한다.
"""

from __future__ import annotations
import json
import re
import streamlit as st

try:
    import google.generativeai as genai
except ImportError:  # requirements.txt 미설치 환경 대비
    genai = None

# 모델 폴백 순서 (최신 → 구형). Secrets에서 override 가능.
DEFAULT_MODEL_CHAIN = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def _get_model_chain() -> list[str]:
    chain = st.secrets.get("GEMINI_MODEL_CHAIN")
    if chain:
        if isinstance(chain, str):
            return [m.strip() for m in chain.split(",") if m.strip()]
        return list(chain)
    return DEFAULT_MODEL_CHAIN


@st.cache_resource(show_spinner=False)
def _build_client(api_key: str):
    """API 키별로 클라이언트 빌더를 분리 캐시 (secrets 추가 후 캐시 꼬임 방지)."""
    if genai is None:
        raise RuntimeError("google-generativeai 패키지가 설치되어 있지 않습니다.")
    genai.configure(api_key=api_key)
    return True


def _extract_json(text: str) -> dict:
    """모델 응답에서 순수 JSON만 추출 (```json 펜스 제거 등)."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    # 혹시 앞뒤에 설명 문구가 붙는 경우 첫 '{'~마지막 '}' 구간만 추출
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


def call_gemini_json(prompt: str, system_instruction: str = "") -> dict:
    """
    구조화된 JSON 응답이 필요한 호출. 모델 체인을 순서대로 시도하고,
    전부 실패하면 예외를 발생시킨다. 반환값: dict (파싱된 JSON)
    """
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY가 설정되어 있지 않습니다. Streamlit Secrets에 추가해주세요."
        )
    _build_client(api_key)

    last_error = None
    for model_name in _get_model_chain():
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction or None,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.3,
                },
            )
            response = model.generate_content(prompt)
            text = response.text
            return _extract_json(text)
        except Exception as e:  # noqa: BLE001 - 폴백을 위해 광범위 캐치
            last_error = e
            continue

    raise RuntimeError(
        f"모든 AI 모델 호출에 실패했습니다 (마지막 오류: {last_error}). "
        "잠시 후 다시 시도하거나 네트워크/API 키 상태를 확인해주세요."
    )


def is_ai_configured() -> bool:
    return bool(st.secrets.get("GEMINI_API_KEY")) and genai is not None

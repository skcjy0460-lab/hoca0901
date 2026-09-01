# 🏥 병원 조직도 설계 AI

주식회사 메디엄 — 병원 개원·경영 컨설팅용 **AI 조직도 자동 설계 및 진단 프로그램**입니다.
병원 종별·병상 수·진료과목·현재 인력 현황을 입력하면 AI(Gemini)가 조직 구조 초안과
진단 코멘트를 생성하고, 이를 인터랙티브하게 편집한 뒤 Excel/PowerPoint/HTML로
바로 컨설팅 산출물로 활용할 수 있습니다.

## 핵심 기능

1. **병원 정보 입력** — 병원 종별, 병상 수, 진료과목, 현재 인력, 애로사항 입력
2. **AI 조직 진단** — Gemini API가 입력 정보를 분석해 조직 구조안(JSON) + 문제점 진단 + 개선안 생성
   (모델 실패 시 `gemini-3.6-flash → gemini-3.5-flash-lite → gemini-2.5-flash → gemini-2.0-flash` 순서로 자동 폴백)
3. **조직도 편집기** — 노드(직책/부서) 추가·수정·삭제, Graphviz 기반 실시간 시각화,
   순환 참조·통제범위(직속 부하 수) 초과 자동 경고
4. **성장 단계 로드맵** — 동일 조직 골격에서 개원초기/안정기/성장기 3단계 인원 배치 시뮬레이션 및 비교 차트
5. **내보내기**
   - Excel: 조직 인원표 + 병원 개요 + 진단 체크리스트 + AI 진단 결과 (서식 적용)
   - PowerPoint: 도형/텍스트를 자유롭게 편집 가능한 조직도 슬라이드 (와이드스크린, 범례 포함)
   - HTML: 다크 네이비 브랜디드 진단 보고서 (조직도 이미지 임베드, 단일 파일)

## 이 프로그램만의 차별점

- **통제범위(Span of Control) 자동 진단**: 관리자 1인당 직속 보고 인원이 권장 범위(5~10명)를
  초과하면 자동으로 경고하여 중간관리 계층 설계를 유도합니다.
- **개원 단계별 로드맵**: 정적인 조직도 1장이 아니라, 병원이 성장하면서 조직이 어떻게
  진화해야 하는지를 3단계로 시뮬레이션합니다.
- **AI 진단 + 수동 편집의 하이브리드**: AI가 초안을 잡고, 컨설턴트가 현장 감각으로
  세부 조정하는 구조 — AI 추천을 맹신하지 않고 검증할 수 있도록 원본 JSON도 함께 제공합니다.
- **법적 리스크 관리**: 법정 인력 기준처럼 시점에 따라 바뀌는 수치는 AI가 단정하지 않고
  "최신 법령 확인 필요"로 안내하도록 프롬프트에 명시했습니다 (컨설팅 산출물의 법적 리스크 최소화).

## 설치 및 실행

```bash
pip install -r requirements.txt
# Graphviz 시스템 바이너리가 필요합니다 (로컬: brew install graphviz / apt install graphviz)
streamlit run app.py
```

### Streamlit Cloud 배포 시

- `packages.txt`가 저장소 루트에 있어야 Graphviz 바이너리와 한글 폰트(NanumGothic)가 설치됩니다.
- `.streamlit/secrets.toml.example`을 참고해 앱 설정 → Secrets에 `GEMINI_API_KEY`를 등록하세요.
- 유료 배포 시 `VALID_LICENSE_KEYS`를 등록하면 라이선스 키 입력 화면이 활성화됩니다
  (미등록 시 인증 없이 바로 사용 가능 — 로컬 개발/데모용).

## 폴더 구조

```
app.py                      # 진입점 (st.navigation)
utils/
  ai_client.py               # Gemini 폴백 체인 클라이언트
  org_data.py                 # 병원 종별 템플릿, 참고 기준 데이터
  org_chart_builder.py        # 트리 데이터 구조, 검증, Graphviz 렌더링
  export_utils.py             # Excel/PPTX/HTML 내보내기
  licensing.py                 # 라이선스 키 게이트
views/
  1_병원정보입력.py
  2_AI조직진단.py
  3_조직도편집기.py
  4_성장로드맵.py
  5_내보내기.py
requirements.txt
packages.txt
.streamlit/secrets.toml.example
```

## ⚠️ 법적 유의사항

본 프로그램이 제시하는 조직 구조, 인력 배치, 성장 단계별 인원 배수는 **일반적인 컨설팅
참고 프레임워크**이며, 의료법 시행규칙상 정확한 법정 정원·필수 인력 기준은 병원 종별/
연도별로 개정되므로 실제 개원 인허가 및 인력 신고 업무에는 반드시 최신 법령 원문과
관할 보건소 확인 절차를 거쳐야 합니다.

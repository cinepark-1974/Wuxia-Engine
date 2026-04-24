# ⚔️ Wuxia Engine v1.0

블루진픽처스 무협 웹소설 전용 집필 엔진.

## 개요

Wuxia Engine은 **아이디어 고정 · 시장 포지셔닝 · 무협 특화 집필**을 수행하는 
무협 장르 전용 AI 집필 파트너입니다.

Web Novel Engine v2.6의 검증된 3단계 파이프라인을 기반으로,
무협 전용 Rule Pack과 6대 공식 매칭 시스템을 탑재했습니다.

## 핵심 기능

### 🎯 STEP 1. 시장 포지셔닝
- 기획자가 입력한 아이디어를 6대 무협 공식과 자동 매칭
- 플랫폼별 적합도 매트릭스 제공 (문피아·카카오·네이버·리디 등)
- 차별화 포인트 자동 추출 + 하이브리드 공식 추천
- 공식별 경고 플래그 및 집필 가이드

### 📖 STEP 2. 빌드업
- 공식별 맞춤 10비트 구조를 50화 Core Arc로 확장
- 캐릭터 바이블 카드 작성 (12분류 무협 직업팩)
- 회차별 플롯 일괄/개별 생성

### ✍️ STEP 3. 무협 집필
- 무협 Rule Pack 적용 집필
- 한자 병기 자동 관리 (첫 등장만)
- 고어체 필터 (재하·소생·본좌 등 금지)
- 글로벌 번역 친화도 자동 체크
- 독자 시뮬레이터 (플랫폼·페르소나별)

## 6대 무협 공식

| 공식 | 이름 | 포화도 | 글로벌 | 주 플랫폼 |
|------|------|--------|--------|-----------|
| F1 | 회귀 먼치킨 문파 재건 | 9.2 | ★★★ | 문피아·카카오 |
| F2 | 이세계 전생 무협 | 7.5 | ★★★★★ | 카카오·LINE |
| F3 | 시스템 게임 무협 | 8.7 | ★★★★★ | 카카오·웹툰·LINE |
| F4 | 학원 무협 | 4.5 | ★★★★ | 네이버 (하이브리드 필수) |
| F5 | 여성향 로맨스 무협 | 6.3 | ★★★ | 네이버·리디 |
| F6 | 정통 강호 서사 | 4.0 | ★★ | 문피아·리디 (하이브리드 권장) |

## 집필 원칙

### 문법 원칙
- 현대어 90% + 최소 고어체 (사부·사형·사제만)
- 지문 100% 현대 산문
- 금지 고어체: 재하·소생·귀공·시주·본좌·본궁 등

### 한자 병기
- 고유명사 **첫 등장 시에만** 병기: `황제통천검(皇帝通天劍)`
- 재등장 시: `황제통천검`
- 적용 대상: 문파·무공·기보·무기·지명

### 무협 세계관 기본
- 경지: 삼류→이류→일류→절정→초절정→화경→현경→생사경
- 내공 단위: 갑자(1갑자=60년)
- 정파·사파·마교 삼분 구도

## 설치 및 실행

### 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/cinepark-1974/wuxia-engine.git
cd wuxia-engine

# 의존성 설치
pip install -r requirements.txt

# API 키 설정 (택1)
# 방법 A: Streamlit secrets 사용
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml 파일에 ANTHROPIC_API_KEY 입력

# 방법 B: UI에서 직접 입력
# (실행 후 사이드바에서 API 키 입력)

# 실행
streamlit run main.py
```

### Streamlit Cloud 배포

1. GitHub 저장소 연결
2. Streamlit Cloud에서 Deploy
3. Settings > Secrets에 다음 추가:
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```

## 프로젝트 구조

```
wuxia-engine/
├── main.py                       # Streamlit UI 엔트리포인트
├── prompt.py                      # 집필 프롬프트 빌더 (무협 Rule Pack)
├── wuxia_formulas.py             # 6대 공식 + 비트 구조 + 매칭 알고리즘
├── wuxia_positioning.py          # STEP 1 시장 포지셔닝 모듈
├── wuxia_martial_arts.py         # 무공 체계 · 경지 · 문파 · 기보
├── wuxia_honorifics.py           # 호칭 · 한자 병기 · 고어체 필터
├── wuxia_profession_pack.py      # 12분류 무협 직업팩
├── wuxia_market_data.py          # 시장 데이터 (6개월 갱신)
├── file_parser.py                # PDF/DOCX/HWP/TXT 업로드 파서
├── docx_exporter.py              # DOCX 출력 (개별 회차 · 전체 합본)
├── requirements.txt
├── .streamlit/
│   ├── config.toml               # 블루진 테마
│   └── secrets.toml.example      # API 키 템플릿
├── .gitignore
└── README.md
```

## 기술 스택

- **Python** 3.11+
- **Streamlit** (UI)
- **Anthropic Claude API** (Opus 4.5 권장 / Sonnet 4.5 옵션)
- **python-docx, pypdf, olefile** (문서 처리)

## 지원 장르

**무협 전용** 엔진입니다.

- ❌ 로맨스·로판·현판·BL → Web Novel Engine v2.6 사용
- ✅ 무협 6대 공식 + 하이브리드 조합만 지원

## 집필 프로세스

```
STEP 1. 포지셔닝
  ├─ 아이디어 입력
  ├─ 6대 공식 매칭 (1+2순위)
  ├─ 플랫폼 전략 매트릭스
  └─ 차별화 포인트 도출

STEP 2. 빌드업
  ├─ Core Arc 50화 비트 확장
  ├─ 캐릭터 바이블 (12직업팩 활용)
  └─ 회차별 플롯 작성

STEP 3. 집필
  ├─ 무협 Rule Pack 적용
  ├─ 한자 병기 · 고어체 필터
  ├─ 품질 체크 (규칙 기반 + AI)
  ├─ 독자 시뮬레이터
  └─ TXT / ZIP 내보내기
```

## 개발 로드맵

### v1.0 (현재)
- 6대 공식 + 기본 3단계 파이프라인
- 무협 Rule Pack
- 프로젝트 저장/불러오기 (JSON)

### v1.1 (예정)
- 하이브리드 비트 머지 정교화
- DOCX 출력 지원
- 플랫폼별 자동 분량 조정

### v1.2 (예정)
- 시장 데이터 6개월 갱신 자동화
- Core Arc 생성 품질 향상
- 독자 시뮬레이터 페르소나 확장

## 유지보수

- **시장 데이터 갱신**: 6개월 주기 (연 2회)
- **공식 포화도 재산정**: 플랫폼 Top 30 재분석
- **Rule Pack 업데이트**: 집필 피드백 기반 지속 개선

## 라이선스

© 2026 Blue Jeans Pictures. All rights reserved.

## 관련 엔진

- **Web Novel Engine v2.6** — 범용 웹소설 (로맨스·로판·현판 등)
- **Creator Engine v2.3.10** — 영상·시리즈 기획
- **Writer Engine v3.1.1** — 시나리오 집필
- **Novel Engine v2.5** — 상업 소설

## 문의

블루진픽처스 문성주 대표  
GitHub: [@cinepark-1974](https://github.com/cinepark-1974)

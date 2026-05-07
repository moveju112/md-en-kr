# md-en-kr 스킬 설계

- 작성일: 2026-05-07
- 리포지토리: https://github.com/moveju112/md-en-kr.git
- 대상 플랫폼: Claude Code, Codex CLI

## 1. 목적

한글로 작성된 rule / MD 파일을 **AI 에이전트가 이해하기 쉬운 형태의 압축된 영어 마크다운**으로 변환해 토큰 사용량을 줄인다. 본질적인 규칙은 손실 없이 보존하고, 중복 표현·관용 어구만 제거한다.

## 2. 사용자 결정 사항 (Brainstorming 결과)

| 항목 | 결정 |
|---|---|
| 트리거 | 양방향 — 슬래시 명령(`/compress-rule`) + `description` 기반 자동 호출 |
| 출력 | 원본 파일 덮어쓰기 |
| 안전장치 | git clean 상태 확인 + diff 미리보기 + 파일별 사용자 승인 |
| 처리 범위 | 단일 파일 / 글롭 패턴 / 디렉토리 재귀 모두 지원 |
| 배포 | 단일 스킬 디렉토리 + `plugin.json` 동시 제공 |
| 호환 | Claude Code + Codex CLI 양쪽 동시 지원 |
| 변환 실행 | 호출한 에이전트가 인라인으로 수행 (외부 API/스크립트 없음) |
| YAML frontmatter | 구조 보존, 한글 값(`description` 등)만 영어로 번역, `name` 같은 식별자는 절대 변경 금지 |

## 3. 리포지토리 구조

```
md-en-kr/
├── SKILL.md          # 진실의 원천. 압축 규칙 + 실행 절차 모두 인라인 포함
├── plugin.json       # Claude Code plugin 메타 (marketplace 배포 대비)
├── README.md         # 양 플랫폼 설치/사용 가이드
├── AGENTS.md         # Codex CLI 진입점. SKILL.md 참조 지시
├── examples/
│   ├── before-ko.md  # 변환 전 예시
│   └── after-en.md   # 변환 후 예시
└── docs/superpowers/specs/
    └── 2026-05-07-md-en-kr-design.md   # 본 문서
```

보조 스크립트는 두지 않는다. 사전 검증(git clean 체크)은 SKILL.md 안의 인라인 bash 지시로 처리한다.

## 4. SKILL.md 설계

### 4.1 Frontmatter

```yaml
---
name: md-en-kr
description: Use when compressing Korean rule/MD files into compact English to reduce token usage. Triggers on "/compress-rule", "한글 룰 압축", "rule 영어 변환" requests, or when working with Korean .md rule files in skills/rules directories.
---
```

`description`은 영어로 작성하되 한글 트리거 문구를 함께 포함해 자동 호출 정확도를 높인다.

### 4.2 호출 시 절차

1. **인자 파싱**
   - 단일 파일 경로 / 글롭 패턴(`*.md`) / 디렉토리(재귀) 자동 분류
   - 디렉토리는 모든 `.md` 파일 수집 (숨김 디렉토리 제외)

2. **사전 검증** (인라인 bash)
   - 대상이 git 저장소인지 확인 (`git rev-parse --is-inside-work-tree`)
   - 각 파일의 워킹트리 클린 여부 확인 (`git status --porcelain <file>`)
   - 미커밋 변경이 있는 파일은 목록 출력 후 전체 중단

3. **파일별 순차 처리**
   1. 원본 파일 Read
   2. 압축 규칙(§5) 적용해 영어 버전 생성
   3. 변환 결과 자가 검증 (§5.3)
   4. 원본 vs 변환본 unified diff 표시
   5. 사용자에게 `apply / skip / abort` 선택 요청
   6. `apply`: 원본 덮어쓰기 / `skip`: 다음 파일 / `abort`: 전체 중단

4. **요약 보고**
   - 적용 N개 / 건너뜀 M개 / 추정 토큰 절감률(원본 대비 변환본 길이 비율)

### 4.3 동작 규칙

- 변환은 호출한 에이전트(Claude Code / Codex CLI)가 직접 수행
- 외부 API 호출, 외부 LLM 호출, 외부 스크립트 모두 사용하지 않음
- 에러 또는 사용자 abort 시 이미 적용된 파일은 그대로 둔다 (git으로 복구 가능)
- frontmatter 없는 파일도 정상 처리

## 5. 압축 규칙 세트

원본 프롬프트(다른 AI에서 받아온 압축 프롬프트)를 기반으로 스킬 형식에 맞게 보강한 규칙.

### 5.1 핵심 규칙 (원본 유지)

- 공격적 압축 / 중복 제거 / 짧은 명령형 불릿 선호
- 다음 항목은 원문 그대로 보존:
  - 파일 경로
  - 명령어
  - 코드 식별자 (클래스 / 메서드 / 함수 / 변수 / 네임스페이스)
  - 스킬 이름
  - 트리거 문구
  - 출력 포맷 예시
  - 응답 언어 규칙
  - 안전 / 파괴적 동작 경고
  - 아키텍처 제약
  - 코딩 컨벤션
- 한글이 규칙 자체로 요구되는 경우(예: `일반 말투`, `stop caveman`, `/graphify`)는 한글/원문 그대로 유지
- 변환 결과는 마크다운 블록 하나만, 메타 코멘트 / 변환 안내 / "Here is..." 류 금지

### 5.2 보강 규칙 (이번에 추가)

1. **YAML frontmatter** — 키는 보존, 한글 값(특히 `description`)만 영어로 번역. `name` 같은 식별자는 절대 변경 금지.
2. **헤딩 레벨 보존** — `#`, `##` 구조를 임의로 변경하지 않는다. 다른 스킬/문서가 이 헤딩을 참조할 수 있다.
3. **링크/이미지 경로 보존** — `[텍스트](경로)`의 경로는 그대로, 텍스트만 영어화.
4. **인라인 코드 보존** — `` ` ``로 감싼 내용은 절대 번역하지 않는다 (식별자/명령어 가능성).
5. **자기 참조 메타 코멘트 금지** — "compressed", "translated", "token-optimized" 같은 변환 관련 메타 코멘트 추가 금지.
6. **안전 워딩 강도 유지** — "절대", "반드시", "MUST", "NEVER" 같은 강도는 영어에서도 동일 강도(`MUST`, `NEVER`, `under no circumstances`)로 유지.
7. **결정론적 어휘 매핑** — 같은 한글 용어는 같은 영어 용어로 일관 변환:
   - 스킬 → `skill`
   - 규칙 → `rule`
   - 트리거 → `trigger`
   - 호출 → `invoke`
   - 응답 → `response`
   - (필요 시 SKILL.md에 매핑 표로 명시)

### 5.3 변환 후 자가 검증

변환 직후 에이전트가 다음을 셀프 체크. 누락 시 재시도:

- 원본의 모든 파일 경로(`/` 포함 토큰)가 결과에 존재하는가
- 원본의 모든 코드블록(```` ``` ````) 개수와 내용이 일치하는가
- 원본의 모든 인라인 코드(`` ` ``) 식별자가 결과에 존재하는가
- frontmatter `name` 값이 변경되지 않았는가

### 5.4 의도적으로 빼는 것

- 원본 프롬프트의 `<PASTE_KOREAN_MD_HERE>` 입력 placeholder — 스킬은 파일을 직접 읽으므로 불필요
- "Do not include 'Here is...'" 류 응답 메타 지시 — 파일에 직접 쓰는 동작이므로 자동 충족

## 6. 양 플랫폼 호환

### 6.1 Claude Code

```bash
git clone https://github.com/moveju112/md-en-kr.git ~/.claude/skills/md-en-kr
```

- 자동 인식, `description` 기반 자동 호출 + 사용자 직접 호출 모두 지원
- 향후 plugin marketplace 등록 시 `/plugin install md-en-kr` 한 줄로 설치 가능

### 6.2 Codex CLI

```bash
git clone https://github.com/moveju112/md-en-kr.git ~/.codex/skills/md-en-kr
```

- `AGENTS.md`가 진입점. 내용은 `SKILL.md` 절차를 그대로 따르도록 지시 (`See SKILL.md for full procedure.`)
- Codex가 AGENTS.md를 자동으로 컨텍스트에 포함하므로 `/compress-rule` 또는 자연어 호출로 트리거

### 6.3 호출 예시 (양 플랫폼 동일)

```
/compress-rule path/to/rule.md
/compress-rule path/to/dir/
/compress-rule "rules/*.md"
```

자연어 호출:

> 이 한글 rule 파일들 영어로 압축해줘: rules/*.md

## 7. README.md 구성

- 스킬 소개 (1–2줄)
- 설치
  - Claude Code 섹션
  - Codex CLI 섹션
- 사용법 (3가지 호출 예시)
- 안전 동작 설명 (git clean 필수, diff 승인 흐름)
- 예시 (`examples/before-ko.md`, `examples/after-en.md` 링크)

## 8. 비범위 (Out of Scope)

- 자동 토큰 측정/리포팅 (단순 길이 비율로 대체)
- plugin marketplace 실제 등록 (`plugin.json` 준비만, 등록은 별도 작업)
- 비-`.md` 파일 지원 (`.txt`, `.rst` 등)
- 영어 → 한글 역변환
- 다중 파일 일괄 자동 적용 (안전을 위해 항상 파일별 승인)

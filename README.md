# md-en-kr

한글로 작성된 rule / MD 파일을 압축된 영어 마크다운으로 변환해 토큰 사용량을 줄이는 스킬. **Claude Code**와 **Codex CLI** 양쪽에서 동작합니다.

원본 파일을 직접 덮어쓰며, 파일별로 diff 미리보기를 보여준 뒤 사용자 승인을 받습니다.

## 설치

### Claude Code

```bash
git clone https://github.com/moveju112/md-en-kr.git ~/.claude/skills/md-en-kr
```

설치 후 자동 인식되어 `description` 기반 자동 호출 + 직접 호출 모두 가능합니다.

### Codex CLI

```bash
git clone https://github.com/moveju112/md-en-kr.git ~/.codex/skills/md-en-kr
```

`AGENTS.md`가 진입점이며 Codex가 자동으로 컨텍스트에 포함합니다.

## 사용법

```
/compress-rule path/to/rule.md
/compress-rule path/to/dir/
/compress-rule "rules/*.md"
/compress-rule --apply rules/*.md                   # 승인 없이 일괄 적용
/compress-rule --mode=plan docs/plans/              # 명시적 모드 지정
/compress-rule --apply --mode=reference docs/       # 두 옵션 조합
```

자연어로도 호출할 수 있습니다:

> 이 한글 rule 파일들 영어로 압축해줘: rules/*.md
> 위 파일들 승인 없이 그냥 적용해줘

## 문서 타입별 모드

`--mode=X`로 명시하지 않으면 파일 경로/이름으로 자동 추론합니다.

| 모드 | 추론 조건 (경로/파일명) | 보존 우선순위 | 압축 목표 비율 |
|---|---|---|---|
| `rule` | `rule`, `RULES`, `/rules/`, `CLAUDE.md`, `AGENTS.md`, `CONVENTIONS` | 행동 규칙(MUST/NEVER) 절대 보존 | 60–85% |
| `plan` | `plan`, `spec`, `TODO`, `tasks`, `roadmap`, `checklist` | TODO/체크리스트/경로/날짜 절대 보존 | 30–50% |
| `reference` | 그 외 모든 파일 | 사실/구조 요약, 산문 중복 제거 가능 | 40–70% |

압축 비율은 가이드라인이며, **의미 보존이 비율보다 우선**합니다.

## 동작

1. 인자(파일 / 글롭 / 디렉토리 + 선택적 `--apply` + 선택적 `--mode=X`)를 파일 목록으로 확장합니다.
2. 파일별로:
   - 모드 결정 (`--mode` 우선, 없으면 경로 추론)
   - 모드별 강조점에 따라 압축 규칙 적용해 영어 버전 생성
   - **자가 검증 스크립트** 실행 (`python3 scripts/verify_md_conversion.py`)
     - 10개 항목 검증: frontmatter `name`, fenced/inline 코드, heading 시퀀스, 체크리스트 개수, 테이블 행, 링크 target, 경로 토큰, URL, IPv4
   - **diff 정책** (아래 표 참고)
3. 처리 결과 요약 (적용 N개, 건너뜀 M개, 검증 실패 K개, 모드별 비율, 총 바이트 비율). git-untracked/ignored 처리 파일도 표시.

### diff 정책

| 조건 | 동작 |
|---|---|
| `--apply` 모드 | diff 출력 없이 검증 통과 즉시 덮어쓰기 |
| 1–3개 파일 (대화형) | 파일별 full diff, `apply / skip / abort` 선택 |
| 4개 이상 (대화형) | 요약 테이블(파일명/모드/바이트/비율/+−) 먼저, `apply all / review individually / abort` 선택. `review individually` 시 1–3개 흐름으로 fall back |

## Git/ignore 처리

- 파일 수집은 **glob 결과 기준**입니다. `.gitignore`나 `.git/info/exclude`는 참조하지 않습니다.
- git-untracked 또는 git-ignored 파일도 정상 처리됩니다.
- 단, 그런 파일은 `git status`에 보이지 않을 수 있으므로 처리 결과 요약에서 별도로 표시됩니다.

## 보존 항목 (절대 변경하지 않음)

- 파일 경로, 명령어, 코드 식별자
- 스킬 이름, 트리거 문구, 출력 포맷 예시
- 안전 / 파괴적 동작 경고
- 코딩 컨벤션 / 아키텍처 제약
- 한글이 규칙 자체로 요구되는 경우 — backtick 안이든 밖이든 (예: `일반 말투`, `/graphify`, `사용자가 "X"라고 말하면` 형태의 한글 트리거)
- YAML frontmatter의 `name` 값과 키 구조
- 숫자 코드 (HTTP status, error code, enum value, version `v1.2.3`)
- enum / range 표현 (`[0, 100]`, `1..10`)
- SQL 키워드 및 테이블/컬럼/스키마/DB 식별자
- URL (`http://`, `https://`, `ftp://`, `ws(s)://`)
- 네트워크 식별자 (IPv4, IPv6, hostname, domain, port)
- Mermaid / PlantUML / ASCII diagram 블록 내용
- 체크리스트 상태 (`- [x]` / `- [ ]`)와 항목 수

## 예시

- 입력: [`examples/before-ko.md`](examples/before-ko.md)
- 출력: [`examples/after-en.md`](examples/after-en.md)

## 안전

- 기본 모드는 모든 파일이 덮어쓰기 직전에 **diff 미리보기 + `apply` 승인**을 거칩니다.
- `--apply` 모드는 사용자 승인 없이 자동 적용하므로, **자가 검증 스크립트 통과**가 유일한 안전망입니다. 중요한 파일은 사용 전 버전 관리 또는 별도 백업을 권장합니다.
- 자가 검증이 3회 연속 실패한 파일은 그대로 두고 (덮어쓰지 않음) 다음 파일로 넘어갑니다.
- `skip`을 선택한 파일은 변경되지 않습니다.
- `abort`로 중단해도 이미 `apply`된 파일은 그대로 유지됩니다 (이전 파일은 영향 없음).

## 비범위

- 영어 → 한글 역변환
- `.md` 외 파일 (`.txt`, `.rst` 등)
- 사용자 승인 없는 일괄 자동 적용
- 외부 LLM/API 호출 (호출한 에이전트가 직접 변환)

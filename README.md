# md-en-kr

한글로 작성된 rule / MD 파일을 압축된 영어 마크다운으로 변환해 토큰 사용량을 줄이는 스킬. **Claude Code**와 **Codex CLI** 양쪽에서 동작합니다.

원본 파일을 직접 덮어쓰며, 변환 전 git clean 상태를 확인하고 파일별로 diff를 보여준 뒤 사용자 승인을 받습니다.

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
```

자연어로도 호출할 수 있습니다:

> 이 한글 rule 파일들 영어로 압축해줘: rules/*.md

## 동작

1. 인자(파일 / 글롭 / 디렉토리)를 파일 목록으로 확장합니다.
2. **각 파일이 git clean 상태인지 확인**합니다. 미커밋 변경이 있으면 전체 중단.
3. 파일별로:
   - 압축 규칙을 적용해 영어 버전 생성
   - 변환 결과 자가 검증 (경로 / 코드블록 / 인라인 코드 / frontmatter 보존 확인)
   - **diff 미리보기**를 보여주고 `apply / skip / abort` 선택
4. 처리 결과 요약 (적용 N개, 건너뜀 M개, 길이 비율).

## 보존 항목 (절대 변경하지 않음)

- 파일 경로, 명령어, 코드 식별자
- 스킬 이름, 트리거 문구, 출력 포맷 예시
- 안전 / 파괴적 동작 경고
- 코딩 컨벤션 / 아키텍처 제약
- 한글이 규칙 자체로 요구되는 경우 (예: `일반 말투`, `/graphify`)
- YAML frontmatter의 `name` 값과 키 구조

## 예시

- 입력: [`examples/before-ko.md`](examples/before-ko.md)
- 출력: [`examples/after-en.md`](examples/after-en.md)

## 안전

- 원본을 덮어쓰므로 **git 트래킹 + 클린 상태**가 필수입니다.
- 롤백은 `git checkout <file>` 한 줄로 가능합니다.
- 변환 도중 abort해도 이미 적용된 파일은 그대로 남습니다 (git으로 복구).

## 비범위

- 영어 → 한글 역변환
- `.md` 외 파일 (`.txt`, `.rst` 등)
- 사용자 승인 없는 일괄 자동 적용
- 외부 LLM/API 호출 (호출한 에이전트가 직접 변환)

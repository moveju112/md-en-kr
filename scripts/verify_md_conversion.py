#!/usr/bin/env python3
"""md-en-kr 변환 결과 검증 스크립트.

원본 한글 .md 파일과 변환된 영어 .md 파일을 비교하여
보존되어야 할 항목들이 모두 유지되었는지 검증한다.

사용법:
    python3 verify_md_conversion.py <original.md> <converted.md>
    python3 verify_md_conversion.py <original.md> -      # converted를 stdin으로 입력

종료 코드:
    0  모든 검증 통과
    1  검증 실패 (구체적 사유는 stderr로 출력)
    2  잘못된 사용
"""

import re
import sys
from pathlib import Path

# path-token 검출에 사용하는 알려진 파일 확장자 목록
KNOWN_EXTENSIONS = {
    "md", "txt", "log", "csv", "tsv", "json", "yaml", "yml", "toml",
    "ini", "cfg", "conf", "env",
    "py", "js", "ts", "tsx", "jsx", "mjs", "cjs",
    "rb", "go", "rs", "java", "kt", "swift", "c", "cpp", "cc", "h",
    "hpp", "cs", "php", "lua", "pl", "scala", "clj",
    "html", "htm", "css", "scss", "sass", "less",
    "sql", "graphql", "proto",
    "sh", "bash", "zsh", "fish", "ps1", "bat",
    "xml", "svg", "vue", "dart",
    "lock", "diff", "patch",
}

FENCED_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)
CHECKLIST_DONE_RE = re.compile(r"^[ \t]*-[ \t]+\[[xX]\]", re.MULTILINE)
CHECKLIST_TODO_RE = re.compile(r"^[ \t]*-[ \t]+\[ \]", re.MULTILINE)
LINK_TARGET_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|[\s\-:|]+\|\s*$")
ABS_OR_REL_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])(?:\.{1,2}/|/|~/)[A-Za-z0-9_./\-]+")
EXT_FILE_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z0-9_\-]+)\.([A-Za-z0-9]{1,6})(?![A-Za-z0-9_])")
FRONTMATTER_RE = re.compile(r"\A---\s*\n([\s\S]*?)\n---\s*(?:\n|$)")
NAME_LINE_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)
URL_RE = re.compile(r"(?:https?|ftp|ws|wss)://[^\s\)\]\}<>\"'`]+")


def strip_fenced_blocks(text):
    """fenced code block 영역만 빈 문자열로 치환."""
    return FENCED_BLOCK_RE.sub("", text)


def strip_inline_code(text):
    """inline code 영역만 빈 문자열로 치환."""
    return INLINE_CODE_RE.sub("", text)


def get_frontmatter_name(text):
    """frontmatter의 name 값을 추출. 없으면 None."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    nm = NAME_LINE_RE.search(m.group(1))
    return nm.group(1).strip() if nm else None


def check_frontmatter_name(original, converted):
    """frontmatter name 보존 검증."""
    original_name = get_frontmatter_name(original)
    if original_name is None:
        return []
    converted_name = get_frontmatter_name(converted)
    if original_name != converted_name:
        return [
            f"frontmatter name 변경됨: {original_name!r} -> {converted_name!r}"
        ]
    return []


def check_fenced_blocks(original, converted):
    """fenced code block 1:1 보존 검증."""
    original_blocks = FENCED_BLOCK_RE.findall(original)
    converted_blocks = FENCED_BLOCK_RE.findall(converted)
    issues = []
    if len(original_blocks) != len(converted_blocks):
        issues.append(
            f"fenced code block 개수 불일치: "
            f"original={len(original_blocks)}, converted={len(converted_blocks)}"
        )
    converted_set = set(converted_blocks)
    for block in original_blocks:
        if block not in converted_set:
            preview = block.strip().splitlines()[0][:60] if block.strip() else "(empty)"
            issues.append(f"fenced code block 손실: {preview!r}")
    return issues


def check_inline_code(original, converted):
    """inline code 토큰의 고유 집합이 모두 변환본에 존재하는지 검증."""
    original_text = strip_fenced_blocks(original)
    converted_text = strip_fenced_blocks(converted)
    original_tokens = set(INLINE_CODE_RE.findall(original_text))
    converted_tokens = set(INLINE_CODE_RE.findall(converted_text))
    missing = original_tokens - converted_tokens
    return [f"inline code 손실: `{token}`" for token in sorted(missing)]


def check_heading_sequence(original, converted):
    """heading 레벨 시퀀스 동일성 검증."""
    original_no_fence = strip_fenced_blocks(original)
    converted_no_fence = strip_fenced_blocks(converted)
    original_levels = [len(m) for m in HEADING_RE.findall(original_no_fence)]
    converted_levels = [len(m) for m in HEADING_RE.findall(converted_no_fence)]
    if original_levels != converted_levels:
        return [
            f"heading 레벨 시퀀스 불일치: "
            f"original={original_levels}, converted={converted_levels}"
        ]
    return []


def check_checklists(original, converted):
    """체크리스트 항목 개수 보존 검증."""
    issues = []
    original_done = len(CHECKLIST_DONE_RE.findall(original))
    converted_done = len(CHECKLIST_DONE_RE.findall(converted))
    original_todo = len(CHECKLIST_TODO_RE.findall(original))
    converted_todo = len(CHECKLIST_TODO_RE.findall(converted))
    if original_done != converted_done:
        issues.append(
            f"체크리스트 [x] 개수 불일치: "
            f"original={original_done}, converted={converted_done}"
        )
    if original_todo != converted_todo:
        issues.append(
            f"체크리스트 [ ] 개수 불일치: "
            f"original={original_todo}, converted={converted_todo}"
        )
    return issues


def count_table_rows(text):
    """마크다운 테이블의 데이터 행 수를 센다 (헤더 + 본문, 구분자 제외)."""
    rows = 0
    for line in TABLE_LINE_RE.findall(text):
        if not TABLE_SEPARATOR_RE.match(line):
            rows += 1
    return rows


def check_table_rows(original, converted):
    """테이블 행 수 보존 검증."""
    original_rows = count_table_rows(strip_fenced_blocks(original))
    converted_rows = count_table_rows(strip_fenced_blocks(converted))
    if original_rows != converted_rows:
        return [
            f"테이블 행 수 불일치: "
            f"original={original_rows}, converted={converted_rows}"
        ]
    return []


def check_link_targets(original, converted):
    """[text](target) 형태의 링크 target 보존 검증."""
    original_targets = set(LINK_TARGET_RE.findall(original))
    converted_targets = set(LINK_TARGET_RE.findall(converted))
    missing = original_targets - converted_targets
    return [f"링크 target 손실: ({target})" for target in sorted(missing)]


def extract_path_tokens(text):
    """fenced/inline code/URL을 제외한 영역에서 path-like 토큰을 추출.

    path-like 정의:
      - /, ./, ../, ~/ 로 시작하는 경로
      - 알려진 파일 확장자(KNOWN_EXTENSIONS)를 가진 <name>.<ext> 형태
    URL은 별도 검사(check_urls)에서 다루므로 여기서는 제거한다.
    """
    cleaned = URL_RE.sub("", strip_inline_code(strip_fenced_blocks(text)))
    tokens = set()
    for match in ABS_OR_REL_PATH_RE.finditer(cleaned):
        tokens.add(match.group(0).rstrip("."))
    for match in EXT_FILE_RE.finditer(cleaned):
        ext = match.group(2).lower()
        if ext in KNOWN_EXTENSIONS:
            tokens.add(match.group(0))
    return tokens


def check_path_tokens(original, converted):
    """경로 토큰 보존 검증 (backtick 안 경로는 inline code 검증이 담당)."""
    original_paths = extract_path_tokens(original)
    converted_paths = extract_path_tokens(converted)
    missing = original_paths - converted_paths
    return [f"경로 토큰 손실: {token}" for token in sorted(missing)]


CHECKS = (
    ("frontmatter name", check_frontmatter_name),
    ("fenced code blocks", check_fenced_blocks),
    ("inline code tokens", check_inline_code),
    ("heading sequence", check_heading_sequence),
    ("checklists", check_checklists),
    ("table rows", check_table_rows),
    ("link targets", check_link_targets),
    ("path tokens", check_path_tokens),
)


def read_input(path_arg):
    """파일 경로 또는 '-'(stdin)에서 텍스트를 읽어 반환."""
    if path_arg == "-":
        return sys.stdin.read()
    return Path(path_arg).read_text(encoding="utf-8")


def main(argv):
    if len(argv) != 3:
        print(
            "사용법: python3 verify_md_conversion.py <original.md> <converted.md|->",
            file=sys.stderr,
        )
        return 2

    try:
        original_text = read_input(argv[1])
        converted_text = read_input(argv[2])
    except OSError as exc:
        print(f"파일 읽기 실패: {exc}", file=sys.stderr)
        return 2

    issues = []
    for name, check in CHECKS:
        for issue in check(original_text, converted_text):
            issues.append(f"[{name}] {issue}")

    if issues:
        for issue in issues:
            print(f"FAIL: {issue}", file=sys.stderr)
        return 1

    print("OK: 모든 보존 항목 검증 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

---
name: md-en-kr
description: Use when compressing Korean rule/MD files into compact English to reduce token usage. Triggers on "/compress-rule", "한글 룰 압축", "rule 영어 변환" requests, or when working with Korean .md rule files in skills/rules directories.
---

# md-en-kr

Compress Korean Markdown rule files into compact English while preserving every behaviorally meaningful instruction. Overwrites originals after user approval.

## Activation

- Slash command: `/compress-rule [--apply] <path>`
- Natural language: "이 한글 rule 파일들 영어로 압축해줘", "compress these korean rules"
- Targets: single `.md` file, glob (`rules/*.md`), or directory (recursive)

## Procedure

### 1. Argument parsing
- Resolve the user-provided argument into a concrete file list and an `auto_apply` boolean.
- `auto_apply` is true when the invocation contains `--apply`, a standalone `apply` token, or natural-language phrasing such as "승인 없이", "그냥 적용", "auto apply", "no prompt". Default is false.
- Single file: use as-is.
- Glob: expand via shell.
- Directory: collect all `*.md` recursively, excluding hidden directories (`.git`, `.venv`, `node_modules`, etc.).
- If the resolved list is empty, abort with a clear message.
- If the resolved list contains non-`.md` files, abort and list them. Only `.md` files are supported.

### 2. Per-file processing (sequential)

For each file in the resolved list:

1. Read the original file.
2. Apply the compression rules in §Rules to produce the English version.
3. Write the candidate output to a temporary path (e.g., `/tmp/<basename>.converted.md`).
4. Run the §Self-Verification script against the temporary path. On failure, regenerate (up to 3 attempts; abort that file on the third failure with the script's stderr).
5. Branch on `auto_apply`:
   - **`auto_apply=true`**: overwrite the original directly with the verified content. No diff, no prompt. Continue.
   - **`auto_apply=false` (default)**: show a unified diff (original vs. compressed) and ask the user `apply / skip / abort`.
     - `apply`: overwrite the original file with the compressed content.
     - `skip`: leave the file unchanged, continue to the next file.
     - `abort`: stop the run. Already-applied files remain unchanged.

### 3. Summary

Report: applied N, skipped M, aborted? Include a length-ratio estimate per file (e.g., `42% of original`). For runs of 4+ files, also print a total-bytes ratio.

## Rules

### Core (preserve exactly)

- File paths
- Commands
- Code identifiers (class, method, function, variable, namespace names)
- Skill names
- Trigger phrases
- Output format examples
- Required response language rules
- Safety / destructive-action warnings
- Architecture constraints
- Coding conventions
- Quoted/inline-code phrases that are themselves part of the rule — typically phrases inside `` ` `` backticks that match user trigger words or required wording (e.g., `일반 말투`, `stop caveman`, `/graphify`)

### Compression behavior

- Compress aggressively; remove duplicated or redundant wording.
- Keep only behaviorally meaningful instructions.
- Prefer short imperative bullets over paragraphs.
- Use compact agent-friendly terms.
- Output Markdown only — no meta comments, no "Here is...", no commentary about the conversion itself.

### Markdown handling

- Preserve heading levels exactly. Do not renumber or restructure.
- Preserve link/image targets: `[text](path)` — translate `text`, leave `path` untouched.
- NEVER translate content inside inline code (`` ` ``) or fenced code blocks (```` ``` ````). They contain identifiers/commands.
- Code blocks count and content must match the original 1:1.

### YAML frontmatter

- Preserve the structure (keys and order).
- Translate Korean values into English (notably `description`).
- NEVER change the `name` value or any other identifier-like value.
- If a value is already English or non-text (boolean, number, list of identifiers), leave it.
- If the file has no frontmatter, skip this subsection's rules entirely.

### Safety wording

- Maintain the original strength. Map "절대", "반드시", "결코" to `MUST`, `NEVER`, `under no circumstances` as appropriate.
- Do not soften warnings.

### Deterministic vocabulary

Use consistent English terms across the output:

| 한글 | English |
|---|---|
| 스킬 | skill |
| 규칙 | rule |
| 트리거 | trigger |
| 호출 | invoke |
| 응답 | response |
| 검증 | verify / verification |
| 사용자 | user |
| 에이전트 | agent |

Extend this mapping consistently within a single file.

## Self-Verification

After producing the compressed output and writing it to a temporary path, the agent MUST run the bundled verification script before either showing the diff or auto-applying:

```bash
python3 scripts/verify_md_conversion.py <original-path> <converted-tmp-path>
```

Exit code 0 = pass; non-zero = fail with reasons on stderr. The script enforces:

1. **Frontmatter `name` unchanged** (when frontmatter exists).
2. **Fenced code blocks** (` ``` ` blocks) preserved 1:1 in count and content.
3. **Unique inline-code tokens** (`` `...` ``) from the original each appear at least once in the output.
4. **Heading level sequence** identical (e.g., `[1, 2, 2, 3]`).
5. **Checklist counts** for `- [x]` and `- [ ]` preserved separately.
6. **Markdown table data row counts** preserved.
7. **Link targets** in `[text](target)` preserved.
8. **Path-like tokens** outside backticks preserved. Path-like = starts with `/`, `./`, `../`, `~/`, or matches `<name>.<ext>` where `<ext>` is a known file extension. (Tokens already inside backticks are covered by check #3.)

If the script fails, regenerate (up to 3 attempts). On the 3rd failure, abort that file and surface the script's stderr to the user. Do not show a failing diff and do not auto-apply.

## Output writing

- Overwrite the original file with the compressed content on `apply`.
- Do not write any other file (no `.bak`, no sibling). The diff preview before `apply` is the user's last chance to back out.

## Out of Scope

- Reverse direction (English → Korean).
- Non-`.md` files.
- External LLM/API calls — the calling agent (Claude Code or Codex CLI) performs the conversion itself.

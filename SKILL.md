---
name: md-en-kr
description: Use when compressing Korean rule/MD files into compact English to reduce token usage. Triggers on "/compress-rule", "한글 룰 압축", "rule 영어 변환" requests, or when working with Korean .md rule files in skills/rules directories.
---

# md-en-kr

Compress Korean Markdown rule files into compact English while preserving every behaviorally meaningful instruction. Overwrites originals after user approval.

## Activation

- Slash command: `/compress-rule <path>`
- Natural language: "이 한글 rule 파일들 영어로 압축해줘", "compress these korean rules"
- Targets: single `.md` file, glob (`rules/*.md`), or directory (recursive)

## Procedure

### 1. Argument parsing
- Resolve the user-provided argument into a concrete file list.
- Single file: use as-is.
- Glob: expand via shell.
- Directory: collect all `*.md` recursively, excluding hidden directories (`.git`, `.venv`, `node_modules`, etc.).
- If the resolved list is empty, abort with a clear message.
- If the resolved list contains non-`.md` files, abort and list them. Only `.md` files are supported.

### 2. Pre-flight check (MUST pass before any conversion)

Run these checks inline. Abort the entire run if any fail.

```bash
git rev-parse --is-inside-work-tree
```

For each target file:

```bash
git ls-files --error-unmatch <file>            # tracked?
git status --porcelain <file>                  # clean? (must produce empty output)
```

If any file is untracked or has uncommitted changes, list those files and abort. Reason: overwriting requires `git checkout` as the rollback path.

### 3. Per-file processing (sequential)

For each file in the resolved list:

1. Read the original file.
2. Apply the compression rules in §Rules to produce the English version.
3. Run the self-verification in §Self-Verification on the produced output. If any check fails, regenerate.
4. Show a unified diff (original vs. compressed) to the user.
5. Ask the user: `apply / skip / abort`.
   - `apply`: overwrite the original file with the compressed content.
   - `skip`: leave the file unchanged, continue to the next file.
   - `abort`: stop the run. Already-applied files remain (recoverable via git).

### 4. Summary

Report: applied N, skipped M, aborted? Include a length-ratio estimate per file (e.g., `42% of original`).

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

After producing the compressed output, the agent MUST verify before showing the diff:

1. Every file path token from the original (any string containing `/`) appears in the output.
2. Every fenced code block from the original is present with identical content.
3. Every unique inline-code token (`` `...` ``) from the original appears at least once in the output.
4. Frontmatter `name` value is unchanged.
5. The required-Korean phrases listed in §Rules → Core are still present verbatim.

If any check fails, regenerate (up to 3 attempts). If checks still fail on the third attempt, abort that file with a message listing which check failed and why. Do not surface a failing diff to the user.

## Output writing

- Overwrite the original file with the compressed content on `apply`.
- Do not write any other file (no `.bak`, no sibling). Rollback path is `git checkout <file>`.

## Out of Scope

- Reverse direction (English → Korean).
- Non-`.md` files.
- Auto-applying without per-file approval.
- External LLM/API calls — the calling agent (Claude Code or Codex CLI) performs the conversion itself.

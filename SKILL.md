---
name: md-en-kr
description: Use when compressing Korean rule/MD files into compact English to reduce token usage, or when adding a user-specified Korean rule to a project rule file during conversion. Triggers on "/compress-rule", "한글 룰 압축", "rule 영어 변환", "프로젝트 rule에 ... 추가" requests, or when working with Korean .md rule files in skills/rules directories.
---

# md-en-kr

Compress Korean Markdown rule files into compact English while preserving every behaviorally meaningful instruction. Can also inject a user-specified Korean rule as compact English. Overwrites originals after user approval.

## Activation

- Slash command: `/compress-rule [--apply] [--mode=rule|reference|plan] [--add-rule "<Korean rule>"] <path>`
- Natural language: "이 한글 rule 파일들 영어로 압축해줘", "compress these korean rules"
- Rule injection: "이 프로젝트의 rule에 md-en-kr을 이용해서 X라는 내용을 추가해줘"
- Targets: single `.md` file, glob (`rules/*.md`), or directory (recursive)

## Procedure

### 1. Argument parsing
- Extract from the invocation:
  - **file list** (single / glob / directory).
  - **`auto_apply`** (bool): true when the invocation contains `--apply`, a standalone `apply` token, or natural-language phrasing such as "승인 없이", "그냥 적용", "auto apply", "no prompt". Default false.
  - **`mode_override`**: one of `rule | reference | plan` if the user passes `--mode=X` or equivalent. If absent, mode is inferred per file (see §Mode Inference). The override applies to all files in the run.
  - **`additional_rules`** (list): Korean rule text from `--add-rule "<rule>"`, repeated `--add-rule` flags, or natural-language patterns like "X라는 내용을 추가", "X 라는 내용을 추가", "X rule을 추가", "X 규칙을 추가". Default empty.
- Project-rule aliases: if the target is omitted and the user says "this project rule", "프로젝트 rule", "프로젝트 룰", or "이 프로젝트의 rule", walk upward from the current working directory and resolve the file list to the nearest `AGENTS.md`, then `CLAUDE.md`, then `GEMINI.md`. If none exists, abort and ask for an explicit `.md` path.
- Single file: use as-is.
- Glob: expand via shell.
- Directory: collect all `*.md` recursively, excluding hidden directories (`.git`, `.venv`, `node_modules`, etc.).
- If the resolved list is empty, abort with a clear message.
- If the resolved list contains non-`.md` files, abort and list them. Only `.md` files are supported.
- If `additional_rules` is non-empty and a target file would not infer to `rule`, abort unless the user explicitly passes `--mode=rule`. Rule injection is only valid for rule-mode processing.
- File collection is glob-based; `.gitignore` and `.git/info/exclude` are NOT consulted. Files that are git-untracked or git-ignored ARE still processed. Note such files in the summary so the user knows they may not appear in `git status`.

### 2. Per-file processing (sequential)

For each file in the resolved list:

1. Read the original file. Determine `effective_mode`: `mode_override` if set, otherwise inferred per §Mode Inference.
2. Apply the compression rules in §Rules with mode-specific emphasis from §Mode-Specific Behavior to produce the English version.
3. If `additional_rules` is non-empty, convert each added Korean rule to a compact English rule and insert it per §Rule Injection.
4. Write the candidate output to a temporary path (e.g., `/tmp/<basename>.converted.md`).
5. Run the §Self-Verification script against the temporary path. On failure, regenerate (up to 3 attempts; abort that file on the third failure with the script's stderr).
6. Branch per §Diff Policy below.

### 3. Diff Policy

| Condition | Behavior |
|---|---|
| `auto_apply=true` | Skip diff entirely. Overwrite the original immediately on verifier pass. |
| `auto_apply=false`, batch size 1–3 | Show full unified diff per file; prompt `apply / skip / abort`. |
| `auto_apply=false`, batch size ≥4 | Show a summary table first (filename, mode, original→compressed bytes, ratio, +/- lines). Then prompt globally: `apply all / review individually / abort`. On `review individually`, fall back to the 1–3 path (full diff per file). |

In all modes, files that fail verification 3 times are left untouched and listed in the final summary.

### 4. Summary

Always print:
- Per file: applied / skipped / failed-verification, mode used, byte ratio (e.g., `42% of original`).
- Injected rule count per file when `additional_rules` is non-empty.
- Total: applied N, skipped M, failed K, aggregate byte ratio.
- Note any files that were git-ignored or git-untracked (visible to the run but not to `git status`).

## Rules

### Mode Inference

If `mode_override` is not provided, infer per file from its path/filename (case-insensitive):

| Match | Mode |
|---|---|
| Path or filename contains `rule`, `RULES`, `/rules/`, `CLAUDE.md`, `AGENTS.md`, `CONVENTIONS` | `rule` |
| Path or filename contains `plan`, `spec`, `TODO`, `tasks`, `roadmap`, `checklist` | `plan` |
| Anything else | `reference` |

When multiple patterns match, prefer `rule` over `plan` over `reference`.

### Mode-Specific Behavior

- **`rule`** — behavioral instructions are sacred. Preserve every MUST/NEVER/required-language rule verbatim. Strong wording (`MUST`, `NEVER`, `under no circumstances`) MUST stay strong. Trim only meta-prose around rules. **Target ratio: 60–85% of original.**
- **`reference`** — facts, definitions, structural descriptions can be deduplicated and condensed. Trim *narrative and examples only*. **NEVER drop named technical entities (controllers, models, libraries, services, handlers, packages, classes, modules referenced by name), counts/quantifiers (`(22)`, `30+`, `~180ms`, `5GB`), package purposes ("for S3 CDN upload"), subsystem roles, or comma-separated identifier lists.** A reference doc with low narrative density (directory trees, named-entity enumerations, count tables) typically compresses to 60–80%, not 40–70% — do NOT chase the lower bound by stripping facts. **Target ratio: 40–70% of original** (60–80% for fact-dense / structured-prose docs).
- **`plan`** — TODOs, checklists (`- [x]` / `- [ ]`), file paths, dates, owners, acceptance criteria are sacred. Prose around them can be heavily compressed; bullets ≪ paragraphs. **Target ratio: 30–50% of original.**

Targets are guidelines. **Meaning preservation always wins over hitting a ratio.** If hitting the target would lose a rule, fact, or named entity, miss the target.

### Structured-prose detection (reference mode)

A reference doc is **structured-prose** when it has:
- Zero or ≤2 `#`/`##` headings, AND
- Multiple comma-separated identifier enumerations (`A, B, C, D, E`), OR
- Frequent parenthetical counts (`(22)`, `(30+)`), OR
- Inline directory/file tree-like enumerations (`foo/bar.php, foo/baz.php, ...`)

In structured-prose mode:
- Treat every named identifier as preservation-critical (like inline-code).
- Treat every `(N)` / `(N+)` / `N+` quantifier as preservation-critical.
- Use the upper end of the ratio band (60–80%); never go below 60%.

### Rule Injection

When `additional_rules` is non-empty:
- Translate each added Korean rule into compact English with rule-mode strictness.
- Preserve mandatory force: "반드시", "해야 한다", "하지 말아줘/말아야 한다", "금지" map to `MUST`, `MUST NOT`, or `NEVER` as appropriate.
- Preserve all numeric limits, units, protocol terms, identifiers, trigger phrases, and quoted/backticked text exactly unless the quoted text is ordinary Korean prose.
- Prefer short bullets, e.g. "프로토콜의 key는 5글자를 넘기지 말아줘" -> `- Protocol keys MUST be <=5 chars.`
- Insert added rules under the most relevant existing rule section (`## Rules`, `# Rules`, `## Coding Conventions`, `## Instructions`, or equivalent). If no rule-like heading exists, append bullets to the end of the file.
- Do not add, remove, or rename headings solely for inserted rules; heading-level sequence must remain compatible with §Self-Verification.
- Do not deduplicate away an added rule unless an equivalent rule already exists with equal or stronger wording. If equivalent, keep the stronger existing wording and report `0 injected (already covered)`.

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
- **Korean trigger phrases referenced verbatim** — even if the source text shows them WITHOUT backticks. If the document says `사용자가 "X"라고 말하면` or otherwise references a Korean phrase as a literal trigger, keep that phrase in Korean unchanged in the output.
- **Numeric codes** — HTTP status codes, error codes, enum values, version numbers (`200`, `4xx`, `v1.2.3`).
- **Quantitative qualifiers** — counts and magnitudes attached to entities, regardless of mode: `(22)`, `(30+)`, `30+`, `~100ms`, `180초`, `5GB`. Drop these and the document becomes a vague approximation of itself.
- **Named technical entities** — controller / model / library / service / handler / package / class / module / function / table / column names referenced by name. Even in reference mode, do NOT replace `Auth, User, Mission, Payment, ...` with "various controllers" or `(22 controllers)` alone.
- **Enum / range values** — `[0, 100]`, `1..10`, `0..=255` and similar ranges.
- **SQL keywords and identifiers** — table, column, schema, database, view names; SQL keywords inside SQL contexts.
- **URLs** — `http://`, `https://`, `ftp://`, `ws://`, `wss://` and similar protocol-prefixed URLs.
- **Network identifiers** — IP addresses (IPv4, IPv6), hostnames, domain names, port numbers.
- **Diagram blocks** — Mermaid (` ```mermaid `), PlantUML, ASCII diagrams. Preserve content verbatim inside fenced blocks; do not translate diagram labels.
- **Checklist states and counts** — `- [x]` and `- [ ]` items; never collapse, reorder, or change checkmark state.

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
9. **Count quantifiers** — `(N)`, `(N+)`, and bare `N+` patterns from the original each appear in the output. Catches cases like `Src/Controller(22)` collapsing to `Src/Controller` during over-aggressive compression.

The script does NOT enforce: byte-ratio targets (those are mode-specific guidelines, not invariants), Korean-trigger-phrase-without-backticks preservation, URL preservation, IP/hostname preservation, named-technical-entity preservation, comma-list cardinality, or semantic correctness of `additional_rules`. The agent is responsible for honoring those §Rules manually.

If the script fails, regenerate (up to 3 attempts). On the 3rd failure, abort that file and surface the script's stderr to the user. Do not show a failing diff and do not auto-apply.

## Output writing

- Overwrite the original file with the compressed content on `apply`.
- Do not write any other file (no `.bak`, no sibling). The diff preview before `apply` is the user's last chance to back out.

## Out of Scope

- Reverse direction (English → Korean).
- Non-`.md` files.
- External LLM/API calls — the calling agent (Claude Code or Codex CLI) performs the conversion itself.

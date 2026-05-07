# md-en-kr (Codex CLI entry point)

This skill compresses Korean Markdown rule files into compact English to reduce token usage.

## How to use

When the user invokes `/compress-rule <path>` or asks to compress/translate Korean rule files, follow the procedure defined in `SKILL.md` exactly.

- Read `SKILL.md` in this directory before acting.
- Follow §Procedure step by step.
- Apply §Rules and §Self-Verification without modification.
- NEVER overwrite a file without showing the diff and getting `apply` from the user.

## Activation triggers

- `/compress-rule <path>`
- `/compress-rule <dir>`
- `/compress-rule "<glob>"`
- `/compress-rule --apply <path>` — skip per-file confirmation, auto-apply on verify pass
- `/compress-rule --mode=rule|reference|plan <path>` — override per-file mode inference
- Natural language: "한글 룰 압축", "rule 영어 변환", "compress korean rules", "승인 없이 적용"

## Modes (see SKILL.md §Mode-Specific Behavior for details)

- `rule` — behavioral rules sacred, target 60–85% of original.
- `reference` — facts/structure dedup-friendly, target 40–70%.
- `plan` — TODOs/checklists/paths sacred, target 30–50%.

If `--mode=X` is not provided, mode is inferred per file from path/filename.

---
name: compress-rule
description: Compress Korean rule/MD files into compact English (md-en-kr skill)
argument-hint: [--apply] [--mode=rule|reference|plan] <file | glob | directory>
---

Invoke the md-en-kr skill to compress the Korean Markdown rule file(s) at the path(s) below.

Read `SKILL.md` in this directory and follow its `## Procedure` exactly:

1. Argument parsing — resolve `$ARGUMENTS` into:
   - file list
   - `auto_apply` flag (`--apply` token enables it)
   - `mode_override` (one of `rule | reference | plan` from `--mode=X`; if absent, mode is inferred per file from path/filename via §Mode Inference).
2. Per-file processing — convert with mode-specific behavior, run `scripts/verify_md_conversion.py`, then apply per §Diff Policy:
   - 1–3 files (interactive): full diff each, prompt `apply / skip / abort`.
   - 4+ files (interactive): summary table first, then `apply all / review individually / abort`.
   - `--apply`: skip all diffs, auto-apply on verifier pass.
3. Summary — applied N, skipped M, failed K, mode used per file, byte ratios. Note any git-ignored/untracked files processed.

Apply `## Rules` and `## Self-Verification` from SKILL.md without modification.

Arguments: $ARGUMENTS

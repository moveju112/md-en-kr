---
name: compress-rule
description: Compress Korean rule/MD files into compact English (md-en-kr skill)
argument-hint: [--apply] <file | glob | directory>
---

Invoke the md-en-kr skill to compress the Korean Markdown rule file(s) at the path(s) below.

Read `SKILL.md` in this directory and follow its `## Procedure` exactly:

1. Argument parsing — resolve `$ARGUMENTS` into a file list and an `auto_apply` flag (`--apply` token enables it).
2. Per-file processing — convert, run `scripts/verify_md_conversion.py`, then either auto-apply or show diff and ask `apply / skip / abort`.
3. Summary — applied N, skipped M, length ratios.

Apply `## Rules` and `## Self-Verification` from SKILL.md without modification.

Arguments: $ARGUMENTS

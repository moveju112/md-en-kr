---
name: compress-rule
description: Compress Korean rule/MD files into compact English (md-en-kr skill)
argument-hint: <file | glob | directory>
---

Invoke the md-en-kr skill to compress the Korean Markdown rule file(s) at the path(s) below.

Read `SKILL.md` in this directory and follow its `## Procedure` exactly:

1. Argument parsing — resolve `$ARGUMENTS` into a concrete file list.
2. Pre-flight check — git clean state for every file (abort otherwise).
3. Per-file processing — convert, self-verify, show diff, ask `apply / skip / abort`.
4. Summary — applied N, skipped M, length ratios.

Apply `## Rules` and `## Self-Verification` from SKILL.md without modification.

Path(s): $ARGUMENTS

---
name: sample-rule
description: Sample Korean coding rules file used as a conversion verification fixture.
---

# Coding Rules

## Response Language
- Always respond in Korean.
- NEVER respond in English.

## Naming
- PHP/JS variables and functions: camelCase.
- Indentation: 4 spaces.
- Avoid abbreviations; use intention-revealing names.

## Safety
- NEVER use destructive commands like `git push --force`.
- On `/graphify`, run `~/.claude/skills/graphify/SKILL.md` first.

## Triggers
- When user says `일반 말투`, return to normal tone.

---
name: markdown-style
description: Markdown conventions for vault notes
globs: Vault/**/*.md
always_apply: false
---
# Markdown Style (vault notes)

- One `#` H1 per note matching its title; ATX headings only.
- YAML frontmatter at the top with at least `created`, `type`, `tags`.
- Link related notes with `[[wiki-links]]` (title only, no path).
- No trailing whitespace; end with a single newline.
- Keep `Context/` notes short — they are read every session.

---
trigger: glob
globs: "**/*.md"
---

# Documentation And Governance

- Les fichiers Markdown doivent renforcer la source de vérité du repo, pas la disperser.
- Les specs vont dans `docs/specs/`.
- Les décisions durables vont dans `docs/decisions/`.
- Les procédures répétables vont dans `.windsurf/workflows/`.
- Les expertises réutilisables vont dans `.windsurf/skills/`.
- Éviter de dupliquer dans plusieurs fichiers la même règle de gouvernance.
- Préférer des titres explicites, un périmètre clair et des listes courtes orientées action.
- Si une consigne doit être durable et partagée, la versionner dans `AGENTS.md` ou une `Rule` plutôt que de compter sur une mémoire implicite.

#!/usr/bin/env python3
"""
Setup script for Windsurf Starter Pack profile.
This script configures the project for a specific domain.
"""

import os
import sys
import shutil
from pathlib import Path

def setup_starter_pack():
    """Configure the starter pack for a specific domain."""
    
    print("=== Windsurf Starter Pack Setup ===\n")
    
    # Get project information
    project_name = input("Nom du projet: ").strip()
    domain = input("Domaine (ex: e-commerce, iot, data-science): ").strip()
    description = input("Description courte: ").strip()
    stack = input("Stack technique (ex: Python+React, Node.js, Java): ").strip()
    
    if not project_name or not domain:
        print("Erreur: Le nom du projet et le domaine sont requis.")
        return False
    
    print(f"\nConfiguration du projet '{project_name}' dans le domaine '{domain}'...")
    
    # Update README.md
    readme_path = Path("README.md")
    if readme_path.exists():
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace starter pack content with project-specific content
        content = content.replace(
            "# Windsurf Starter Pack",
            f"# {project_name}"
        )
        content = content.replace(
            "Base de projet réutilisable pour construire des applications propres et maintenables avec Cascade.",
            description
        )
        content = content.replace(
            "## Objectifs\n\n- Démarrer rapidement avec une gouvernance intégrée",
            f"## Objectifs\n\n- {description}"
        )
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("README.md mis à jour")
    
    # Update AGENTS.md
    agents_path = Path("AGENTS.md")
    if agents_path.exists():
        with open(agents_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update domain-specific content
        content = content.replace(
            "Ce dépôt sert à construire des projets propres et maintenables avec Cascade.",
            f"Ce dépôt sert à construire {project_name}, un projet {domain} avec Cascade."
        )
        content = content.replace(
            "Le domaine métier sera défini lors de l'initialisation du projet via `/bootstrap-project`.",
            f"Domaine: {domain}\nStack: {stack}\n\n## Capacités métier\n\nLes capacités métier spécifiques au domaine {domain} seront définies au fur et à mesure du développement."
        )
        
        with open(agents_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("AGENTS.md mis à jour")
    
    # Create domain-specific rule
    domain_rule_path = Path(".windsurf/rules") / f"{domain.lower().replace('-', '_')}-domain.md"
    if not domain_rule_path.exists():
        with open(domain_rule_path, 'w', encoding='utf-8') as f:
            f.write(f"""---
trigger: model_decision
description: Contraintes métier à appliquer quand une tâche touche le domaine {domain}.
---

# {domain.title()} Domain

- Construire des solutions robustes dans le domaine {domain}.
- Préférer les approches éprouvées du domaine.
- Les intégrations doivent respecter les standards du domaine {domain}.
- Toute nouvelle capacité métier doit avoir une seule source de vérité.
- Les données temporaires ou générées doivent rester dans `tmp/`, `reports/` ou `data/generated/`.
""")
        print(f"Règle métier créée: {domain_rule_path}")
    
    # Clean up starter pack files
    starter_files = [
        "README_STARTER_PACK.md",
        "AGENTS_STARTER_PACK.md",
        "scripts/setup-starter-pack.py"
    ]
    
    for file in starter_files:
        file_path = Path(file)
        if file_path.exists():
            file_path.unlink()
            print(f"Fichier temporaire supprimé: {file}")
    
    # Create initial decision
    decisions_dir = Path("docs/decisions")
    decisions_dir.mkdir(parents=True, exist_ok=True)
    
    decision_file = decisions_dir / "001-project-initialization.md"
    with open(decision_file, 'w', encoding='utf-8') as f:
        f.write(f"""# Project Initialization Decision

**Date**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
**Status**: Accepted

## Context

Initialisation du projet {project_name} depuis le Windsurf Starter Pack.

## Decision

Utiliser le starter pack Windsurf comme base pour le projet {project_name} dans le domaine {domain}.

## Rationale

- Gouvernance intégrée via AGENTS.md et .windsurf/
- Structure canonique éprouvée
- Workflows et skills réutilisables
- Adaptation rapide au domaine spécifique

## Consequences

- Structure de repo propre et maintenable
- Gouvernance Windsurf disponible immédiatement
- Règles métier spécifiques au domaine {domain}
- Base extensible pour l'équipe

## Next Steps

1. Définir les capacités métier spécifiques
2. Créer les premiers modules canoniques
3. Adapter les workflows si nécessaire
""")
    
    print(f"\n=== Configuration terminée ===")
    print(f"Projet '{project_name}' prêt dans le domaine '{domain}'")
    print(f"Decision documentée: {decision_file}")
    print("\nProchaines étapes:")
    print("1. Exécuter /repo-hygiene pour valider la structure")
    print("2. Commencer le développement avec /task-intake")
    
    return True

if __name__ == "__main__":
    if setup_starter_pack():
        sys.exit(0)
    else:
        sys.exit(1)

#!/usr/bin/env python3
"""
Script de scan automatique pour détecter les données sensibles dans le dépôt.
À utiliser avant chaque commit ou dans le CI/CD.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Patterns à détecter (uniquement les critiques)
PATTERNS = {
    "JWT_TOKEN": r'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}',
    "API_KEY_OPENAI": r'sk-[a-zA-Z0-9]{20,}',
    "API_KEY_ANTHROPIC": r'sk-ant-[a-zA-Z0-9_-]{20,}',
    "PRIVATE_KEY": r'-----BEGIN (RSA )?PRIVATE KEY-----',
    "INTERNAL_URL": r'https?://[a-z0-9-]+\.int\.cubixmedia\.fr',
}

# Fichiers/dossiers à ignorer
IGNORE_DIRS = {
    '.git',
    '.venv',
    '__pycache__',
    'venv',
    'env',
    '.idea',
    'node_modules',
    'dist',
    'build',
    '.pytest_cache',
    'tmp',
    'docs/temp',
    'scraper_env',
    'recipe_env',
}

# Extensions à scanner
SCAN_EXTENSIONS = {
    '.py', '.js', '.ts', '.json', '.yml', '.yaml', '.md', '.txt', '.sh', '.env', '.ini'
}


def scan_file(file_path: Path) -> List[Tuple[str, int, str]]:
    """Scan un fichier pour détecter les patterns sensibles."""
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return findings
    
    for pattern_name, pattern in PATTERNS.items():
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[:match.start()].count('\n') + 1
            line_content = content.split('\n')[line_num - 1].strip()
            
            # Ignorer les patterns de template/commentaire
            if any(marker in line_content.lower() for marker in ['your-', 'example', 'placeholder', 'template', 'sample', 'changeme']):
                continue
            
            # Masquer la valeur sensible
            masked_value = mask_sensitive(match.group(), pattern_name)
            findings.append((pattern_name, line_num, masked_value))
    
    return findings


def mask_sensitive(value: str, pattern_name: str) -> str:
    """Masquer une valeur sensible pour l'affichage."""
    if len(value) <= 10:
        return f"{value[:2]}***{value[-2:]}" if len(value) > 4 else "***"
    return f"{value[:8]}...{value[-4:]}"


def scan_directory(root_dir: Path) -> dict:
    """Scanner récursivement un répertoire."""
    all_findings = {}
    
    for file_path in root_dir.rglob('*'):
        # Ignorer les dossiers
        if any(part in IGNORE_DIRS for part in file_path.parts):
            continue
        
        # Ignorer les fichiers qui ne sont pas dans les extensions à scanner
        if file_path.suffix not in SCAN_EXTENSIONS:
            continue
        
        # Ignorer les fichiers .template
        if 'template' in file_path.name.lower():
            continue
        
        findings = scan_file(file_path)
        if findings:
            all_findings[str(file_path.relative_to(root_dir))] = findings
    
    return all_findings


def main():
    """Fonction principale."""
    root_dir = Path(__file__).parent.parent
    
    print(f"🔍 Scan du dépôt : {root_dir}")
    print("=" * 60)
    
    findings = scan_directory(root_dir)
    
    if not findings:
        print("✅ Aucune donnée sensible détectée !")
        return 0
    
    print(f"⚠️  Données sensibles détectées dans {len(findings)} fichiers :\n")
    
    total_issues = 0
    for file_path, issues in findings.items():
        print(f"📄 {file_path}")
        for pattern_name, line_num, masked_value in issues:
            print(f"   ❌ {pattern_name} (ligne {line_num}): {masked_value}")
            total_issues += 1
        print()
    
    print("=" * 60)
    print(f"Total : {total_issues} problème(s) détecté(s)")
    print("\n🔧 Actions recommandées :")
    print("1. Remplacer les valeurs sensibles par des variables d'environnement")
    print("2. Utiliser des fichiers .env.template pour les exemples")
    print("3. Ne jamais commiter de vrais tokens ou clés API")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())

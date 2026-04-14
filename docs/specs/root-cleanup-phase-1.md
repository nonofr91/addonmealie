# Root Cleanup Phase 1

## Objectif

Réduire la dette historique à la racine du repo sans casser les flux encore potentiellement utilisés.

## Constat

La racine contient plusieurs familles de fichiers incompatibles avec la gouvernance actuelle :

- variantes `final_*`, `debug_*`, `fixed_*`, `definitive_*`
- multiples configurations MCP concurrentes
- scripts historiques concurrents autour de `mealie_mcp_*`
- fichiers contenant des secrets hardcodés

## Stratégie retenue

Le nettoyage se fait par lots :

1. sécurisation de la configuration
2. réduction de la pollution visible
3. consolidation vers une source de vérité unique

## Lot 1

### Fait

- ajout d'un `.env.template` racine pour rendre explicite la configuration attendue du repo

### À traiter ensuite

- identifier la configuration MCP canonique
- retirer les secrets des fichiers racine encore sensibles
- reclasser ou supprimer les configurations MCP obsolètes

## Critères de réussite

- plus aucun secret versionné dans les points d'entrée actifs
- une seule configuration MCP canonique documentée
- disparition progressive des variantes historiques à la racine

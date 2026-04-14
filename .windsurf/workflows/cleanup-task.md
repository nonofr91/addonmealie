---
description: Nettoyer les fichiers temporaires, artefacts et sorties parasites après une tâche
---

# Workflow Cleanup Task

Utilise ce workflow avant de conclure une tâche pour éviter la pollution du projet.

## Étapes

1. Relever les fichiers créés ou modifiés pendant la tâche.
2. Vérifier si un fichier temporaire ou exploratoire a été laissé au mauvais endroit.
3. Déplacer les sorties générées dans `reports/` ou `data/generated/` si elles doivent être conservées.
4. Supprimer les fichiers temporaires inutiles.
5. Vérifier qu'aucun fichier métier nouveau n'a été laissé à la racine.
6. Vérifier que la doc ou la spec a été mise à jour si le changement modifie la gouvernance ou l'architecture.

## Check final

- pas de fichier parasite
- pas de duplication métier
- pas de secret dans le code
- pas de nom de fichier interdit

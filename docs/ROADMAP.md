# Roadmap - Mealie Addons Platform

## Vision

Devenir l'assistant intelligent ultime pour les corvées culinaires en automatisant l'ensemble du cycle de gestion alimentaire : de l'import de recettes à la livraison de courses, en passant par la planification nutritionnelle, le budget et l'optimisation du temps de cuisine.

Le projet vise à créer une suite d'addons externes pour Mealie qui :
- **Ne modifient jamais l'image Mealie**
- **Sont déployés comme services Docker indépendants**
- **Communiquent via API publiques et MCP**
- **Sont maintenables et extensibles par la communauté**

## Fonctionnalités actuelles

### ✅ Import de recettes intelligent (mealie-import-orchestrator)
- Scraping de sites de cuisine (Marmiton, 750g, etc.)
- Structuration automatique des recettes
- Audit de qualité (images manquantes, tags de test, doublons probables)
- Auto-fix (images de fallback, nettoyage des tags)
- Intégration avec TheMealDB pour les images
- Support IA optionnel (OpenAI/Anthropic/Mistral)
- Web UI Streamlit + REST API FastAPI

### ✅ Calcul nutritionnel (mealie-nutrition-advisor)
- Calcul automatique des valeurs nutritionnelles (kcal, protéines, lipides, glucides, fibres)
- Enrichissement des recettes existantes
- Sources multiples : Open Food Facts + IA + cache local
- Profils avancés du foyer (âge, poids, activité, objectifs)
- Gestion des pathologies médicales (diabète, hypertension, insuffisance rénale, goutte, reflux)
- Ajustement automatique des cibles selon les pathologies
- Planification de menus hebdomadaires
- Gestion des absences (pattern de présence hebdomadaire)
- Intégration avec le planning natif Mealie

### ✅ Intégration MCP (mealie-mcp-server)
- 45 outils API couvrant l'intégralité de l'API Mealie
- Gestion des recettes (CRUD, duplication, images, assets)
- Listes de courses (CRUD, opérations bulk, intégration recettes)
- Organisation (catégories, tags, filtrage avancé)
- Planning de repas (consultation, création bulk)
- Compatible avec Claude Desktop et autres clients MCP

## Perspectives futures

### 🔄 Court terme (3-6 mois)

#### Optimisation des listes de courses
- Regroupement intelligent des ingrédients (même ingrédient, différentes unités)
- Détection des achats en vrac vs individuels
- Suggestions de substitutions pour les ingrédients manquants
- Historique des achats par ingrédient

#### Budget alimentaire
- Coût estimé par recette (basé sur les prix des ingrédients)
- Suivi des dépenses réelles vs budget
- Alertes de dépassement de budget
- Recommandations de recettes économiques

#### Gestion du temps de cuisine
- Estimation du temps de préparation par recette
- Planning optimisé du temps de cuisine (recettes parallèles)
- Suggestions de recettes rapides selon le temps disponible
- Suivi du temps réel de cuisine

#### Interface livraison
- Intégration avec services de livraison (drive, courses en ligne)
- Génération automatique de commandes à partir des listes
- Comparaison de prix entre fournisseurs
- Suivi des livraisons

### 💡 Moyen terme (6-12 mois)

#### Coaching nutritionnel personnalisé
- Analyse des habitudes alimentaires
- Recommandations basées sur les objectifs de santé
- Suivi de l'apport nutritionnel sur le temps
- Alertes en cas de déséquilibre nutritionnel

#### Recommandations basées sur les préférences
- Système de recommandation collaborative
- Apprentissage des préférences utilisateur
- Suggestions de recettes personnalisées
- Filtrage par goûts, allergies, restrictions

#### Analyse des habitudes alimentaires
- Tableaux de bord de consommation
- Tendances alimentaires mensuelles
- Détection des patterns de consommation
- Rapports de nutrition hebdomadaires

#### Intégration avec autres services
- Fitness (sync avec apps d'exercice)
- Santé (intégration avec Apple Health, Google Fit)
- Finance (catégorisation des dépenses alimentaires)
- Smart home (intégration avec frigo intelligent)

### 🚀 Long terme (12+ mois)

#### Intelligence artificielle avancée
- Génération de recettes personnalisées
- Substitution intelligente d'ingrédients
- Optimisation multi-objective (coût, temps, nutrition)
- Prédiction des préférences utilisateur

#### Écosystème d'addons
- Marketplace d'addons communautaires
- SDK pour créer des addons personnalisés
- Templates d'addons réutilisables
- Documentation complète pour développeurs

#### Mobile et IoT
- Application mobile native
- Intégration avec assistants vocaux
- Notifications intelligentes (courses à faire, repas à planifier)
- Wearables (suivi nutritionnel en temps réel)

## Appel à contributions

Ce projet est ouvert à toutes les contributions ! Voici comment vous pouvez participer :

### Pour les développeurs
- Forker le dépôt et proposer des Pull Requests
- Implémenter des fonctionnalités de la roadmap
- Corriger des bugs et améliorer la documentation
- Créer de nouveaux addons

### Pour les utilisateurs
- Signaler des bugs via GitHub Issues
- Proposer des nouvelles fonctionnalités
- Tester les versions de développement
- Partager vos retours d'expérience

### Pour les designers
- Améliorer l'UI/UX des addons
- Créer des templates de design
- Proposer des améliorations d'accessibilité

### Pour les rédacteurs
- Améliorer la documentation
- Traduire les docs dans d'autres langues
- Créer des tutoriels et guides

## Principes de développement

- **Architecture modulaire** : chaque addon a une responsabilité claire
- **API d'abord** : toutes les fonctionnalités exposées via API REST
- **Docker natif** : déploiement simple et reproductible
- **Documentation continue** : docs à jour avec le code
- **Tests automatiques** : couverture minimale de 70%
- **Code review obligatoire** : qualité avant quantité

## Discussion et feedback

Rejoignez la discussion sur :
- GitHub Issues : bugs et questions techniques
- GitHub Discussions : idées et feedback général
- Email : pour les questions sensibles ou privées

---

Cette roadmap est évolutive et s'adaptera aux besoins de la communauté. N'hésitez pas à proposer des idées ou modifications !

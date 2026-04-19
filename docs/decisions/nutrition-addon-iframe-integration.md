# Intégration iframe dans Mealie - Analyse technique

## Question

Est-il possible d'intégrer l'UI de l'addon mealie-nutrition-advisor via iframe dans l'interface Mealie ?

## Résultats de recherche

### Mealie peut être intégré dans des iframes externes

**Oui** - Mealie peut être intégré DANS des iframes d'autres applications :

- **Home Assistant** : Plusieurs exemples d'intégration de Mealie dans des iframes HA
- **Issue #5690** : Problème de login iframe corrigé (juillet 2025)
- **Issue #6368** : Mealie fonctionne dans iframe HA après correction #5690 (octobre 2025)

### Mais l'inverse n'est pas documenté

**Non documenté** - Intégration d'iframes externes DANS l'interface Mealie :

- Aucune documentation officielle sur l'intégration d'iframes externes dans Mealie
- Pas de système de pages personnalisées ou de dashboard modifiable
- Les résultats de recherche ne mentionnent pas cette capacité

### Fonctionnalités existantes Mealie

- **API REST** : Pour intégrations externes
- **Vidéo embed** : Supporte l'intégration de vidéos (YouTube, etc.) dans les recettes
- **Actions de recette** : Liens externes mais pas d'embed
- **Pas de système de pages personnalisées** : Mealie n'a pas de mécanisme pour ajouter des pages/sections personnalisées

## Conclusion

**L'intégration iframe DANS Mealie n'est pas supportée nativement.**

Mealie peut être intégré DANS des iframes d'autres applications (Home Assistant, etc.), mais l'inverse (intégrer une iframe externe DANS l'interface Mealie) n'est pas documenté ni supporté.

## Alternatives recommandées

1. **Lien externe** : Ajouter un lien dans l'interface Mealie vers l'UI de l'addon
2. **API REST** : Utiliser l'API de l'addon pour créer une intégration directe dans Mealie (si Mealie supporte les plugins)
3. **UI autonome** : Garder l'UI Streamlit comme interface séparée, accessible via lien

## Recommandation

Conserver l'UI Streamlit comme interface autonome, accessible via :
- Lien depuis l'interface Mealie (si possible via configuration)
- URL directe configurée dans docker-compose
- Intégration dans Home Assistant (si utilisé)

L'intégration iframe directe DANS Mealie n'est pas une option viable à court terme sans modification de l'image Mealie, ce qui contrevient aux règles de gouvernance du projet.

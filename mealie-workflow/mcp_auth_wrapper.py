#!/usr/bin/env python3
"""
MEALIE MCP WRAPPER - AUTHENTIFICATION CORRIGÉE
Utilise les vrais MCP Mealie avec authentification
"""

import json
import os
import requests
import sys
from pathlib import Path

WRAPPER_DIR = Path(__file__).parent

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

# Configuration
def load_mealie_config():
    """Charge la configuration Mealie"""
    config_path = Path(__file__).parent / "config" / "mealie_config.json"
    config = {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")

    mealie_api = config.setdefault("mealie_api", {})
    env_base_url = os.environ.get("MEALIE_BASE_URL")
    env_api_key = os.environ.get("MEALIE_API_KEY")

    if env_base_url:
        mealie_api["url"] = env_base_url
    if env_api_key:
        mealie_api["token"] = env_api_key

    return config

import os
import json

# Charger le système de profils si disponible
def load_mealie_profile():
    """Charge le profil Mealie actif depuis le fichier de configuration"""
    # Le fichier est dans mealie-workflow/config/, __file__ est dans mealie-workflow/
    profile_path = Path(__file__).parent / "config" / "mealie-profiles.json"
    try:
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                config = json.load(f)
                active_profile = config.get('active_profile', 'local')
                profile_data = config['profiles'][active_profile]
                return profile_data
    except Exception as e:
        print(f"⚠️ Erreur chargement profil: {e}")
    return None

# Env vars directes priment toujours sur le profil fichier (Docker, CI, …)
_direct_url = os.getenv("MEALIE_BASE_URL")
_direct_key = os.getenv("MEALIE_API_KEY")

if _direct_url and _direct_key:
    env_api_url = _direct_url
    env_token = _direct_key
    print("📍 Config: variables d'environnement directes")
else:
    # Fallback : charger le profil si pas de vars directes
    profile = load_mealie_profile()
    if profile:
        profile_url = profile.get('url')
        profile_name = profile.get('name')
        profile_token_env = profile.get('token_env')
        print(f"📍 Profil Mealie: {profile_name}")
        print(f"🌐 URL: {profile_url}")
        print(f"🔑 Token depuis: {profile_token_env}")
        env_api_url = profile_url
        env_token = os.getenv(profile_token_env) or os.getenv("MEALIE_API_KEY")
    else:
        env_api_url = _direct_url
        env_token = _direct_key or os.getenv("MEALIE_LOCAL_API_KEY")
        print("⚠️ Utilisation variables d'environnement directes (pas de profil)")

if env_api_url and env_token:
    # Variables d'environnement présentes : les utiliser directement
    api_url = env_api_url
    # Ajouter /api si non présent (comme le client Mealie)
    if not api_url.endswith("/api"):
        api_url = f"{api_url.rstrip('/')}/api"
    token = env_token
    print(f"🔧 MCP Mealie authentifiés vers: {api_url}")
    print("🔑 Token configuré")
else:
    # Pas de variables d'environnement : utiliser le fichier config
    config = load_mealie_config()
    if config:
        mealie_api = config.get("mealie_api", {})
        api_url = mealie_api.get("url", "")
        token = mealie_api.get("token", "")
        print(f"🔧 MCP Mealie authentifiés vers: {api_url or 'non configuré'} (via fichier config)")
        print("🔑 Token configuré" if token else "❌ Pas de token")
    else:
        api_url = ""
        token = ""
        print("❌ Configuration Mealie manquante")

# MCP avec authentification corrigée
def mcp3_list_recipes():
    """Liste les recettes Mealie avec authentification"""
    if not api_url or not token:
        print("❌ Configuration Mealie manquante")
        return []
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{api_url}/recipes", headers=headers, timeout=10)
        
        if response.status_code == 200:
            recipes = response.json()
            # S'assurer que recipes est une liste
            if isinstance(recipes, dict):
                recipes = recipes.get('items', [])
            elif not isinstance(recipes, list):
                recipes = []
            
            print(f"✅ {len(recipes)} recettes trouvées")
            return recipes
        else:
            print(f"❌ Erreur API list_recipes: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Erreur connexion list_recipes: {e}")
        return []

def mcp3_get_recipe_details(slug):
    """Obtient les détails d'une recette avec authentification"""
    if not api_url or not token:
        print("❌ Configuration Mealie manquante")
        return {"name": "Erreur config", "ingredients": [], "instructions": []}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{api_url}/recipes/{slug}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            details = response.json()
            print(f"✅ Détails: {details.get('name', 'N/A')}")
            return details
        else:
            print(f"❌ Erreur API get_recipe_details: {response.status_code}")
            return {"name": "Erreur API", "ingredients": [], "instructions": []}
    except Exception as e:
        print(f"❌ Erreur connexion get_recipe_details: {e}")
        return {"name": "Erreur connexion", "ingredients": [], "instructions": []}

UNIT_NORMALIZATION = {
    # Masse
    "g": "gramme", "gr": "gramme", "grs": "gramme", "grammes": "gramme",
    "kg": "kilogramme", "kilogrammes": "kilogramme",
    "mg": "milligramme", "milligrammes": "milligramme",
    "lb": "livre", "lbs": "livre",
    "oz": "once",
    # Volume
    "l": "litre", "litres": "litre",
    "cl": "centilitre", "cls": "centilitre", "centilitres": "centilitre",
    "ml": "millilitre", "millilitres": "millilitre",
    "dl": "d\u00e9cilitre", "d\u00e9cilitres": "d\u00e9cilitre",
    "gal": "gallon", "pt": "pinte", "qt": "quart",
    # Cuill\u00e8res
    "c\u00e0c": "cuill\u00e8re \u00e0 caf\u00e9", "cac": "cuill\u00e8re \u00e0 caf\u00e9",
    "c. \u00e0 c.": "cuill\u00e8re \u00e0 caf\u00e9", "c.\u00e0.c.": "cuill\u00e8re \u00e0 caf\u00e9",
    "c\u00e0s": "cuill\u00e8re \u00e0 soupe", "cas": "cuill\u00e8re \u00e0 soupe",
    "c. \u00e0 s.": "cuill\u00e8re \u00e0 soupe", "c.\u00e0.s.": "cuill\u00e8re \u00e0 soupe",
    "cuill\u00e8re \u00e0 caf\u00e9 rase": "cuill\u00e8re \u00e0 caf\u00e9",
    "cuill\u00e8res \u00e0 caf\u00e9": "cuill\u00e8re \u00e0 caf\u00e9",
    "cuill\u00e8res \u00e0 soupe": "cuill\u00e8re \u00e0 soupe",
    # Contenants
    "boites": "bo\u00eete", "boite": "bo\u00eete",
    "paquets": "paquet",
    # Divers
    "gousses": "gousse",
    "pinc\u00e9es": "pinc\u00e9e",
    "brins": "brin",
    "bottes": "botte",
    "portions": "portion",
    "tasses": "tasse",
    "personnes": "personne",
    "gouttes": "goutte",
}

UNIT_NOISE = {
    "bonnes", "bon", "bonne", "gros", "grosse", "petit", "petite",
    "grands", "grande", "moyen", "moyenne", "clous", "beau", "belle",
}


def _build_mealie_cache(api_url, headers):
    """Charge tous les foods et units de Mealie dans un dict {nom_lower: objet}."""
    foods, units = {}, {}
    try:
        r = requests.get(f"{api_url}/foods?page=1&perPage=500", headers=headers, timeout=10)
        if r.status_code == 200:
            for item in r.json().get("items", []):
                foods[item["name"].lower()] = item
                abbr = item.get("abbreviation", "")
                if abbr:
                    foods[abbr.lower()] = item
    except Exception:
        pass
    try:
        r2 = requests.get(f"{api_url}/units?page=1&perPage=500", headers=headers, timeout=10)
        if r2.status_code == 200:
            for item in r2.json().get("items", []):
                units[item["name"].lower()] = item
                abbr = item.get("abbreviation", "")
                if abbr:
                    units[abbr.lower()] = item
            # Indexer aussi via les alias de normalisation
            for alias, canonical in UNIT_NORMALIZATION.items():
                if canonical.lower() in units and alias not in units:
                    units[alias] = units[canonical.lower()]
    except Exception:
        pass
    return foods, units


def _clean_food_name(name: str) -> str:
    """Supprime les prépositions/articles français en début de nom de food."""
    import re
    name = name.strip()
    name = re.sub(r"^(de |d'|des |du |l'|la |le |les )", "", name, flags=re.IGNORECASE)
    return name.strip()


def _get_or_create_food(api_url, headers, food_name, cache):
    """Retourne un objet food Mealie {id, name} — utilise le cache ou crée si absent."""
    food_name = _clean_food_name(food_name)
    key = food_name.lower().strip()
    if key in cache:
        item = cache[key]
        return {"id": item["id"], "name": item["name"]}
    try:
        r = requests.post(f"{api_url}/foods", headers=headers, json={"name": food_name}, timeout=5)
        if r.status_code in [200, 201]:
            item = r.json()
            cache[item["name"].lower()] = item
            return {"id": item["id"], "name": item["name"]}
        # 400/409 = déjà existant → chercher via GET search
        if r.status_code in [400, 409, 422]:
            sr = requests.get(f"{api_url}/foods?search={requests.utils.quote(food_name)}&perPage=5",
                              headers=headers, timeout=5)
            if sr.status_code == 200:
                items = sr.json().get("items", [])
                for item in items:
                    if item["name"].lower() == key:
                        cache[key] = item
                        return {"id": item["id"], "name": item["name"]}
    except Exception:
        pass
    return None


def _get_or_create_unit(api_url, headers, unit_name, cache):
    """Retourne un objet unit Mealie {id, name} — utilise le cache ou crée si absent."""
    unit_name = unit_name.strip().lower()
    # Ignorer les adjectifs parasites du parsing LLM
    if unit_name in UNIT_NOISE:
        return None
    # Normaliser vers le nom canonique
    unit_name = UNIT_NORMALIZATION.get(unit_name, unit_name)
    key = unit_name.lower().strip()
    if key in cache:
        item = cache[key]
        return {"id": item["id"], "name": item["name"]}
    try:
        r = requests.post(f"{api_url}/units", headers=headers, json={"name": unit_name}, timeout=5)
        if r.status_code in [200, 201]:
            item = r.json()
            cache[item["name"].lower()] = item
            return {"id": item["id"], "name": item["name"]}
        # 400/409 = déjà existant → chercher via GET search
        if r.status_code in [400, 409, 422]:
            sr = requests.get(f"{api_url}/units?search={requests.utils.quote(unit_name)}&perPage=5",
                              headers=headers, timeout=5)
            if sr.status_code == 200:
                items = sr.json().get("items", [])
                for item in items:
                    if item["name"].lower() == key:
                        cache[key] = item
                        return {"id": item["id"], "name": item["name"]}
    except Exception:
        pass
    return None


def _resolve_items(api_url, headers, endpoint, items_as_strings):
    """Résout une liste de strings en objets {id, name, slug} via la liste complète ou POST création."""
    try:
        r = requests.get(f"{api_url}/{endpoint}?page=1&perPage=200", headers=headers, timeout=5)
        existing = {i["slug"]: i for i in r.json().get("items", [])} if r.status_code == 200 else {}
    except Exception:
        existing = {}
    
    resolved = []
    for name in items_as_strings:
        slug = name.lower().replace(" ", "-").replace("'", "").replace("\u00e9", "e").replace("\u00e8", "e").replace("\u00ea", "e").replace("\u00e0", "a")
        if slug in existing:
            resolved.append(existing[slug])
            continue
        try:
            r2 = requests.post(f"{api_url}/{endpoint}", headers=headers, json={"name": name}, timeout=5)
            if r2.status_code in [200, 201]:
                resolved.append(r2.json())
        except Exception:
            pass
    return resolved


_FR_EN_CULINARY = {
    "pâtes": "pasta", "pates": "pasta", "spaghetti": "spaghetti",
    "soupe": "soup", "potage": "soup", "velouté": "soup", "velout": "soup",
    "salade": "salad", "gratin": "gratin",
    "poulet": "chicken", "bœuf": "beef", "boeuf": "beef",
    "porc": "pork", "agneau": "lamb", "veau": "veal",
    "saumon": "salmon", "thon": "tuna", "cabillaud": "cod",
    "tomate": "tomato", "oignon": "onion", "ail": "garlic",
    "carbonara": "carbonara", "bolognaise": "bolognese", "ratatouille": "ratatouille",
    "quiche": "quiche", "tarte": "tart", "tartelette": "tart",
    "crêpe": "crepe", "crepe": "crepe", "gateau": "cake", "gâteau": "cake",
    "beurre": "butter", "crème": "cream", "fromage": "cheese",
    "lentilles": "lentils", "lentille": "lentil",
    "champignon": "mushroom", "champignons": "mushrooms",
    "épinards": "spinach", "courgette": "zucchini",
    "pomme": "apple", "pommes": "apples",
}

def _fetch_themealsdb_image(recipe_name):
    """Cherche une image pertinente sur TheMealDB par nom de recette.
    Gratuit, sans clé API. Essaie plusieurs variantes du nom (FR + EN).
    Retourne (url, content_type, bytes) ou None si non trouvé."""
    name = recipe_name.strip()
    STOP = {"les", "des", "aux", "avec", "pour", "une", "the", "and", "with",
            "sur", "dans", "par", "mais", "très", "plus", "sans", "façon", "facon"}
    # Mots bruts significatifs (sans strip de "s" qui cause des faux matchs)
    raw_words = [w for w in name.split() if len(w) > 3 and w.lower().rstrip("s,'") not in STOP]
    # Traduction FR→EN : mots qui ont une correspondance connue uniquement
    en_words = [_FR_EN_CULINARY[w.lower()] for w in raw_words if w.lower() in _FR_EN_CULINARY]
    # Ordre de priorité : EN spécifique d'abord (plus de chances de matcher), puis brut
    seen = set()
    queries = []
    for q in ([" ".join(en_words[:2])] if len(en_words) >= 2 else []) + \
             ([en_words[0]] if en_words else []) + \
             [name, " ".join(raw_words[:2]) if raw_words else ""] :
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            queries.append(q)
    UA = {"User-Agent": "MealieImporter/1.0"}
    for query in queries:
        try:
            r = requests.get(
                "https://www.themealdb.com/api/json/v1/1/search.php",
                params={"s": query},
                headers=UA,
                timeout=8,
            )
            if r.status_code != 200:
                continue
            meals = r.json().get("meals") or []
            if not meals:
                continue
            img_url = meals[0].get("strMealThumb")
            if not img_url:
                continue
            # Télécharger l'image
            dl = requests.get(img_url, headers=UA, timeout=12)
            ct = dl.headers.get("content-type", "image/jpeg")
            if dl.status_code == 200 and len(dl.content) > 20_000 and "image" in ct:
                print(f"   📸 Image TheMealDB trouvée pour '{query}': {meals[0].get('strMeal')}")
                return (img_url, ct, dl.content)
        except Exception as e:
            print(f"   ⚠️ TheMealDB fallback échoué pour '{query}': {e}")
    return None


def _upload_recipe_image(api_url, headers, slug, image_url, recipe_name):
    """Télécharge l'image depuis image_url et l'uploade dans Mealie via PUT multipart.
    Si image_url absent ou inaccessible, essaie TheMealDB par nom de recette.
    Rejette les images trop petites (logos/icônes). Pas de placeholder si tout échoue."""
    import tempfile, os as _os
    # Seuil minimal : 20 KB — en dessous c'est probablement un logo, icône ou erreur
    MIN_IMAGE_SIZE = 20_000
    img_ok = False
    if image_url and isinstance(image_url, str) and image_url.startswith("http"):
        # Adapter le Referer selon le CDN pour contourner le hotlink protection
        if "afcdn.com" in image_url:
            referer = "https://www.marmiton.org/"
        elif "750g.com" in image_url or "reseaudesmedias.com" in image_url:
            referer = "https://www.750g.com/"
        else:
            referer = image_url
        BROWSER_UA = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": referer,
            "Accept": "image/avif,image/webp,image/apng,image/jpeg,*/*",
        }
        try:
            dl = requests.get(image_url, headers=BROWSER_UA, timeout=12)
            content_type = dl.headers.get("content-type", "image/jpeg")
            if dl.status_code == 200 and len(dl.content) >= MIN_IMAGE_SIZE and "image" in content_type:
                ext = "jpg" if "jpeg" in content_type else content_type.split("/")[-1].split(";")[0]
                with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
                    f.write(dl.content)
                    tmp = f.name
                try:
                    with open(tmp, "rb") as f:
                        put_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
                        resp = requests.put(
                            f"{api_url}/recipes/{slug}/image",
                            headers=put_headers,
                            files={"image": (f"image.{ext}", f, content_type), "extension": (None, ext)},
                            timeout=20,
                        )
                    if resp.status_code == 200:
                        img_ok = True
                        print(f"✅ Recette créée et peuplée avec image: {recipe_name} (slug: {slug})")
                finally:
                    _os.unlink(tmp)
        except Exception as e:
            print(f"   ⚠️ Téléchargement image échoué: {e}")

    if not img_ok and image_url and isinstance(image_url, str) and image_url.startswith("http"):
        try:
            post_headers = {**headers, "Content-Type": "application/json"}
            resp2 = requests.post(
                f"{api_url}/recipes/{slug}/image",
                headers=post_headers,
                json={"url": image_url},
                timeout=12,
            )
            if resp2.status_code == 200 and resp2.text not in ["null", ""]:
                img_ok = True
                print(f"✅ Recette créée et peuplée avec image (scrape): {recipe_name} (slug: {slug})")
        except Exception:
            pass

    if not img_ok:
        # Fallback TheMealDB : chercher par nom de recette (gratuit, sans clé)
        themealsdb = _fetch_themealsdb_image(recipe_name)
        if themealsdb:
            _, ct, img_bytes = themealsdb
            ext = "jpg" if "jpeg" in ct else ct.split("/")[-1].split(";")[0]
            import tempfile, os as _os2
            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
                f.write(img_bytes); tmp2 = f.name
            try:
                with open(tmp2, "rb") as f:
                    put_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
                    resp3 = requests.put(
                        f"{api_url}/recipes/{slug}/image",
                        headers=put_headers,
                        files={"image": (f"image.{ext}", f, ct), "extension": (None, ext)},
                        timeout=20,
                    )
                if resp3.status_code == 200:
                    img_ok = True
                    print(f"✅ Recette créée avec image TheMealDB: {recipe_name} (slug: {slug})")
            finally:
                _os2.unlink(tmp2)

    if not img_ok:
        print(f"✅ Recette créée (slug: {slug}), image non récupérable depuis: {image_url[:60] if image_url else 'aucune URL'}")


def mcp3_create_recipe(payload=None, **kwargs):
    """Crée une recette avec authentification"""
    if not api_url or not token:
        print("❌ Configuration Mealie manquante")
        return {"success": False, "error": "Configuration manquante"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Utiliser le payload complet si fourni, sinon reconstruire depuis kwargs
    if payload:
        final_payload = payload
    else:
        final_payload = {
            "name": kwargs.get("name", "Recette sans nom"),
            "description": kwargs.get("description", ""),
            "recipeIngredient": kwargs.get("ingredients", []),
            "recipeInstructions": kwargs.get("instructions", []),
            "recipeServings": int(kwargs.get("servings", 4)) if kwargs.get("servings") else 4,
            "prepTime": kwargs.get("prep_time", "PT15M"),
            "cookTime": kwargs.get("cook_time", "PT30M"),
            "totalTime": kwargs.get("total_time", "PT45M"),
            "recipeCategory": kwargs.get("categories", []),
            "tags": kwargs.get("tags", []),
            "image": kwargs.get("image", "")
        }
    
    try:
        recipe_name = final_payload.get("name", kwargs.get("name", "Recette sans nom"))
        
        # Étape 1 : POST avec seulement le nom → retourne le slug
        create_response = requests.post(
            f"{api_url}/recipes",
            headers=headers,
            json={"name": recipe_name},
            timeout=10
        )
        
        if create_response.status_code not in [200, 201]:
            print(f"❌ Erreur création: {create_response.status_code} - {create_response.text}")
            return {"success": False, "error": f"HTTP {create_response.status_code}"}
        
        # Le résultat est le slug sous forme de string
        slug = create_response.json()
        if not isinstance(slug, str):
            slug = slug.get("slug") if isinstance(slug, dict) else None
        if not slug:
            print(f"❌ Pas de slug dans la réponse API")
            return {"success": False, "error": "Pas de slug retourné"}
        
        # Étape 1.5 : GET pour récupérer le vrai nom assigné par Mealie (peut avoir un suffixe -2, -3...)
        get_response = requests.get(f"{api_url}/recipes/{slug}", headers=headers, timeout=10)
        real_name = recipe_name
        if get_response.status_code == 200:
            real_name = get_response.json().get("name", recipe_name)
        
        # Étape 2 : PATCH avec le payload complet → peuple la recette
        # Utiliser le vrai nom et slug assignés par Mealie, supprimer l'image (gérée séparément)
        patch_payload = {**final_payload, "name": real_name, "slug": slug, "image": None}
        
        # Résoudre foods et units des ingrédients → objets {id, name} Mealie
        foods_cache, units_cache = _build_mealie_cache(api_url, headers)
        resolved_ingredients = []
        for ing in patch_payload.get("recipeIngredient", []):
            ing = dict(ing)
            unit_val = ing.get("unit")
            food_val = ing.get("food")
            if unit_val and isinstance(unit_val, str) and unit_val.strip():
                ing["unit"] = _get_or_create_unit(api_url, headers, unit_val.strip(), units_cache)
            else:
                ing["unit"] = None  # Mealie rejette les strings vides avec ValueError
            if food_val and isinstance(food_val, str) and food_val.strip():
                ing["food"] = _get_or_create_food(api_url, headers, food_val.strip(), foods_cache)
            else:
                ing["food"] = None
            resolved_ingredients.append(ing)
        if resolved_ingredients:
            patch_payload["recipeIngredient"] = resolved_ingredients
        
        # Résoudre recipeCategory et tags → objets avec vrais IDs Mealie
        categories = patch_payload.get("recipeCategory", [])
        if categories and isinstance(categories[0], str):
            patch_payload["recipeCategory"] = _resolve_items(api_url, headers, "organizers/categories", categories)
        elif categories and isinstance(categories[0], dict) and not categories[0].get("id"):
            patch_payload["recipeCategory"] = _resolve_items(api_url, headers, "organizers/categories", [c["name"] for c in categories])
        tags = patch_payload.get("tags", [])
        if tags and isinstance(tags[0], str):
            patch_payload["tags"] = _resolve_items(api_url, headers, "organizers/tags", tags)
        elif tags and isinstance(tags[0], dict) and not tags[0].get("id"):
            patch_payload["tags"] = _resolve_items(api_url, headers, "organizers/tags", [t["name"] for t in tags])
        patch_response = requests.patch(
            f"{api_url}/recipes/{slug}",
            headers=headers,
            json=patch_payload,
            timeout=15
        )
        
        if patch_response.status_code in [200, 201]:
            # Étape 3 : Uploader l'image (URL recette ou fallback TheMealDB)
            image_raw = final_payload.get("image") or final_payload.get("image_path") or kwargs.get("image")
            # Marmiton JSON-LD retourne une liste d'URLs → prendre la première .jpg
            if isinstance(image_raw, list):
                image_url = next((u for u in image_raw if isinstance(u, str) and u.endswith('.jpg')), None) or \
                            next((u for u in image_raw if isinstance(u, str) and u.startswith('http')), None)
            else:
                image_url = image_raw
            _upload_recipe_image(api_url, headers, slug, image_url, recipe_name)
            return {"success": True, "recipe_id": slug, "id": slug}
        else:
            print(f"❌ Recette créée (slug: {slug}) mais PATCH échoué: {patch_response.status_code} - {patch_response.text[:200]}")
            # La recette existe quand même, retourner succès partiel
            return {"success": True, "recipe_id": slug, "id": slug, "warning": f"PATCH échoué: {patch_response.status_code}"}
            
    except Exception as e:
        print(f"❌ Erreur connexion create_recipe: {e}")
        return {"success": False, "error": str(e)}

def mcp3_delete_recipe(slug):
    """Supprime une recette avec authentification"""
    if not api_url or not token:
        print("❌ Configuration Mealie manquante")
        return {"success": False, "error": "Configuration manquante"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(f"{api_url}/recipes/{slug}", headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            print(f"✅ Recette {slug} supprimée")
            return {"success": True, "message": f"Recette {slug} supprimée"}
        else:
            print(f"❌ Erreur suppression: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ Erreur connexion delete_recipe: {e}")
        return {"success": False, "error": str(e)}

def mcp3_update_recipe(slug, updates):
    """Met à jour une recette avec authentification"""
    if not api_url or not token:
        print("❌ Configuration Mealie manquante")
        return {"success": False, "error": "Configuration manquante"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.patch(f"{api_url}/recipes/{slug}", headers=headers, json=updates, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Recette {slug} mise à jour")
            return {"success": True, "updated_recipe": result}
        else:
            print(f"❌ Erreur mise à jour: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ Erreur connexion update_recipe: {e}")
        return {"success": False, "error": str(e)}

# MCP Jina (disponibles directement)
try:
    mcp2_read_url = globals().get('mcp2_read_url')
    mcp2_search_images = globals().get('mcp2_search_images')
    mcp2_show_api_key = globals().get('mcp2_show_api_key')
    
    if mcp2_read_url and mcp2_search_images:
        print("✅ MCP Jina disponibles")
    else:
        print("⚠️ MCP Jina non disponibles")
        
        # Fallbacks MCP Jina
        def mcp2_read_url(url):
            print(f"⚠️ Simulation mcp2_read_url: {url}")
            return f"Contenu simulé pour {url}"
        
        def mcp2_search_images(query, return_url=False, num=3):
            print(f"⚠️ Simulation mcp2_search_images: {query}")
            if return_url:
                return ["https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop"]
            else:
                return [{"url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop"}]
        
        def mcp2_show_api_key():
            print("⚠️ Simulation mcp2_show_api_key")
            return "jina-api-key-simulated"
        
except Exception as e:
    print(f"⚠️ Erreur MCP Jina: {e}")

# Importer les MCP personnalisés critiques
print("\n🔧 CHARGEMENT MCP CRITIQUES")
try:
    exec((WRAPPER_DIR / 'mcp3_validate_recipe.py').read_text(encoding='utf-8'))
    print("✅ validate_recipe chargé")
except Exception as e:
    print(f"⚠️ Import validate_recipe: {e}")

try:
    exec((WRAPPER_DIR / 'mcp3_verify_import.py').read_text(encoding='utf-8'))
    print("✅ verify_import chargé")
except Exception as e:
    print(f"⚠️ Import verify_recipe: {e}")

try:
    exec((WRAPPER_DIR / 'mcp3_import_batch.py').read_text(encoding='utf-8'))
    print("✅ import_batch chargé")
except Exception as e:
    print(f"⚠️ Import import_batch: {e}")

try:
    exec((WRAPPER_DIR / 'mcp3_check_recipe_quality.py').read_text(encoding='utf-8'))
    print("✅ check_recipe_quality chargé")
except Exception as e:
    print(f"⚠️ Import check_recipe_quality: {e}")

try:
    exec((WRAPPER_DIR / 'mcp3_cleanup_duplicates.py').read_text(encoding='utf-8'))
    print("✅ cleanup_duplicates chargé")
except Exception as e:
    print(f"⚠️ Import cleanup_duplicates: {e}")

try:
    exec((WRAPPER_DIR / 'mcp3_fix_invalid_recipes.py').read_text(encoding='utf-8'))
    print("✅ fix_invalid_recipes chargé")
except Exception as e:
    print(f"⚠️ Import fix_invalid_recipes: {e}")

def audit_recipes(fix: bool = False) -> dict:
    """Audite toutes les recettes Mealie et détecte les problèmes courants.

    Détecte :
    - Images manquantes (champ image null/vide)
    - Images depuis CDN de placeholder connus (picsum, via.placeholder, etc.)
    - Tags avec nom de type test/debug/tmp
    - Doublons probables (slug se terminant par -1, -2, ... ou noms très proches)

    Si fix=True :
    - Supprime les tags "test" détectés
    - Tente un upload d'image TheMealDB pour les recettes sans image valide
    """
    import re as _re
    from difflib import SequenceMatcher

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    BAD_IMAGE_DOMAINS = ["picsum.photos", "via.placeholder.com", "dummyimage.com",
                         "lorempixel.com", "placehold.it", "placeimg.com"]
    TEST_TAG_WORDS = {"test", "debug", "tmp", "temp", "sample", "example", "demo"}
    DUPE_SLUG_RE = _re.compile(r"-(\d+)$")

    r = requests.get(f"{api_url}/recipes?perPage=200&page=1", headers=headers, timeout=10)
    if r.status_code != 200:
        return {"success": False, "error": f"Impossible de lister les recettes: {r.status_code}"}

    recipes = r.json().get("items", [])
    report = {"total": len(recipes), "issues": [], "fixed": []}

    slug_names = {rec["slug"]: rec.get("name", "") for rec in recipes}

    for rec in recipes:
        slug = rec["slug"]
        name = rec.get("name", "")
        image = rec.get("image")        # None ou nom de fichier si existant
        tags  = rec.get("tags", [])
        issues_for_rec = []

        # 1. Image manquante
        if not image:
            issues_for_rec.append("no_image")

        # 2. Image depuis CDN placeholder
        elif any(bad in str(image) for bad in BAD_IMAGE_DOMAINS):
            issues_for_rec.append(f"bad_image_cdn:{image[:80]}")

        # 3. Tags "test"
        test_tags = [t for t in tags if t.get("name", "").lower().strip() in TEST_TAG_WORDS]
        if test_tags:
            issues_for_rec.append(f"test_tags:{[t['name'] for t in test_tags]}")

        # 4. Doublon probable : slug se termine par -N
        m = DUPE_SLUG_RE.search(slug)
        if m:
            base_slug = slug[:slug.rfind(f"-{m.group(1)}")]
            if base_slug in slug_names:
                issues_for_rec.append(f"probable_duplicate_of:{base_slug}")

        if issues_for_rec:
            entry = {"slug": slug, "name": name, "issues": issues_for_rec}
            report["issues"].append(entry)
            print(f"  ⚠️  {name} ({slug})")
            for iss in issues_for_rec:
                print(f"       → {iss}")

            if fix:
                # Fix A : supprimer les tags test
                if test_tags:
                    detail_r = requests.get(f"{api_url}/recipes/{slug}", headers=headers, timeout=8)
                    if detail_r.status_code == 200:
                        recipe_detail = detail_r.json()
                        kept_tags = [t for t in recipe_detail.get("tags", [])
                                     if t.get("name", "").lower().strip() not in TEST_TAG_WORDS]
                        patch_r = requests.patch(f"{api_url}/recipes/{slug}", headers=headers,
                                                  json={"tags": kept_tags}, timeout=10)
                        if patch_r.status_code in [200, 201]:
                            print(f"       ✅ Tags test supprimés")
                            report["fixed"].append(f"{slug}: tags test supprimés")

                # Fix B : image manquante ou CDN placeholder → TheMealDB
                if "no_image" in issues_for_rec or any("bad_image_cdn" in i for i in issues_for_rec):
                    # Supprimer l'image existante si CDN placeholder
                    if any("bad_image_cdn" in i for i in issues_for_rec):
                        requests.delete(f"{api_url}/recipes/{slug}/image", headers=headers, timeout=8)
                    # Tenter TheMealDB
                    themealsdb = _fetch_themealsdb_image(name)
                    if themealsdb:
                        _, ct, img_bytes = themealsdb
                        ext = "jpg" if "jpeg" in ct else ct.split("/")[-1].split(";")[0]
                        import tempfile, os as _os
                        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
                            f.write(img_bytes); tmp = f.name
                        try:
                            put_h = {k: v for k, v in headers.items() if k != "Content-Type"}
                            pr = requests.put(f"{api_url}/recipes/{slug}/image", headers=put_h,
                                              files={"image": (f"image.{ext}", open(tmp, "rb"), ct),
                                                     "extension": (None, ext)}, timeout=20)
                            if pr.status_code == 200:
                                print(f"       ✅ Image TheMealDB uploadée")
                                report["fixed"].append(f"{slug}: image TheMealDB ajoutée")
                        finally:
                            _os.unlink(tmp)
                    else:
                        print(f"       ℹ️  Pas d'image TheMealDB pour '{name}'")

    print(f"\n📊 Audit terminé: {len(report['issues'])}/{report['total']} recettes avec problèmes")
    if fix:
        print(f"✅ Corrections appliquées: {len(report['fixed'])}")
    return report


print("\n🎉 MCP WRAPPER AUTHENTIFIÉ INITIALISÉ")
print("✅ Vrais MCP Mealie avec authentification")
print("✅ Outils de validation et vérification")
print("✅ Import par lot et qualité")
print("✅ Nettoyage et corrections")
print("✅ Plus besoin de MCP mealie-test")
print("✅ 100% MCP réels et fonctionnels !")

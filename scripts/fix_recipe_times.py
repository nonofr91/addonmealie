#!/usr/bin/env python3
"""Script pour retraiter les recettes existantes et convertir les temps ISO en format texte lisible."""

import os
import re
import sys
from typing import Optional

import requests

MEALIE_BASE_URL = os.environ.get("MEALIE_BASE_URL", "https://your-mealie-instance.com")
MEALIE_API_KEY = os.environ.get("MEALIE_API_KEY", "")

if not MEALIE_API_KEY:
    print("❌ ERREUR: MEALIE_API_KEY n'est pas définie")
    print("   Exportez la variable d'environnement:")
    print("   export MEALIE_API_KEY=your-api-key")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {MEALIE_API_KEY}",
    "Content-Type": "application/json"
}


def iso_to_minutes(iso: str) -> Optional[str]:
    """Convert ISO 8601 duration to minutes."""
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', iso.upper())
    if not m:
        return None
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    total = hours * 60 + minutes
    return str(total) if total > 0 else None


def minutes_to_text(minutes) -> Optional[str]:
    """Convert minutes to readable text format."""
    if minutes is None:
        return None
    try:
        m = int(minutes)
    except (ValueError, TypeError):
        return None
    if m <= 0:
        return None
    hours, mins = divmod(m, 60)
    if hours == 0:
        return f"{mins} minutes"
    if mins == 0:
        return f"{hours} hour{'s' if hours > 1 else ''}"
    return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"


def get_all_recipes():
    """Get all recipes from Mealie."""
    recipes = []
    page = 1
    per_page = 100
    
    while True:
        response = requests.get(
            f"{MEALIE_BASE_URL}/api/recipes",
            headers=HEADERS,
            params={"page": page, "perPage": per_page}
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get("items"):
            break
        
        recipes.extend(data["items"])
        
        if len(data["items"]) < per_page:
            break
        
        page += 1
    
    return recipes


def get_recipe_detail(slug: str):
    """Get detailed recipe information."""
    response = requests.get(
        f"{MEALIE_BASE_URL}/api/recipes/{slug}",
        headers=HEADERS
    )
    response.raise_for_status()
    return response.json()


def update_recipe(slug: str, recipe_data: dict):
    """Update recipe with converted times."""
    response = requests.patch(
        f"{MEALIE_BASE_URL}/api/recipes/{slug}",
        headers=HEADERS,
        json=recipe_data
    )
    response.raise_for_status()
    return response.json()


def process_recipe(slug: str):
    """Process a single recipe to convert ISO times to text format."""
    try:
        recipe = get_recipe_detail(slug)
        
        updated = False
        updates = {}
        
        # Convert prepTime
        if recipe.get("prepTime"):
            minutes = iso_to_minutes(recipe["prepTime"])
            if minutes:
                text = minutes_to_text(minutes)
                if text:
                    updates["prepTime"] = text
                    updated = True
                    print(f"  ✅ prepTime: {recipe['prepTime']} → {text}")
        
        # Convert cookTime
        if recipe.get("cookTime"):
            minutes = iso_to_minutes(recipe["cookTime"])
            if minutes:
                text = minutes_to_text(minutes)
                if text:
                    updates["cookTime"] = text
                    updated = True
                    print(f"  ✅ cookTime: {recipe['cookTime']} → {text}")
        
        # Convert totalTime
        if recipe.get("totalTime"):
            minutes = iso_to_minutes(recipe["totalTime"])
            if minutes:
                text = minutes_to_text(minutes)
                if text:
                    updates["totalTime"] = text
                    updated = True
                    print(f"  ✅ totalTime: {recipe['totalTime']} → {text}")
        
        if updated:
            update_recipe(slug, updates)
            return True
        
        return False
    
    except Exception as e:
        print(f"  ❌ Error processing {slug}: {e}")
        return False


def main():
    """Main function to process all recipes."""
    print("🔍 Récupération des recettes...")
    recipes = get_all_recipes()
    print(f"📊 {len(recipes)} recettes trouvées")
    
    updated_count = 0
    skipped_count = 0
    
    for recipe in recipes:
        slug = recipe.get("slug")
        name = recipe.get("name", slug)
        print(f"\n📝 Traitement: {name} ({slug})")
        
        if process_recipe(slug):
            updated_count += 1
        else:
            skipped_count += 1
    
    print(f"\n✅ {updated_count} recettes mises à jour")
    print(f"⏭️ {skipped_count} recettes ignorées (pas de temps ISO ou déjà convertis)")


if __name__ == "__main__":
    main()

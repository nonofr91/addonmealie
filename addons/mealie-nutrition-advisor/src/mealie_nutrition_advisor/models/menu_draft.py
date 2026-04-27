"""Menu draft models for interactive menu planning."""

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .menu import MealType, NutritionFacts
from .seasonality import SeasonalScore


class DraftStatus(str, Enum):
    """Status of a menu draft."""
    draft = "draft"           # Being edited
    validated = "validated"   # Reviewed and confirmed
    cancelled = "cancelled"   # Discarded


class AlternativeRecipe(BaseModel):
    """Alternative recipe suggestion for a slot."""
    
    recipe_slug: str = Field(..., description="Recipe slug")
    recipe_name: str = Field(..., description="Recipe name")
    recipe_id: Optional[str] = Field(None, description="Mealie recipe UUID")
    score: float = Field(0.0, ge=0.0, le=1.0, description="Overall compatibility score")
    score_breakdown: dict[str, float] = Field(default_factory=dict, description="Score components: nutrition, variety, season")
    nutrition_per_serving: NutritionFacts = Field(default_factory=NutritionFacts)
    calories_per_serving: float = Field(0.0, description="Calories per serving")
    reason: str = Field("", description="Why this is suggested (e.g., 'Similar profile, higher variety score')")
    main_ingredients: list[str] = Field(default_factory=list, description="Key ingredients for seasonality check")
    seasonal_score: float = Field(0.5, ge=0.0, le=1.0, description="Seasonal fitness score")


class DraftSlot(BaseModel):
    """A single meal slot in a draft menu."""
    
    slot_id: str = Field(default_factory=lambda: str(uuid4())[:8], description="Unique slot identifier")
    meal_type: MealType = Field(..., description="Type of meal")
    recipe_slug: str = Field(..., description="Selected recipe slug")
    recipe_name: str = Field(..., description="Recipe name")
    recipe_id: Optional[str] = Field(None, description="Mealie recipe UUID")
    servings: int = Field(1, ge=1, description="Number of servings")
    
    # Scoring
    score: float = Field(0.0, ge=0.0, le=1.0, description="Overall composite score")
    score_breakdown: dict[str, float] = Field(default_factory=dict, description="Score components")
    
    # Nutrition
    nutrition_per_serving: NutritionFacts = Field(default_factory=NutritionFacts)
    
    # Variety tracking
    days_since_last_used: Optional[int] = Field(None, description="Days since this recipe was last in a menu")
    recipe_family: Optional[str] = Field(None, description="Recipe category/family for variety tracking (e.g., 'pasta', 'rice', 'soup')")
    
    # Seasonality
    ingredient_seasonal_scores: list[SeasonalScore] = Field(default_factory=list, description="Seasonal scores for main ingredients")
    seasonal_score_avg: float = Field(0.5, ge=0.0, le=1.0, description="Average seasonal score")
    
    # Alternatives for user selection
    alternatives: list[AlternativeRecipe] = Field(default_factory=list, description="Alternative recipes for this slot (top 5)")
    
    # User notes
    user_notes: str = Field("", description="User notes for this slot")
    locked: bool = Field(False, description="If True, won't be changed by auto-regeneration")


class DayDraftSlots(BaseModel):
    """All slots for a single day in a draft."""
    
    date: date = Field(..., description="Date of the day")
    day_name: str = Field(..., description="Day name (Monday, Tuesday...)")
    slots: list[DraftSlot] = Field(default_factory=list, description="Meal slots for this day")
    
    def total_nutrition(self) -> NutritionFacts:
        """Calculate total nutrition for the day."""
        total = NutritionFacts()
        for slot in self.slots:
            total = total + slot.nutrition_per_serving.scale(float(slot.servings))
        return total
    
    def total_calories(self) -> float:
        """Get total calories for the day."""
        return self.total_nutrition().calories_kcal


class ConflictReport(BaseModel):
    """Report of a conflict in the menu."""
    
    conflict_type: Literal["multi_profile", "nutrition", "variety", "availability"] = Field(..., description="Type of conflict")
    severity: Literal["info", "warning", "blocking"] = Field("info", description="Severity level")
    day: date = Field(..., description="Date of conflict")
    meal_type: MealType = Field(..., description="Meal type")
    recipe_slug: str = Field(..., description="Recipe involved")
    message: str = Field(..., description="Human-readable description")
    details: dict = Field(default_factory=dict, description="Additional details (scores, alternatives...)")


class NutritionSummary(BaseModel):
    """Nutritional summary of a draft menu."""
    
    avg_daily_calories: float = Field(0.0, description="Average daily calories")
    avg_daily_protein: float = Field(0.0, description="Average daily protein (g)")
    avg_daily_fat: float = Field(0.0, description="Average daily fat (g)")
    avg_daily_carbs: float = Field(0.0, description="Average daily carbs (g)")
    avg_daily_fiber: float = Field(0.0, description="Average daily fiber (g)")
    
    target_calories: float = Field(0.0, description="Target calories per day (from profiles)")
    calories_variance_pct: float = Field(0.0, description="Variance from target (%)")
    
    protein_adequacy_pct: float = Field(0.0, description="Protein adequacy percentage")


class MenuDraft(BaseModel):
    """A draft menu for a week."""
    
    draft_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique draft identifier")
    week_label: str = Field(..., description="Week label (YYYY-Www format, e.g., 2026-W16)")
    status: DraftStatus = Field(DraftStatus.draft, description="Current status")
    
    # Timeline
    generated_at: datetime = Field(default_factory=datetime.now, description="When generated")
    validated_at: Optional[datetime] = Field(None, description="When validated")
    pushed_to_mealie_at: Optional[datetime] = Field(None, description="When pushed to Mealie")
    
    # Content
    days: list[DayDraftSlots] = Field(default_factory=list, description="7 days of the week")
    member_names: list[str] = Field(default_factory=list, description="Household members this menu is for")
    
    # Scoring & Conflicts
    overall_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall menu quality score")
    conflicts: list[ConflictReport] = Field(default_factory=list, description="Detected conflicts")
    
    # Nutrition summary
    nutrition_summary: NutritionSummary = Field(default_factory=NutritionSummary)
    
    # User data
    user_notes: str = Field("", description="User notes for the whole menu")
    generated_by: str = Field("system", description="Who/what generated this menu")
    
    def get_slot(self, day_date: date, meal_type: MealType) -> Optional[DraftSlot]:
        """Get a specific slot by date and meal type."""
        for day in self.days:
            if day.date == day_date:
                for slot in day.slots:
                    if slot.meal_type == meal_type:
                        return slot
        return None
    
    def update_slot(self, day_date: date, meal_type: MealType, new_slot: DraftSlot) -> bool:
        """Update a specific slot. Returns True if found and updated."""
        for day in self.days:
            if day.date == day_date:
                for i, slot in enumerate(day.slots):
                    if slot.meal_type == meal_type:
                        day.slots[i] = new_slot
                        return True
        return False
    
    def to_mealie_mealplan_entries(self) -> list[dict]:
        """Convert to Mealie mealplan entries format."""
        entries = []
        for day in self.days:
            for slot in day.slots:
                entry = {
                    "date": day.date.isoformat(),
                    "entry_type": slot.meal_type.value,
                }
                if slot.recipe_id:
                    entry["recipe_id"] = slot.recipe_id
                else:
                    entry["title"] = slot.recipe_name
                entries.append(entry)
        return entries
    
    def compute_nutrition_summary(self, target_daily_calories: float = 2000.0) -> None:
        """Compute nutrition summary from slots."""
        if not self.days:
            return
        
        total_nutrition = NutritionFacts()
        for day in self.days:
            total_nutrition = total_nutrition + day.total_nutrition()
        
        num_days = len(self.days)
        self.nutrition_summary = NutritionSummary(
            avg_daily_calories=round(total_nutrition.calories_kcal / num_days, 1),
            avg_daily_protein=round(total_nutrition.protein_g / num_days, 1),
            avg_daily_fat=round(total_nutrition.fat_g / num_days, 1),
            avg_daily_carbs=round(total_nutrition.carbohydrate_g / num_days, 1),
            avg_daily_fiber=round(total_nutrition.fiber_g / num_days, 1),
            target_calories=target_daily_calories,
            calories_variance_pct=round(
                ((total_nutrition.calories_kcal / num_days) - target_daily_calories) / target_daily_calories * 100, 1
            ) if target_daily_calories > 0 else 0.0,
            protein_adequacy_pct=0.0,  # Would need target protein to calculate
        )


class DraftSummary(BaseModel):
    """Lightweight summary of a draft for listing."""
    
    draft_id: str
    week_label: str
    status: DraftStatus
    generated_at: datetime
    overall_score: float
    num_conflicts: int
    num_slots: int
    member_names: list[str]
    avg_daily_calories: float
    has_been_pushed: bool

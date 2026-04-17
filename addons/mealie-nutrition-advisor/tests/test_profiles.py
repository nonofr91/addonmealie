"""Tests for profile models and manager."""

import json

import pytest

from mealie_nutrition_advisor.models.profile import (
    ActivityLevel,
    DietaryRestriction,
    Goal,
    HouseholdProfile,
    MacroTargets,
    MemberProfile,
    Sex,
)
from mealie_nutrition_advisor.profiles.manager import ProfileManager


def _make_member(**kwargs) -> MemberProfile:
    defaults = dict(name="Test", age=30, sex=Sex.male, weight_kg=75, height_cm=175)
    defaults.update(kwargs)
    return MemberProfile(**defaults)


class TestMemberProfile:
    def test_bmr_male(self):
        m = _make_member(age=30, sex=Sex.male, weight_kg=80, height_cm=180)
        expected = 10 * 80 + 6.25 * 180 - 5 * 30 + 5
        assert m.bmr() == pytest.approx(expected)

    def test_bmr_female(self):
        m = _make_member(age=35, sex=Sex.female, weight_kg=65, height_cm=168)
        expected = 10 * 65 + 6.25 * 168 - 5 * 35 - 161
        assert m.bmr() == pytest.approx(expected)

    def test_tdee_moderately_active(self):
        m = _make_member(activity_level=ActivityLevel.moderately_active)
        assert m.tdee() == pytest.approx(m.bmr() * 1.55, rel=0.01)

    def test_target_calories_weight_loss(self):
        m = _make_member(goal=Goal.weight_loss)
        assert m.target_calories() < m.tdee()

    def test_target_calories_muscle_gain(self):
        m = _make_member(goal=Goal.muscle_gain)
        assert m.target_calories() > m.tdee()

    def test_custom_calories_override(self):
        m = _make_member(custom_targets=MacroTargets(calories_per_day=1800))
        assert m.target_calories() == pytest.approx(1800)

    def test_custom_protein_override(self):
        m = _make_member(custom_targets=MacroTargets(protein_g_per_day=150))
        assert m.recommended_protein_g() == pytest.approx(150)

    def test_summary_keys(self):
        m = _make_member()
        s = m.summary()
        assert "bmr_kcal" in s
        assert "tdee_kcal" in s
        assert "target_calories_kcal" in s
        assert "recommended_protein_g" in s


class TestHouseholdProfile:
    def test_aggregate_calories(self):
        h = HouseholdProfile(members=[_make_member(name="A"), _make_member(name="B")])
        assert h.aggregate_daily_calories() == pytest.approx(
            h.members[0].target_calories() + h.members[1].target_calories()
        )

    def test_all_allergies(self):
        m1 = _make_member(name="A", allergies=["cacahuètes"])
        m2 = _make_member(name="B", allergies=["gluten", "LAIT"])
        h = HouseholdProfile(members=[m1, m2])
        allergies = h.all_allergies()
        assert "cacahuètes" in allergies
        assert "gluten" in allergies
        assert "lait" in allergies

    def test_all_restrictions(self):
        m1 = _make_member(name="A", dietary_restrictions=[DietaryRestriction.vegetarian])
        m2 = _make_member(name="B", dietary_restrictions=[DietaryRestriction.gluten_free])
        h = HouseholdProfile(members=[m1, m2])
        restrictions = h.all_restrictions()
        assert DietaryRestriction.vegetarian in restrictions
        assert DietaryRestriction.gluten_free in restrictions


class TestProfileManager:
    def test_load_empty(self, tmp_path):
        manager = ProfileManager(config_path=tmp_path / "profiles.json")
        h = manager.load()
        assert isinstance(h, HouseholdProfile)
        assert len(h.members) == 0

    def test_add_member(self, tmp_path):
        manager = ProfileManager(config_path=tmp_path / "profiles.json")
        manager.load()
        member = _make_member(name="Alice")
        manager.add_member(member)
        assert manager.get_member("Alice") is not None

    def test_save_and_reload(self, tmp_path):
        path = tmp_path / "profiles.json"
        manager = ProfileManager(config_path=path)
        manager.load()
        manager.add_member(_make_member(name="Bob", age=40))

        manager2 = ProfileManager(config_path=path)
        h = manager2.load()
        assert len(h.members) == 1
        assert h.members[0].name == "Bob"

    def test_remove_member(self, tmp_path):
        manager = ProfileManager(config_path=tmp_path / "profiles.json")
        manager.load()
        manager.add_member(_make_member(name="Charlie"))
        assert manager.remove_member("Charlie") is True
        assert manager.get_member("Charlie") is None

    def test_update_member(self, tmp_path):
        manager = ProfileManager(config_path=tmp_path / "profiles.json")
        manager.load()
        manager.add_member(_make_member(name="Dave", age=25))
        manager.add_member(_make_member(name="Dave", age=30))
        assert len(manager.household.members) == 1
        assert manager.household.members[0].age == 30

    def test_load_example_file(self):
        from pathlib import Path
        example = Path(__file__).parent.parent / "config" / "household_profiles.json"
        if not example.exists():
            pytest.skip("household_profiles.json absent")
        manager = ProfileManager(config_path=example)
        h = manager.load()
        assert len(h.members) > 0

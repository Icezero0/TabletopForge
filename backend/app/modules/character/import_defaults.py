DND5E_CLASSES = (
    "artificer",
    "barbarian",
    "bard",
    "cleric",
    "druid",
    "fighter",
    "monk",
    "paladin",
    "ranger",
    "rogue",
    "sorcerer",
    "warlock",
    "wizard",
)


def default_identity() -> dict:
    return {
        "name": "",
        "race": "",
        "gender": "",
        "age": "",
        "height": "",
        "weight": "",
        "appearance": "",
        "alignment": "",
        "background": "",
        "classes": [],
        "gallery_asset_ids": [None, None, None],
    }


def default_flavor() -> dict:
    return {
        "personality": "",
        "ideals": "",
        "bonds": "",
        "flaws": "",
        "backstory": "",
    }


def default_attributes() -> dict:
    return {
        "ability_scores": {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
        },
        "derived": {
            "ac": {"value": 10, "breakdown": ""},
            "max_hp": {"value": 0, "breakdown": ""},
            "speed": {"value": 30, "breakdown": ""},
            "initiative": {"value": 0, "breakdown": ""},
            "proficiency_bonus": {"value": 2, "breakdown": ""},
            "passive_perception": {"value": 10, "breakdown": ""},
        },
        "saving_throws": {},
        "saving_throw_profs": {},
        "skill_values": {},
        "skill_profs": {},
        "weapon_proficiencies": [],
        "armor_proficiencies": [],
        "tool_proficiencies": [],
        "languages": [],
    }


def default_features() -> dict:
    return {
        "racial_traits": [],
        "class_features": [],
        "proficiencies": {"weapons": [], "armor": [], "tools": []},
        "custom_fields": {},
    }


def default_spells() -> dict:
    return {
        "spellcasting_ability": "intelligence",
        "spell_save_dc": {"value": 0, "breakdown": ""},
        "spell_attack_bonus": {"value": 0, "breakdown": ""},
        "cantrips": [],
        "spellbook": {
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "5": [],
            "6": [],
            "7": [],
            "8": [],
            "9": [],
        },
        "spell_slots_max": {
            "1": 0,
            "2": 0,
            "3": 0,
            "4": 0,
            "5": 0,
            "6": 0,
            "7": 0,
            "8": 0,
            "9": 0,
        },
    }


def default_equipment() -> dict:
    return {
        "items": [],
        "currency": {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0},
    }


def default_resources() -> list:
    return []


def default_extras() -> dict:
    return {"notes": ""}

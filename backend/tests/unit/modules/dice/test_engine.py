import pytest

from app.modules.dice.engine import DiceFormulaError, evaluate_formula, normalize_formula


def sequence(values):
    items = iter(values)
    return lambda _faces: next(items)


def test_normalize_formula_removes_whitespace_and_lowercases():
    assert normalize_formula(" 2D20 KH1 + 5 ") == "2d20kh1+5"


def test_normalize_formula_accepts_chinese_advantage_and_disadvantage():
    assert normalize_formula("1d优势8") == "2d8kh1"
    assert normalize_formula("1d劣势8") == "2d8kl1"
    assert normalize_formula("2d优势20") == "4d20kh2"
    assert normalize_formula("2d劣势20") == "4d20kl2"
    assert normalize_formula("d优势20+5") == "2d20kh1+5"
    assert normalize_formula("d优势+7") == "2d20kh1+7"


def test_evaluate_simple_dice_and_modifier():
    result = evaluate_formula("1d20+3", random_int=sequence([14]))

    assert result.formula == "1d20+3"
    assert result.total == 17
    assert result.detail["terms"][0]["rolls"] == [{"value": 14, "kept": True}]
    assert result.detail["terms"][1]["total"] == 3


def test_evaluate_omitted_single_die_count():
    result = evaluate_formula("d8+2", random_int=sequence([6]))

    assert result.formula == "d8+2"
    assert result.total == 8
    assert result.detail["terms"][0]["count"] == 1


def test_evaluate_omitted_die_faces_defaults_to_d20():
    result = evaluate_formula("2d+1", random_int=sequence([4, 17]))

    assert result.formula == "2d+1"
    assert result.total == 22
    assert result.detail["terms"][0]["count"] == 2
    assert result.detail["terms"][0]["faces"] == 20


def test_evaluate_advantage_keeps_highest():
    result = evaluate_formula("2d20kh1+5", random_int=sequence([7, 18]))

    assert result.total == 23
    dice_term = result.detail["terms"][0]
    assert dice_term["keep"] == "kh1"
    assert dice_term["rolls"] == [
        {"value": 7, "kept": False},
        {"value": 18, "kept": True},
    ]


def test_evaluate_chinese_advantage_keeps_highest():
    result = evaluate_formula("1d优势8+1", random_int=sequence([3, 7]))

    assert result.formula == "2d8kh1+1"
    assert result.total == 8
    dice_term = result.detail["terms"][0]
    assert dice_term["keep"] == "kh1"
    assert dice_term["rolls"] == [
        {"value": 3, "kept": False},
        {"value": 7, "kept": True},
    ]


def test_evaluate_chinese_advantage_with_multiple_base_dice():
    result = evaluate_formula("2d优势20", random_int=sequence([3, 19, 12, 8]))

    assert result.formula == "4d20kh2"
    assert result.total == 31
    dice_term = result.detail["terms"][0]
    assert dice_term["keep"] == "kh2"
    assert dice_term["rolls"] == [
        {"value": 3, "kept": False},
        {"value": 19, "kept": True},
        {"value": 12, "kept": True},
        {"value": 8, "kept": False},
    ]


def test_evaluate_disadvantage_keeps_lowest():
    result = evaluate_formula("2d20kl1-1", random_int=sequence([7, 18]))

    assert result.total == 6
    dice_term = result.detail["terms"][0]
    assert dice_term["keep"] == "kl1"
    assert dice_term["rolls"] == [
        {"value": 7, "kept": True},
        {"value": 18, "kept": False},
    ]


@pytest.mark.parametrize("formula", ["", "1d20++5", "2d20kh3", "101d6", "1d1", "(1d20)+2"])
def test_invalid_formula_raises(formula):
    with pytest.raises(DiceFormulaError):
        evaluate_formula(formula, random_int=sequence([1] * 200))

from unittest.mock import patch

import pytest

from app.core.exceptions import AppError


VALID_LLM_JSON = """{
  "name": "艾莉亚",
  "player_name": "玩家A",
  "identity": {
    "name": "艾莉亚",
    "race": "精灵",
    "classes": [{"name": "ranger", "level": 3, "subclass": "猎人"}]
  },
  "flavor": {"backstory": "来自北方森林"},
  "attributes": {
    "ability_scores": {
      "strength": 10, "dexterity": 16, "constitution": 12,
      "intelligence": 10, "wisdom": 14, "charisma": 8
    },
    "derived": {"max_hp": {"value": 28, "breakdown": ""}}
  },
  "features": {"racial_traits": [{"name": "黑暗视觉", "notes": "60尺"}]},
  "equipment": {"items": [{"name": "长弓", "quantity": 1, "notes": ""}]},
  "extras": {"notes": "测试"}
}"""


@pytest.mark.asyncio
async def test_import_preview_success(api_client, factories, auth_headers) -> None:
    user = await factories.create_user()
    await factories.commit()

    with patch(
        "app.api.v1.characters.import_preview",
        return_value=__import__(
            "app.modules.character.import_service",
            fromlist=["parse_and_normalize"],
        ).parse_and_normalize(VALID_LLM_JSON),
    ):
        response = await api_client.post(
            "/api/v1/characters/import-preview",
            headers=auth_headers(user),
            json={"raw_text": "艾莉亚，3级游侠，精灵"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "艾莉亚"
    assert body["player_name"] == "玩家A"
    assert body["identity"]["race"] == "精灵"
    assert body["identity"]["classes"][0]["name"] == "ranger"
    assert body["attributes"]["ability_scores"]["dexterity"] == 16


@pytest.mark.asyncio
async def test_import_preview_invalid_json(api_client, factories, auth_headers) -> None:
    user = await factories.create_user()
    await factories.commit()

    with patch(
        "app.api.v1.characters.import_preview",
        side_effect=lambda raw: __import__(
            "app.modules.character.import_service",
            fromlist=["parse_and_normalize"],
        ).parse_and_normalize("not-json"),
    ):
        response = await api_client.post(
            "/api/v1/characters/import-preview",
            headers=auth_headers(user),
            json={"raw_text": "broken"},
        )

    assert response.status_code == 400
    assert response.json()["error"]["reason"] == "llm_invalid_json"


@pytest.mark.asyncio
async def test_import_preview_missing_api_key(api_client, factories, auth_headers) -> None:
    user = await factories.create_user()
    await factories.commit()

    with patch(
        "app.api.v1.characters.import_preview",
        side_effect=AppError(
            "LLM API key is not configured. Set LLM_API_KEY or DASHSCOPE_API_KEY in .env",
            code="service_unavailable",
            status_code=503,
            reason="llm_not_configured",
        ),
    ):
        response = await api_client.post(
            "/api/v1/characters/import-preview",
            headers=auth_headers(user),
            json={"raw_text": "some text"},
        )

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["reason"] == "llm_not_configured"
    assert "LLM_API_KEY" in body["error"]["message"]

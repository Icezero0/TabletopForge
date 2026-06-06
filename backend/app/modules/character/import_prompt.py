"""LLM prompt templates for D&D 5e character text import."""

from __future__ import annotations

from app.modules.character.import_defaults import DND5E_CLASSES

_SKILL_KEYS = (
    "acrobatics",
    "animal_handling",
    "arcana",
    "athletics",
    "deception",
    "history",
    "insight",
    "intimidation",
    "investigation",
    "medicine",
    "nature",
    "perception",
    "performance",
    "persuasion",
    "religion",
    "sleight_of_hand",
    "stealth",
    "survival",
)

_ABILITY_KEYS = (
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
)

_ALIGNMENTS = (
    "",
    "lawful_good",
    "neutral_good",
    "chaotic_good",
    "lawful_neutral",
    "true_neutral",
    "chaotic_neutral",
    "lawful_evil",
    "neutral_evil",
    "chaotic_evil",
)


def _output_format_section() -> str:
    classes = ", ".join(DND5E_CLASSES)
    skills = ", ".join(_SKILL_KEYS)
    abilities = ", ".join(_ABILITY_KEYS)
    alignments = ", ".join(_ALIGNMENTS)

    return f"""## 5. 输出格式（OUTPUT FORMAT）

只输出**一个 JSON 对象**，不要用 markdown 代码块，不要附加解释文字。

### 5.1 顶层字段

| 字段 | 类型 | 含义 |
|------|------|------|
| `name` | string | 角色名（必填）。与 `identity.name` 保持一致；无法确定时用 `"未命名角色"` |
| `player_name` | string | 玩家/操控者姓名；文本未提及则 `""` |
| `identity` | object | 角色身份与外貌（见 5.2） |
| `flavor` | object | 性格与背景叙事（见 5.3） |
| `attributes` | object | 数值、豁免、技能与熟练（见 5.4） |
| `features` | object | 种族/职业特性（见 5.5） |
| `spells` | object \\| null | 施法信息；非施法者或无信息时 `null` |
| `equipment` | object | 物品与货币（见 5.6） |
| `extras` | object | 其他备注（见 5.7） |
| `state` | null | 导入预览固定为 `null`（实时状态由对战层维护，勿填写） |

### 5.2 `identity` — 角色信息 Tab

| 字段 | 类型 | 含义 |
|------|------|------|
| `name` | string | 角色名，与顶层 `name` 一致 |
| `race` | string | 种族，如「人类」「精灵」 |
| `gender` | string | 性别 |
| `age` | string | 年龄（保留原文表述，如「25岁」「青年」） |
| `height` | string | 身高 |
| `weight` | string | 体重 |
| `appearance` | string | 外貌描述 |
| `alignment` | string | 阵营枚举，必须是以下之一：{alignments}；未知则 `""` |
| `background` | string | 背景（如「士兵」「学者」） |
| `classes` | array | 职业列表，支持多职业；每项见下表 |
| `gallery_asset_ids` | array | 固定 `[null, null, null]`，不要编造图片 ID |

`classes[]` 每项：

| 字段 | 类型 | 含义 |
|------|------|------|
| `name` | string | 职业枚举，**必须**是：{classes} |
| `level` | int | 该职业等级，1–20 |
| `subclass` | string | 子职业/范型；未知则 `""` |

### 5.3 `flavor` — 性格与背景

| 字段 | 类型 | 含义 |
|------|------|------|
| `personality` | string | 性格特点 |
| `ideals` | string | 理想 |
| `bonds` | string | 羁绊 |
| `flaws` | string | 缺陷 |
| `backstory` | string | 背景故事长文 |

### 5.4 `attributes` — 属性 Tab

| 字段 | 类型 | 含义 |
|------|------|------|
| `ability_scores` | object | 六维属性，键为 {abilities}；每项整数 1–30 |
| `derived` | object | 派生数值，键见下表；每项为 `{{"value": number, "breakdown": string}}` |
| `saving_throws` | object | 豁免加值，键为六维属性名；值为 `"+3"` / `"-1"` 格式字符串，未知可 `""` |
| `saving_throw_profs` | object | 豁免熟练标记，键为六维属性名；值为 `true`（熟练）或 `false`；未提及可省略（默认 `{{}}`） |
| `skill_values` | object | 技能加值，键为技能 key（见下）；值为 `"+3"` 格式字符串，未知可 `""` |
| `skill_profs` | object | 技能熟练等级，键为技能 key；值为 `"none"` / `"proficient"` / `"expert"`；未提及可省略（默认 `{{}}`） |
| `weapon_proficiencies` | string[] | 武器熟练，如 `["简易武器","长剑"]` |
| `armor_proficiencies` | string[] | 护甲熟练 |
| `tool_proficiencies` | string[] | 工具熟练 |
| `languages` | string[] | 语言列表 |

`derived` 必须包含以下键，每项均为 `{{value, breakdown}}`：

| 键 | 含义 | `value` 说明 |
|----|------|----------------|
| `ac` | 护甲等级 AC | 整数 |
| `max_hp` | 最大生命值 | 整数 |
| `speed` | 速度（尺） | 整数，默认 30 |
| `initiative` | 先攻加值 | 整数 |
| `proficiency_bonus` | 熟练加值 | 整数，通常 2–6 |
| `passive_perception` | 被动察觉 | 整数，通常 10+察觉加值 |

`breakdown` 用简短中文说明计算来源（如 `"10 + 敏捷2"`），无则 `""`。

技能 `skill_values` 合法键：{skills}

### 5.5 `features` — 特性 Tab

| 字段 | 类型 | 含义 |
|------|------|------|
| `racial_traits` | array | 种族特性，每项 `{{"name": string, "notes": string}}` |
| `class_features` | array | 职业特性，每项 `{{"name": string, "source": string, "notes": string}}`；`source` 为职业枚举 |
| `proficiencies` | object | `{{"weapons": string[], "armor": string[], "tools": string[]}}`，可与 attributes 熟练互补 |
| `custom_fields` | object | 自定义键值对，如 `{{"灵感": "1"}}`；无则 `{{}}` |

### 5.6 `spells` — 法术 Tab（施法者填写，否则 `null`）

| 字段 | 类型 | 含义 |
|------|------|------|
| `spellcasting_ability` | string | `intelligence` \\| `wisdom` \\| `charisma` |
| `spell_save_dc` | object | `{{"value": int, "breakdown": string}}` 法术豁免 DC |
| `spell_attack_bonus` | object | `{{"value": int, "breakdown": string}}` 法术攻击加值 |
| `spellbook` | object | 按环位存放法术名；键 `"0"`–`"9"`，`"0"` 为戏法，值为 `string[]` |
| `spell_slots_max` | object | 各环位每日法术位上限；键 `"1"`–`"9"`，值为 int |

### 5.7 `equipment` — 背包 Tab

| 字段 | 类型 | 含义 |
|------|------|------|
| `items` | array | 物品列表，每项 `{{"name": string, "quantity": int, "notes": string}}` |
| `currency` | object | `{{"cp":0,"sp":0,"ep":0,"gp":0,"pp":0}}` 各币种数量 |

### 5.8 `extras`

| 字段 | 类型 | 含义 |
|------|------|------|
| `notes` | string | 不适合归入其他分类的自由备注 |

### 5.9 JSON 骨架示例（字段必须齐全，值按文本填写）

{{
  "name": "角色名",
  "player_name": "",
  "identity": {{
    "name": "角色名",
    "race": "",
    "gender": "",
    "age": "",
    "height": "",
    "weight": "",
    "appearance": "",
    "alignment": "",
    "background": "",
    "classes": [{{"name": "fighter", "level": 1, "subclass": ""}}],
    "gallery_asset_ids": [null, null, null]
  }},
  "flavor": {{
    "personality": "",
    "ideals": "",
    "bonds": "",
    "flaws": "",
    "backstory": ""
  }},
  "attributes": {{
    "ability_scores": {{
      "strength": 10,
      "dexterity": 10,
      "constitution": 10,
      "intelligence": 10,
      "wisdom": 10,
      "charisma": 10
    }},
    "derived": {{
      "ac": {{"value": 10, "breakdown": ""}},
      "max_hp": {{"value": 0, "breakdown": ""}},
      "speed": {{"value": 30, "breakdown": ""}},
      "initiative": {{"value": 0, "breakdown": ""}},
      "proficiency_bonus": {{"value": 2, "breakdown": ""}},
      "passive_perception": {{"value": 10, "breakdown": ""}}
    }},
    "saving_throws": {{}},
    "saving_throw_profs": {{}},
    "skill_values": {{}},
    "skill_profs": {{}},
    "weapon_proficiencies": [],
    "armor_proficiencies": [],
    "tool_proficiencies": [],
    "languages": []
  }},
  "features": {{
    "racial_traits": [],
    "class_features": [],
    "proficiencies": {{"weapons": [], "armor": [], "tools": []}},
    "custom_fields": {{}}
  }},
  "spells": null,
  "equipment": {{
    "items": [],
    "currency": {{"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0}}
  }},
  "extras": {{"notes": ""}},
  "state": null
}}"""


def build_import_prompt(raw_text: str) -> str:
    classes = ", ".join(DND5E_CLASSES)

    return f"""# D&D 5e 角色卡文本导入

## 1. 任务描述（TASK）

你是 TabletopForge 的角色卡结构化提取助手。用户会提供一段**非结构化**的 D&D 5e 角色信息（导出卡、论坛帖、聊天记录、PDF 复制等）。

你的任务是：阅读全文，提取能确定的字段，输出**一份完整 JSON**，供前端 6 个编辑 Tab（身份 / 属性 / 特性 / 法术 / 背包 / 其他）预填表单。用户会在界面中校对后再保存。

**不要**编造文本中不存在的事实；**不要**输出 markdown 或自然语言说明；**只输出 JSON**。

## 2. 任务规则（RULES）

### 2.1 忠实性
- 仅提取输入文本中**明确出现或可直接推断**的信息。
- 无法确定的字段：字符串用 `""`，数组用 `[]`，对象用 `{{}}` 或文档规定的默认值。
- 不要虚构玩家名、肖像、图库资源 ID、实时 HP 等输入未提供的内容。

### 2.2 命名与枚举
- JSON 键名一律使用文档规定的 **snake_case 英文键**。
- `identity.classes[].name` 与 `features.class_features[].source` 必须是英文职业枚举：{classes}
- 若原文为中文职业名，映射到最接近的枚举（如 战士→fighter，游侠→ranger，法师→wizard）。
- `identity.alignment` 使用英文枚举值（如 `lawful_good`），不要用中文。

### 2.3 数值与格式
- `ability_scores` 每项为整数，范围 1–30。
- `derived.*` 必须为 `{{"value": number, "breakdown": string}}`，不可写成裸数字。
- `saving_throws` / `skill_values` 的值为修饰符字符串（如 `"+5"`、`"-1"`），不是裸整数。
- 多职业时：`classes` 数组可有多项；`level` 为各职业等级之和应合理（总等级通常 ≤ 20）。

### 2.4 施法与法术
- 明显非施法职业且无法术列表：`spells` 设为 `null`。
- 施法者：填写 `spells` 对象；戏法放入 `spellbook["0"]`，1–9 环法术放入对应键。

### 2.5 一致性
- 顶层 `name` 与 `identity.name` 保持一致。
- 同一信息出现在多处时（如种族在正文与表格各写一次），取最完整、最一致的一份。
- 列表字段保留原文用语（中文武器名、特性名可保持中文）。

### 2.6 输出约束
- 响应体只能是**单个 JSON 对象**。
- 必须包含输出格式章节中列出的**全部顶层键**及嵌套结构，不可省略键。

## 3. 任务工作流（WORKFLOW）

按以下顺序执行（内部推理，不要在输出中写步骤说明）：

1. **通读**：浏览全文，识别角色名、职业/等级、种族、六维、HP/AC、技能、特性、法术、装备。
2. **分段映射**：将信息归入 `identity` / `flavor` / `attributes` / `features` / `spells` / `equipment` / `extras`。
3. **规范化**：职业转枚举；阵营转英文枚举；数值转合法范围；派生项套 `{{value, breakdown}}`。
4. **补缺**：未提及的字段填入空值或默认值，保证 JSON 结构与输出格式一致。
5. **校验**：检查必填键、枚举合法性、顶层 `name` 非空；最后只输出 JSON。

## 4. 输入（INPUT）

以下为用户粘贴的原始角色文本。除该文本外无其他上下文：

---BEGIN CHARACTER TEXT---
{raw_text}
---END CHARACTER TEXT---

{_output_format_section()}"""


def build_import_system_message() -> str:
    return (
        "你是 TabletopForge 的 D&D 5e 角色卡 JSON 提取器。"
        "严格按用户消息中的任务描述、规则、工作流与输出格式执行。"
        "只输出一个合法 JSON 对象，不要 markdown，不要解释。"
    )

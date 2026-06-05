# 角色卡模块设计

版本：v0.5  
状态：Draft

---

## 1 模块目标

维护玩家的 **角色定义**（Character），支持角色信息编辑、属性计算辅助、法术管理、装备记录，
以及后续与房间 Token / CharacterState 实时状态层联动。

当前已完整实现：角色卡列表页、角色卡编辑页（6 个 Tab）、角色头像上传、脏数据守卫。

---

## 2 数据模型

### 2.1 数据库表

```text
characters
├── id                 INTEGER PK
├── owner_id           INTEGER FK → users.id (CASCADE DELETE)
├── name               VARCHAR(255)       -- 从 identity.name 冗余，方便列表查询
├── player_name        VARCHAR(255)
├── portrait_asset_id  INTEGER FK → assets.id (SET NULL)
├── system             VARCHAR(50)        -- 固定 "dnd5e"
├── identity           JSON               -- 见 2.2
├── flavor             JSON               -- 见 2.3
├── attributes         JSON               -- 见 2.4
├── features           JSON               -- 见 2.5
├── spells             JSON NULLABLE      -- 见 2.6
├── equipment          JSON               -- 见 2.7
├── extras             JSON               -- 见 2.8
├── created_at         TIMESTAMPTZ
└── updated_at         TIMESTAMPTZ
```

### 2.2 identity 块

```jsonc
{
  "name": "角色名",
  "race": "种族",
  "gender": "性别",
  "age": "年龄",
  "height": "身高",
  "weight": "体重",
  "appearance": "外貌描述",
  "alignment": "lawful_good | neutral_good | ...",   // 9 阵营枚举 + ""
  "background": "背景",
  "classes": [
    { "name": "fighter", "level": 3, "subclass": "武器大师" }
    // 支持多职业，职业名为 DND5E_CLASSES 中的枚举值
  ],
  "gallery_asset_ids": [null, null, null]             // 最多 3 张图库图片
}
```

**职业枚举**（`DND5E_CLASSES`，共 13 个）：

`artificer` `barbarian` `bard` `cleric` `druid`
`fighter` `monk` `paladin` `ranger` `rogue`
`sorcerer` `warlock` `wizard`

编辑时以下拉选择框呈现；已选职业不出现在其他行的选项中；中英文跟随 i18n 切换。

### 2.3 flavor 块

```jsonc
{
  "personality": "性格特点",
  "ideals": "理想",
  "bonds": "羁绊",
  "flaws": "缺陷",
  "backstory": "背景故事"
}
```

### 2.4 attributes 块

```jsonc
{
  "ability_scores": {
    "strength": 10, "dexterity": 10, "constitution": 10,
    "intelligence": 10, "wisdom": 10, "charisma": 10
  },
  "derived": {
    "ac":                { "value": 10, "breakdown": "" },
    "max_hp":            { "value": 0,  "breakdown": "" },
    "speed":             { "value": 30, "breakdown": "" },
    "initiative":        { "value": 0,  "breakdown": "" },
    "proficiency_bonus": { "value": 2,  "breakdown": "" },
    "passive_perception":{ "value": 10, "breakdown": "" }
  },
  "saving_throws": { "strength": "+2", "dexterity": "" },  // 手填文本
  "skill_values":  { "acrobatics": "+3" },                 // 手填文本
  "weapon_proficiencies": ["简单武器", "军事武器"],
  "armor_proficiencies":  ["轻甲", "中甲", "盾牌"],
  "tool_proficiencies":   ["盗贼工具"],
  "languages":            ["通用语", "精灵语"]
}
```

**`derived` 字段说明**：每个派生属性存储 `{ value, breakdown }` 二元组；`breakdown`
为计算过程说明字符串（如 `"战士3级 22 + 体质 2×3"`）。

**自动计算**（前端辅助，非强制）：

| 字段 | 计算规则 |
| --- | --- |
| `ac` | 10 + 敏捷修正 |
| `max_hp` | 各职业固定平均生命值之和 + 体质修正×总等级（首级取骰值最大值） |
| `initiative` | 敏捷修正 |
| `proficiency_bonus` | floor((总等级 - 1) / 4) + 2 |
| `passive_perception` | 10 + 察觉加值（智慧修正 + 熟练加值） |

六维属性输入带 `[−][值][+]` 步进按钮，范围 1–30；修正值实时显示在属性框下方。

### 2.5 features 块

```jsonc
{
  "racial_traits": [
    { "name": "黑暗视觉", "notes": "60 尺" }
  ],
  "class_features": [
    { "name": "战斗风格", "source": "fighter", "notes": "防御风格" }
    // source 为 DND5E_CLASSES 枚举，前端渲染为本地化职业名
  ],
  "custom_fields": {
    "灵感": "1",
    "房规备注": "..."
  }
}
```

### 2.6 spells 块

```jsonc
{
  "spellcasting_ability": "intelligence",   // intelligence | wisdom | charisma
  "spell_save_dc":      { "value": 14, "breakdown": "" },
  "spell_attack_bonus": { "value": 6,  "breakdown": "" },
  "spellbook": {
    "0": ["魔法飞弹", "冰刀术"],           // 0 环 = 戏法
    "1": ["魔法飞弹"], "2": [], "3": [],
    "4": [], "5": [], "6": [], "7": [], "8": [], "9": []
  },
  "spell_slots_max": {
    "1": 4, "2": 3, "3": 2,
    "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0
  }
}
```

法术 Tab 按环位 0–9 折叠展示；0 环标签为"0 环 (戏法)"，不显示环位格子数量。
`spell_save_dc` 和 `spell_attack_bonus` 为手填数值（无自动计算按钮）。

### 2.7 equipment 块

```jsonc
{
  "items": [
    { "name": "长剑", "quantity": 1, "notes": "+1 魔法武器" }
  ]
}
```

数量通过 `[−][qty][+]` 步进按钮调整（也可直接输入），最小值 0。
货币、魔法标记、同调状态字段已从 UI 移除（数据结构中不再写入）。

### 2.8 extras 块

```jsonc
{
  "notes": "其他备注文本..."
}
```

仅一个自由文本区域，用于记录不适合其他分类的信息。

---

## 3 编辑页 UI 结构

### 3.1 Tab 导航

| Tab key | 中文标签 | 主要内容 |
| --- | --- | --- |
| `identity` | 角色信息 | 头像、基本信息、阵营、职业/等级、图库 |
| `attributes` | 属性 | 六维属性、派生属性、豁免、技能、熟练项、语言 |
| `features` | 特性 | 种族特性、职业特性、自定义字段 |
| `spells` | 法术 | 施法属性、DC/加值、法术书（0–9 环折叠） |
| `equipment` | 背包 | 物品列表（名称 / 数量 / 备注） |
| `extras` | 其他 | 自由备注文本区 |

### 3.2 角色信息 Tab（identity）

- 头像：裁剪上传（`AvatarCropDialog`），存入 `portrait_asset_id`。
- 基本信息：名称、玩家名、种族、性别、年龄、身高、体重、外貌、阵营（下拉）、背景。
- 职业列表：每行选择职业（`BaseSelect`，已选职业不重复出现）+ 等级步进 + 子职业文本。
  支持多职业，最多可加至 13 个（全部职业各用一次）。
- 图库：3 个图片槽，各自独立上传，存入 `gallery_asset_ids`。

### 3.3 属性 Tab（attributes）

- **六维属性**：6 格网格，每格含 `[−][值][+]` 步进 + 修正值显示。
- **派生属性**：每行 `[名称][数值输入][计算过程输入][自动计算按钮]`；
  `speed` 无自动计算按钮。
- **豁免**：3 列紧凑布局，属性缩写 + 数值输入（留空时以属性修正值作占位提示）。
- **技能**：3 列紧凑布局（18 个 DnD 5e 技能），技能名 + 数值输入。
- **熟练项**：武器、护甲、工具各一行 TagInput。
- **语言**：TagInput。

### 3.4 特性 Tab（features）

- **种族特性**：列表，每行 [名称输入] [备注输入] [删除]。
- **职业特性**：列表，每行 [名称输入] [来源职业下拉] [备注输入] [删除]。
- **自定义字段**：key/value 列表，支持任意 key（允许空 key 行编辑中）；
  保存时过滤空 key，存为 `custom_fields` 对象。

### 3.5 法术 Tab（spells）

- 顶部一行：施法属性（下拉） / 法术豁免 DC（数值输入） / 法术攻击加值（数值输入）。
- 法术书：按环位 0–9 折叠手风琴；0 环标签"0 环 (戏法)"；1–9 环显示格子最大数输入。
  展开后用 TagInput 录入法术名称列表。

### 3.6 背包 Tab（equipment）

物品列表，每行 [名称] [数量步进] [备注] [删除]；底部"添加物品"按钮。

---

## 4 脏数据追踪与导航守卫

- `currentSnapshot`：当前所有表单字段 JSON.stringify 快照（computed）。
- `savedSnapshot`：上次成功保存（或页面初始加载）后的快照（ref）。
- `isDirty = currentSnapshot !== savedSnapshot`。
- 保存按钮：编辑模式下无脏数据时禁用（新建模式始终可用）。
- 页内导航守卫（`onBeforeRouteLeave`）：有脏数据时弹出 `window.confirm`。
- 浏览器 tab 关闭 / 刷新守卫（`beforeunload` 事件）：有脏数据时触发浏览器原生提示。

---

## 5 角色卡列表页

- URL：`/characters`
- 卡片展示：头像（`portrait_asset_id`）、角色名、玩家名、种族 · 职业摘要。
- 职业摘要：读取 `identity.classes`，职业名通过 i18n key `character.classes.*` 翻译为
  当前语言，格式 `战士 3 / 游荡者 2`。
- 悬浮删除按钮；点击卡片跳转编辑页。

---

## 6 权限规则

- 登录用户可创建、读取、编辑、删除**自己**的角色。
- 房间内角色权限由 `game_role`（GM/PL/OB）决定，见 `08_permission_design.md`。

---

## 7 后续扩展

- **CharacterState 实时状态层**：当前 HP / 实时 AC / Buff，与房间对局绑定，分表 / 分 API。
- **CharacterLibraryEntry 房间角色库**：同一角色定义复用生成多个 Token。
- **Token 图片**（`token_image` asset type）：角色 Token，无图时首字渲染。
- 属性 / 技能自动计算规则引擎
- 职业升级向导、法术库联动
- 角色导入 / 导出、模板
- 实时事件：`CHARACTER_CREATED` / `UPDATED` / `DELETED` / `CHARACTER_STATE_CHANGED`

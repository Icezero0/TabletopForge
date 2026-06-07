# TabletopForge 数据库设计

版本：v0.4  
状态：Draft

---

# 1 文档定位

本文档描述 TabletopForge 的核心数据表、字段方向、关系和索引建议。

字段为初始设计，可在实现中根据 ORM 和迁移需求调整。

---

# 2 用户与站点

## 2.1 users

用途：存储系统用户。

核心字段：

```text
id
email
username
hashed_password
avatar_asset_id
site_role
created_at
```

当前后端地基：

- `site_role` 取值为 `user` 或 `admin`。
- `avatar_asset_id` 指向当前头像 asset 的 id，但不建立数据库外键，避免 users 与 assets 形成双向建表依赖。

## 2.2 user_avatar_history

用途：记录用户历史头像，作为用户侧对 avatar asset 的引用。

核心字段：

```text
id
user_id
asset_id
created_at
```

说明：

- `users.avatar_asset_id` 表示当前头像。
- `user_avatar_history.asset_id` 记录用户上传过的头像 asset。
- 切换当前头像不释放旧头像；删除历史头像记录时，才应释放对应 asset 的一次引用。

## 2.3 feedbacks

用途：存储用户反馈。

核心字段：

```text
id
creator_id
handled_by_id
feedback_type
page
title
description
status
admin_note
handled_at
created_at
updated_at
```

反馈图片通过 `assets.feedback_id` 关联。

---

# 3 房间与成员

## 3.1 rooms

用途：存储跑团房间。

核心字段：

```text
id
name
owner_id
visibility
join_audit_mode
created_at
```

## 3.2 room_members

用途：存储用户与房间的成员关系。

核心字段：

```text
room_id
user_id
role          # 文档称 room_role；API 对外字段名 room_role
game_role     # GM | PL | OB，默认 PL
player_color  # 可选，房间内玩家主色（#RRGGBB），用于 Pointer/绘制默认色
joined_at
```

索引建议：

```text
unique(room_id, user_id)
```

`role`（`room_role`）与 `game_role` **独立**，不做隐式绑定。见 `08_permission_design.md` §5。

## 3.3 room_join_requests

用途：存储加入房间申请。

核心字段：

```text
id
room_id
initiator_user_id
target_user_id
source
status
room_action
target_action
room_action_by_user_id
created_at
updated_at
```

## 3.4 room_personal_memos

用途：跑团主界面 **个人备忘录**（按房间、按用户隔离，仅本人可见）。

核心字段：

```text
id
user_id
room_id
content       # Text，默认空串
updated_at
```

索引建议：

```text
unique(user_id, room_id)
```

## 3.5 role_change_requests

用途：存储 room_role 或 game_role 变更申请。

当前后端地基暂未实现该表。管理员设置与解除通过 room member API 直接完成。

核心字段：

```text
id
room_id
user_id
role_type
from_role
to_role
reason
status
reviewed_by
reviewed_at
created_at
updated_at
```

---

# 4 资源库

## 4.1 library_resources

用途：用户个人资源库，按资源类型（`ResourceType`）管理可复用素材。

核心字段：

```text
id
owner_id          # FK → users.id，CASCADE DELETE
type              # ResourceType：map_background | token | sound
name              # 用户命名
primary_asset_id  # FK → assets.id，SET NULL；主文件资产（图片 / 音频）
meta              # JSON，类型附加字段，默认 {}
usage_count       # 业务引用计数；>0 时拒绝删除
created_at
updated_at
```

说明：

- `type` 决定必填字段；当前 `map_background`、`token` 要求图片，`sound` 要求音频。
- `primary_asset_id` 对应 `IMAGE` / `AUDIO` asset，享受 `content_hash` 去重与 `ref_count` 生命周期管理。
- 删除资源时自动递减 `assets.ref_count`；归零则删除物理文件。
- `usage_count` 由业务模块调用 `increment_usage` / `decrement_usage` 维护；当前角色 Token 配置会在引用 `library_resource_id` 时维护该计数。

---

# 5 消息

## 5.1 messages

用途：普通聊天消息。

核心字段：

```text
id
room_id
sender_user_id
content
created_at
updated_at
```

## 5.2 rp_messages

用途：结构化 RP 消息。

核心字段：

```text
id
room_id
character_id
sender_user_id
action_text
speech_text
visibility
created_at
updated_at
```

---

# 6 角色

## 6.1 characters（已实现）

用途：角色卡，按用户所有，存储完整 DnD 5e 角色数据。不绑定房间（用户在多个房间使用同一角色）。

核心字段：

```text
id
owner_id           FK → users.id，CASCADE DELETE
name               VARCHAR(255)，从 identity.name 冗余，方便列表查询
player_name        VARCHAR(255)
kind               VARCHAR(16)，pc_main | pc_additional | npc，默认 pc_main
portrait_asset_id  FK → assets.id，SET NULL（角色卡头像）
token_image_asset_id FK → assets.id，SET NULL（地图 Token 圆图，AssetType.TOKEN_IMAGE）
system             VARCHAR(50)，固定 "dnd5e"
identity           JSON  — 基本信息（种族、职业列表、阵营、图库等）
flavor             JSON  — 扮演设定（性格、理想、羁绊、缺陷、背景故事）
attributes         JSON  — 六维属性、派生属性、豁免、技能、熟练项、语言
features           JSON  — 种族特性、职业特性、自定义字段
spells             JSON NULLABLE — 法术书、施法属性、法术位等
equipment          JSON  — 物品列表
extras             JSON  — 自由备注
created_at
updated_at
```

各 JSON 块的结构详见 `09_module_design/character_card.md` §2。

索引：

```text
ix_characters_id
ix_characters_owner_id
```

## 6.2 character_states（已实现）

用途：角色实时状态层（当前 HP / Buff 等高频变更字段），与 `characters` 1:1。

与 characters 拆分的原因：角色定义稳定，状态层在对局中高频变更，需要单独同步与追溯。

核心字段：

```text
character_id       PK/FK → characters.id，CASCADE DELETE
current_hp         INT NULLABLE
max_hp             INT NULLABLE
temp_hp            INT，默认 0
armor_class        INT NULLABLE
conditions         JSON，默认 {}
damage_taken       INT，默认 0（Phase 4 怪物伤害记录用）
updated_at
```

API：`GET/PATCH /characters/{id}/state`；创建角色（全局或房间库）时自动 bootstrap 默认行。

## 6.3 room_characters（已实现）

用途：房间角色库 — 标记某角色在本房间可用/上场；不复制 `characters` 定义。

```text
id
room_id            FK → rooms.id
character_id       FK → characters.id
kind               VARCHAR(16)，pc_main | pc_additional | npc
added_by_user_id   FK → users.id
created_at
```

API：`GET/POST /rooms/{id}/characters`；`POST /rooms/{id}/characters/link`（关联全局已有 `characters`，幂等，不复制定义）；列表含 character 摘要 + state 摘要。

## 6.4 character_token_configs（已实现）

用途：角色可复用 Token 配置。角色卡稳定层的一部分，用于定义主要 Token、备用 Token 和 Token 面板初始数据。当前已通过角色编辑页 Token Tab 维护。

核心字段：

```text
id
character_id          FK → characters.id，CASCADE DELETE
is_primary            bool，是否主要 Token
name                  VARCHAR(100)
asset_id              FK → assets.id，SET NULL，Token 图片 asset
library_resource_id   FK → library_resources.id，SET NULL，可复用素材引用
panel_initial         JSON，Token 面板初始值（HP/AC/PP/六维/技能/物品等）
sort_order            int
created_at
```

说明：

- 创建/更新角色时可通过 `token_configs` upsert。
- primary config 若缺少 `library_resource_id`，后端会基于 `portrait_asset_id` 自动创建 `library_resources(type=token)` 并写回引用。
- `library_resource_id` 增减时同步维护 `library_resources.usage_count`。
- 当前地图上场 Token 仍主要使用 `characters.token_image_asset_id || portrait_asset_id`；选择具体 token config 上场属于下一步深化。

---

# 7 地图桌面

> **MVP（Step 4）**：扁平 room 表 `room_tabletop_settings`、`room_maps`、`room_drawings`（见 §7.0）。§7.1–7.2 的 `scenes` / `scene_maps` 为后续多场景归档预留。

## 7.0 MVP：room tabletop（已实现中）

### room_tabletop_settings

用途：房间跑团桌面网格尺度（全员一致）。

```text
room_id          PK, FK rooms
grid_cell_ft     float，默认 5
grid_cell_px     int，默认 40
updated_at
```

### room_maps

用途：地图 band 底图（effective z = 0 + z_index）。每房间可多行，由 GM 管理。

```text
id
room_id
asset_id         FK assets（map_background）
x, y, scale
locked
z_index          类内序号
created_at, updated_at
```

### room_drawings

用途：绘制 band（effective z = 200 + z_index）。

```text
id
room_id
kind             brush | line | rect | ellipse | text
geometry         JSON，场景坐标
style            JSON，颜色/线宽/字号等
z_index
created_by_user_id
created_at, updated_at
```

---

## 7.1 scenes（后续，非 MVP）

用途：房间内场景。

核心字段：

```text
id
room_id
name
description
sort_order
created_at
updated_at
```

## 7.2 scene_maps

用途：场景地图配置。

核心字段：

```text
id
scene_id
background_asset_id
width
height
grid_enabled
grid_size
grid_offset_x
grid_offset_y
snap_to_grid
created_at
updated_at
```

## 7.3 tokens

用途：地图上的可操作对象。

**MVP 已落地**：表 `room_tokens`（Alembic `20260606_0007`）；扁平 `room_id`，**无** `scene_id`。API：`POST/PATCH/DELETE /rooms/{id}/tokens`；`POST .../characters/{id}/spawn-token`；快照 `GET /rooms/{id}/tabletop` 含 `tokens`（`state_summary`，按观看者权限展示 HP/AC/PP/伤害信息）；WS `token_created/updated/deleted`、`character_state_updated`（含 GM 全量 summary 与 public summary）。

核心字段：

```text
id
room_id
asset_id              FK → assets.id，nullable
linked_character_id   FK → characters.id，SET NULL
name
token_type
x
y
width
height
rotation
z_index
visible
locked
owner_user_id
created_at
updated_at
```

`z_index` 语义：Token **类内**叠放顺序；渲染时 **effective z = 100 + 类内值**（或持久化为 band 内绝对值 `[100, 199]`）。不得与地图（0）、绘制（200）band 混排。图层菜单只调同类，见 `tabletop_scene.md` §3.2。未来 `drawings` / 多地图实例字段沿用同类 band 规则。

索引建议：

```text
index(room_id)
index(linked_character_id)
```

---

# 8 资源

## 8.1 assets

用途：基础图片资产元信息。

核心字段：

```text
id
asset_type
owner_id
feedback_id
original_filename
storage_path
content_type
size_bytes
content_hash
ref_count
created_at
```

当前已实现的 `asset_type`：

```text
avatar
feedback_image
map_background    # Step 4：房间地图底图；同房间成员可读 content
image
audio
token_image       # 角色/桌面 Token 图片
```

说明：

- 文件二进制存储在 `DATA_DIR/assets` 下。
- 数据库只存储相对路径和元信息。
- `content_hash` 为上传内容的 SHA-256，用于同类型、同大小、同 MIME 的文件去重。
- `ref_count` 记录当前有多少业务对象引用该底层文件；归零后才删除数据库记录和物理文件。
- 当前地基已支持用户资源库中的底层图片 / 音频 asset；地图、Token 等游戏语义层通过 `library_resources` 与业务表引用 asset。

---

# 9 骰子与日志

## 9.1 dice_rolls

用途：骰子记录。

核心字段：

```text
id
room_id
character_id
roller_user_id
expression
result_detail
total
roll_type
visibility
created_at
```

## 9.2 operation_logs

用途：关键操作日志。

核心字段：

```text
id
room_id
operator_user_id
entity_type
entity_id
action_type
before_value
after_value
description
created_at
```

索引建议：

```text
index(room_id, created_at)
index(room_id, action_type)
index(operator_user_id)
index(entity_type, entity_id)
```

---

# 10 数据库设计原则

1. 房间相关数据必须包含 room_id 或可追溯到 room_id。
2. 高频查询字段需要建立索引。
3. 关键业务对象建议软删除。
4. 操作日志不应被普通业务删除。
5. 资源表只存元信息，不直接存储文件二进制。
6. DND5E 字段先满足当前需求，复杂规则后续逐步拆分。

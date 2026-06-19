# TabletopForge HTTP API 设计

版本：v0.4  
状态：Draft（2026-06-19 对齐当前实现）

---

# 1 文档定位

本文档描述 TabletopForge 的 HTTP API 设计原则、路径规范、主要接口分组与权限要求。

详细请求体和响应体可在后续 OpenAPI 文档中维护。

---

# 2 API 设计原则

1. API 路径以资源为中心。
2. 需要持久化的数据变更通过 HTTP API 完成。
3. 所有写操作必须进行后端权限校验。
4. 会触发实时同步的 API 需要在文档中标明 WebSocket 事件。
5. 返回结构保持统一。

---

# 3 基础路径

```text
/api/v1
```

---

# 4 认证 API

```text
POST /auth/register
POST /auth/login
POST /auth/logout
GET  /auth/me
```

---

# 5 用户 API

```text
GET   /users/me
PATCH /users/me
POST  /users/me/avatar
GET   /users/me/avatar-history
GET   /users/me/rooms
GET   /users/me/owned-rooms
GET   /users
GET   /users/{user_id}
PATCH /users/{user_id}/site-role
```

`PATCH /users/{user_id}/site-role` 需要 `manage_site_roles` 站点权限。当前用于由 `admin` 将另一个用户设置为 `admin` 或 `user`。

---

# 6 房间 API

```text
POST   /rooms
GET    /rooms
GET    /rooms/{room_id}
PATCH  /rooms/{room_id}
DELETE /rooms/{room_id}
```

说明：

- `POST /rooms` 支持 `type`，当前取值为 `DND5E` / `ThunderStone`；未传时默认为 `DND5E`。
- `type` 创建后不可修改，`PATCH /rooms/{room_id}` 只修改名称、可见性、入房审核模式等房间基础信息。
- 房间基础层只负责房间、成员、权限、邀请、个人备忘录和 WebSocket 会话。具体游戏内容由房间类型对应的前端模式承载。

---

# 7 成员与审批 API

```text
POST   /rooms/{room_id}/join-requests/apply
POST   /rooms/{room_id}/join-requests/invite
GET    /rooms/{room_id}/join-requests
GET    /join-requests
POST   /join-requests/{request_id}/approve
POST   /join-requests/{request_id}/reject

GET    /rooms/{room_id}/members
PATCH  /rooms/{room_id}/members/{target_user_id}/game-role
PUT    /rooms/{room_id}/members/{target_user_id}/manager
DELETE /rooms/{room_id}/members/{target_user_id}/manager
DELETE /rooms/{room_id}/members/{target_user_id}
DELETE /rooms/{room_id}/members/me

GET    /rooms/{room_id}/personal-memo
PUT    /rooms/{room_id}/personal-memo

GET    /rooms/{room_id}/tabletop
GET    /rooms/{room_id}/scenes
POST   /rooms/{room_id}/scenes
GET    /rooms/{room_id}/scenes/{scene_id}
PATCH  /rooms/{room_id}/scenes/{scene_id}
POST   /rooms/{room_id}/scenes/{scene_id}/snapshot
POST   /rooms/{room_id}/scenes/{scene_id}/activate
DELETE /rooms/{room_id}/scenes/{scene_id}
PATCH  /rooms/{room_id}/tabletop/settings
POST   /rooms/{room_id}/maps
POST   /rooms/{room_id}/maps/from-resource
PATCH  /rooms/{room_id}/maps/{map_id}
DELETE /rooms/{room_id}/maps/{map_id}
POST   /rooms/{room_id}/drawings
PATCH  /rooms/{room_id}/drawings/{drawing_id}
DELETE /rooms/{room_id}/drawings
POST   /rooms/{room_id}/tokens
PATCH  /rooms/{room_id}/tokens/{token_id}
DELETE /rooms/{room_id}/tokens/{token_id}
GET    /rooms/{room_id}/characters
POST   /rooms/{room_id}/characters
POST   /rooms/{room_id}/characters/link
DELETE /rooms/{room_id}/characters/{room_character_id}
PATCH  /rooms/{room_id}/characters/{room_character_id}/visibility
PATCH  /rooms/{room_id}/characters/{room_character_id}/data-visibility
POST   /rooms/{room_id}/characters/{character_id}/spawn-token
```

**个人备忘录**（`room_personal_memos`）：仅当前登录用户读写本人在该房间的记录；须为房间成员，否则 `403`。不通过 WebSocket 同步。

请求/响应示例：

```json
{ "content": "session notes…" }
```

```json
{ "content": "session notes…", "updated_at": "2026-06-04T12:00:00Z" }
```

成员响应字段（`room_members`）：

```json
{
  "room_id": 1,
  "user_id": 2,
  "room_role": "member",
  "game_role": "PL",
  "joined_at": "...",
  "user": { }
}
```

- `room_role`：治理身份（DB 列 `role`）。
- `game_role`：跑团身份，与 `room_role` 正交。
- `POST /rooms` 请求体可选 `creator_game_role`（默认 `GM`）；入房落成员默认 `game_role=PL`。
- `PATCH .../game-role` 请求体 `{ "game_role": "GM" }`，需 `MANAGE_MEMBERS`。

可能触发事件：

- `room_members`
- `notification`
- `session_closed`

---

# 8 普通消息 API

```text
POST /messages/rooms/{room_id}
GET  /messages/rooms/{room_id}
```

触发事件：

- `message`

---

# 9 RP 消息 API

```text
POST /rooms/{room_id}/rp-messages
GET  /rooms/{room_id}/rp-messages
```

触发事件：

- 后续实现 RP 消息后定义。

---

# 10 角色 API（已实现）

角色按用户所有，不绑定房间（用户在多个房间使用同一角色）。

```text
GET    /characters                  # 分页列出当前用户的角色
POST   /characters                  # 创建角色
GET    /characters/{character_id}   # 获取单个角色
PATCH  /characters/{character_id}   # 更新角色（仅 owner 可操作）
DELETE /characters/{character_id}   # 删除角色（仅 owner 可操作）
```

说明：

- `GET /characters` 支持分页参数 `page` / `page_size`，仅返回当前用户的角色。
- `POST /characters` / `PATCH` 请求体包含 `name`、`system`、`portrait_asset_id`、
  `token_image_asset_id`、`identity`、`flavor`、`attributes`、`features`、`spells`、
  `resources`、`equipment`、`extras`、`token_configs` 等字段。
- 主要指示物不再由用户手动维护 `token_configs`：后端会为角色维护 `primary_token_resource_id`，
  并根据角色卡名称、头像与面板数据派生主要指示物。角色头像或 token 图像变化时，主要资源库 token 会同步更新。
- `token_configs` 只用于次要指示物配置，支持 `name`、`asset_id`、`library_resource_id`、
  `panel_initial`、`sort_order`。次要指示物仍可绑定资源库 token。
- `resources` 是角色卡资源列表，包含名称、上限、恢复方式、备注等 UI 需要字段。资源可从职业等级自动计算通用资源，再同步到指示物配置/room token 快照。
- `PATCH` 仅更新请求体中显式包含的字段（`model_fields_set`），允许传 `null` 清空可空字段
  （`portrait_asset_id`、`spells`）而不影响其他字段。
- 权限：需登录；全局角色写操作仅限 `owner_id == current_user.id`；已加入房间的角色可被房间成员按 `game_role` 读取状态摘要。

---

# 11 角色状态 API（已实现）

```text
GET   /characters/{character_id}/state
PATCH /characters/{character_id}/state
```

说明：

- 角色创建时自动 bootstrap `character_states`。
- owner 可编辑自己的角色状态；GM 可编辑房间内任意角色状态。
- 隐藏数据由房间角色与 room token 面板控制。隐藏数据开启时，非 GM 视角会遮盖面板数据；累计伤害由 `max_hp - current_hp` 在前端计算展示。

触发事件：

- `character_state_updated`

---

# 12 DND5E 跑团桌面 API（已实现）

这些接口服务当前 DND5E 房间模式。ThunderStone 房间类型不会直接复用 DND5E 桌面模型。

```text
GET    /rooms/{room_id}/tabletop
PATCH  /rooms/{room_id}/tabletop/settings
POST   /rooms/{room_id}/maps              # multipart: file=图片, name?, comment?
POST   /rooms/{room_id}/maps/from-resource
PATCH  /rooms/{room_id}/maps/{map_id}
DELETE /rooms/{room_id}/maps/{map_id}
POST   /rooms/{room_id}/drawings
PATCH  /rooms/{room_id}/drawings/{drawing_id}
DELETE /rooms/{room_id}/drawings          # body: { "ids": [1, 2] }
POST   /rooms/{room_id}/tokens
PATCH  /rooms/{room_id}/tokens/{token_id}
DELETE /rooms/{room_id}/tokens/{token_id}
POST   /rooms/{room_id}/characters/{character_id}/spawn-token
```

权限（`game_role`，见 `08` §6.4）：

| 操作 | GM | PL | OB |
|---|---|---|---|
| GET tabletop | ✓ | ✓ | ✓ |
| PATCH settings（grid/combat/music/fog） | ✓ | 当前回合角色 owner 可提交合法结束回合状态 | — |
| POST/PATCH/DELETE maps | ✓ | — | — |
| POST/PATCH drawings | ✓ | ✓ | — |
| DELETE drawings（含批量） | ✓ | ✓ | — |
| POST/PATCH/DELETE tokens | ✓ | 自己拥有/绑定的指示物 | — |
| spawn character token | ✓ | 自己拥有的角色 | — |

`GET /tabletop` 响应：`settings`、`maps[]`、`drawings[]`、`tokens[]` 快照。

`settings` 当前包含：

- `grid_cell_ft` / `grid_cell_px`
- `combat_state`
- `music_state`
- `fog_state`

`POST /maps`：上传地图图片并创建资源库地图资源，再创建 `room_maps` 行。  
`POST /maps/from-resource`：从现有 `library_resources(type=map_background)` 创建房间地图实例。删除地图时会清理该地图对应的战争迷雾 mask。

指示物头像来源是资源库 token。资源库 token 被删除或不可读时，前端回退到名称首字头像。

触发 WS 事件：`tabletop_settings_updated`、`map_created`、`map_updated`、`map_deleted`、`drawing_created`、`drawing_updated`、`drawing_deleted`、`token_created`、`token_updated`、`token_deleted`、`character_state_updated`、`room_character_updated`（见 `06_websocket_protocol.md`）。

---

## 12.1 场景 API（已实现）

场景是 DND5E 房间桌面状态的快照容器。切换场景时，当前 tabletop 会先保存到当前场景，再载入目标场景快照。掷骰日志也按当前场景归属，删除场景时其关联掷骰记录随之删除。

```text
GET    /rooms/{room_id}/scenes
POST   /rooms/{room_id}/scenes
GET    /rooms/{room_id}/scenes/{scene_id}
PATCH  /rooms/{room_id}/scenes/{scene_id}
POST   /rooms/{room_id}/scenes/{scene_id}/snapshot
POST   /rooms/{room_id}/scenes/{scene_id}/activate
DELETE /rooms/{room_id}/scenes/{scene_id}
```

- 创建场景会创建空场景，而不是复制当前 tabletop。
- `snapshot` 手动保存当前 tabletop 到指定场景。
- `activate` 切换当前场景，并触发 `tabletop_snapshot_replaced` 与 `room_characters`。
- 现有房间迁移后应至少有默认场景承接原 tabletop 状态。

---

# 13 房间角色 API（已实现）

房间角色是角色卡在房间内的可见性、隐藏数据状态与上场入口。角色卡本身仍归属用户角色库。

```text
GET    /rooms/{room_id}/characters
POST   /rooms/{room_id}/characters
POST   /rooms/{room_id}/characters/link
DELETE /rooms/{room_id}/characters/{room_character_id}
PATCH  /rooms/{room_id}/characters/{room_character_id}/visibility
PATCH  /rooms/{room_id}/characters/{room_character_id}/data-visibility
POST   /rooms/{room_id}/characters/{character_id}/spawn-token
```

说明：

- `POST /rooms/{room_id}/characters` 是房间内快速创建角色入口，支持上传头像文件和 JSON 字段。
- `POST /characters/link` 将当前用户角色库中的角色加入房间。
- `visibility` 控制角色在房间角色列表和关联指示物中的隐藏表现。
- `data-visibility` 控制角色信息面板隐藏数据；由该角色生成的指示物默认继承隐藏数据状态，但单个 room token 仍可单独调整。
- `spawn-token` 从角色卡/次要指示物配置生成 room token。主要指示物由角色卡名称、头像和面板数据派生，并使用角色绑定的主要资源库 token。

触发事件：

- `room_characters`
- `token_created`
- `token_deleted`

---

# 14 Asset API

当前后端已实现基础资产与部分业务资产：

- `avatar`：用户头像。
- `feedback_image`：反馈图片。
- `image`：用户资源库中的通用图片。
- `audio`：用户资源库中的通用音频。
- `map_background`：房间地图底图。
- `token_image`：指示物头像图片。

```text
POST   /assets
GET    /assets
GET    /assets/{asset_id}
GET    /assets/{asset_id}/content
DELETE /assets/{asset_id}
POST   /users/me/avatar
GET    /users/me/avatar-history
POST   /feedback
```

说明：

- `POST /assets` 以 multipart 上传用户资源库 `image` / `audio`；后端按 SHA-256、大小、MIME 与类型去重，命中已有文件时复用 asset 并增加 `ref_count`。
- `GET /assets` 分页列出用户资源库 asset，可按 `asset_type=image|audio` 过滤。
- `GET /assets/{asset_id}` 返回 asset 元数据。
- `DELETE /assets/{asset_id}` 释放一次用户资源库 asset 引用；`ref_count` 归零后才删除元数据和文件。
- `POST /users/me/avatar` 以 multipart 上传头像图片；后端按 SHA-256、大小、MIME 与类型去重，命中已有头像文件时复用 asset 并增加 `ref_count`。
- `GET /users/me/avatar-history` 分页返回当前用户的历史头像记录。当前头像仍由 `users.avatar_asset_id` 表示，历史记录作为用户侧对 avatar asset 的引用。
- `POST /feedback` 可通过 multipart 字段 `images` 上传反馈图片。
- `GET /assets/{asset_id}/content` 返回文件内容。
- avatar 公开可读；feedback_image 仅提交者和具备查看全部反馈权限的 admin 可读；image/audio 公开可读，供共同游戏使用。

---

# 15 资源库 API

个人资源库（`library_resources`）。资源类型由 `type` 字段决定字段要求；
当前实现：`map_background`、`token`、`sound`。

```text
GET    /library/resources
POST   /library/resources
GET    /library/resources/{resource_id}
PATCH  /library/resources/{resource_id}
DELETE /library/resources/{resource_id}
```

说明：

- `GET /library/resources`：分页列出当前用户的资源，支持 `?type=map_background|token|sound`。
- `POST /library/resources`：multipart 创建资源；通用字段 `type`、`name`；
  `map_background` / `token` 类型需附带 `image` 文件字段，`sound` 类型需附带 `audio` 文件字段（享受 hash 去重）。
- `PATCH /library/resources/{id}`：仅限改名（`name` 字段），仅所有者可操作。
- `DELETE /library/resources/{id}`：`usage_count > 0` 时返回 409（桌面上有引用）；
  删除成功后自动递减 `assets.ref_count`，归零则清理物理文件。

权限：所有端点需登录，且仅所有者可读写本人资源。

---

# 16 骰子 API（已实现）

```text
POST /rooms/{room_id}/dice-rolls
GET  /rooms/{room_id}/dice-rolls
```

`POST /rooms/{room_id}/dice-rolls` 请求体：

```json
{
  "actor_type": "user",
  "actor_token_id": null,
  "label": "",
  "formula": "d20+3",
  "visibility": "public"
}
```

说明：

- `actor_type` 为 `user` 或 `token`。选择 token 作为主体时，会在日志中保存 token 当时的显示名与头像资产。
- `visibility` 为 `public` / `blind`。暗骰仅 GM 收到完整结果；非 GM 不应看到该暗骰记录。
- 掷骰记录绑定当前 `scene_id`。`GET` 支持 `scene_id`、`before_id`、`limit`，默认一页 30 条，最大 100 条。
- 公式由底层 dice engine 解析；DND5E 的检定、豁免、技能、先攻等语义由上层 UI 生成公式和标签。

触发事件：

- `dice_roll`

---

# 17 掷骰预设 API（已实现）

```text
GET    /dice-presets
POST   /dice-presets
PATCH  /dice-presets/{preset_id}
DELETE /dice-presets/{preset_id}
```

说明：

- 掷骰预设归当前用户所有。
- 预设支持树形分组：`kind=folder` 表示分组，`kind=preset` 表示实际预设。
- 预设字段包括 `name`、`parent_id`、`formula`、`label`、`visibility`、`sort_order`。
- 删除分组时会删除其子级预设/分组。

---

# 18 操作日志 API（规划）

```text
GET /rooms/{room_id}/operation-logs
```

支持查询条件：

- action_type
- character_id
- operator_user_id
- from_time
- to_time

---

# 19 反馈 API

```text
POST /feedback
GET  /feedback
GET  /feedback/{feedback_id}
GET  /feedback/admin
PATCH /feedback/admin/{feedback_id}
```

管理接口需要 site 权限。

---

# 20 错误返回

建议统一错误结构：

```json
{
  "error": {
    "reason": "ROOM_NOT_FOUND",
    "message": "Room not found",
    "details": {}
  }
}
```

reason 应稳定，用于前端判断错误类型。

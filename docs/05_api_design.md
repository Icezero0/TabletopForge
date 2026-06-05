# TabletopForge HTTP API 设计

版本：v0.2  
状态：Draft

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
PATCH  /rooms/{room_id}/tabletop/settings
POST   /rooms/{room_id}/maps
PATCH  /rooms/{room_id}/maps/{map_id}
DELETE /rooms/{room_id}/maps/{map_id}
POST   /rooms/{room_id}/drawings
PATCH  /rooms/{room_id}/drawings/{drawing_id}
DELETE /rooms/{room_id}/drawings
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
- `POST /characters` / `PATCH` 请求体包含 `name`、`system`、`portrait_asset_id`、`identity`、
  `flavor`、`attributes`、`features`、`spells`、`equipment`、`extras` 等字段。
- `PATCH` 仅更新请求体中显式包含的字段（`model_fields_set`），允许传 `null` 清空可空字段
  （`portrait_asset_id`、`spells`）而不影响其他字段。
- 权限：需登录；写操作仅限 `owner_id == current_user.id`。

---

# 11 角色状态 API（未落地，规划态）

```text
GET   /characters/{character_id}/state
PATCH /characters/{character_id}/state
POST  /characters/{character_id}/hp-change
POST  /characters/{character_id}/effects
DELETE /characters/{character_id}/effects/{effect_id}
```

触发事件：

- 后续实现 CharacterState 层时定义。

---

# 12 跑团桌面 Tabletop API（MVP，扁平 room 模型）

> Campaign / Session / Scene 多场景 API 见下文「后续」；MVP 以房间为边界，见 `working-note/04-map-core.md`。

```text
GET    /rooms/{room_id}/tabletop
PATCH  /rooms/{room_id}/tabletop/settings
POST   /rooms/{room_id}/maps              # multipart: file=图片
PATCH  /rooms/{room_id}/maps/{map_id}
DELETE /rooms/{room_id}/maps/{map_id}
POST   /rooms/{room_id}/drawings
PATCH  /rooms/{room_id}/drawings/{drawing_id}
DELETE /rooms/{room_id}/drawings          # body: { "ids": [1, 2] }
```

权限（`game_role`，见 `08` §6.4）：

| 操作 | GM | PL | OB |
|---|---|---|---|
| GET tabletop | ✓ | ✓ | ✓ |
| PATCH settings（grid_cell_ft/px） | ✓ | — | — |
| POST/PATCH/DELETE maps | ✓ | — | — |
| POST/PATCH drawings | ✓ | ✓ | — |
| DELETE drawings（含批量） | ✓ | ✓ | — |

`GET /tabletop` 响应：`settings`、`maps[]`、`drawings[]` 快照。

`POST /maps`：上传 `map_background` asset 并创建 `room_maps` 行；MVP **每房间至多 1 张底图**。

触发 WS 事件：`map_created`、`map_updated`、`map_deleted`、`drawing_created`、`drawing_updated`、`drawing_deleted`、`tabletop_settings_updated`（见 `06_websocket_protocol.md`）。

---

## 12.1 后续：场景与地图 API（非 MVP）

```text
POST   /rooms/{room_id}/scenes
GET    /rooms/{room_id}/scenes
GET    /scenes/{scene_id}
PATCH  /scenes/{scene_id}
DELETE /scenes/{scene_id}
POST   /rooms/{room_id}/current-scene
PATCH  /scenes/{scene_id}/map
```

实现 Campaign/Session/Scene 归档后再定义。

---

# 13 Token API

```text
POST   /scenes/{scene_id}/tokens
GET    /scenes/{scene_id}/tokens
GET    /tokens/{token_id}
PATCH  /tokens/{token_id}
DELETE /tokens/{token_id}
```

常见 PATCH 操作：

- 移动
- 缩放
- 旋转
- 锁定
- 隐藏
- 绑定角色

触发事件：

- 后续实现 Token 模块后定义。

---

# 14 Asset API

当前后端地基只实现与业务无关的基础图片资产：

- `avatar`：用户头像。
- `feedback_image`：反馈图片。
- `image`：用户资源库中的通用图片。
- `audio`：用户资源库中的通用音频。

地图、Token、handout 等游戏语义层用途后续在业务模块落地时再扩展。

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
当前实现：`map_background`（必须上传图片）。

```text
GET    /library/resources
POST   /library/resources
GET    /library/resources/{resource_id}
PATCH  /library/resources/{resource_id}
DELETE /library/resources/{resource_id}
```

说明：

- `GET /library/resources`：分页列出当前用户的资源，支持 `?type=map_background`。
- `POST /library/resources`：multipart 创建资源；通用字段 `type`、`name`；
  `map_background` 类型需附带 `image` 文件字段，写入 `IMAGE` 类型 asset（享受 hash 去重）。
- `PATCH /library/resources/{id}`：仅限改名（`name` 字段），仅所有者可操作。
- `DELETE /library/resources/{id}`：`usage_count > 0` 时返回 409（桌面上有引用）；
  删除成功后自动递减 `assets.ref_count`，归零则清理物理文件。

权限：所有端点需登录，且仅所有者可读写本人资源。

---

# 16 骰子 API

```text
POST /rooms/{room_id}/dice-rolls
GET  /rooms/{room_id}/dice-rolls
```

触发事件：

- 后续实现骰子模块后定义。

---

# 16 操作日志 API

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

# 17 反馈 API

```text
POST /feedback
GET  /feedback
GET  /feedback/{feedback_id}
GET  /feedback/admin
PATCH /feedback/admin/{feedback_id}
```

管理接口需要 site 权限。

---

# 18 错误返回

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

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

# 10 角色 API

```text
POST   /rooms/{room_id}/characters
GET    /rooms/{room_id}/characters
GET    /characters/{character_id}
PATCH  /characters/{character_id}
DELETE /characters/{character_id}
```

触发事件：

- 后续实现角色模块后定义。

---

# 11 角色状态 API

```text
GET   /characters/{character_id}/state
PATCH /characters/{character_id}/state
POST  /characters/{character_id}/hp-change
POST  /characters/{character_id}/effects
DELETE /characters/{character_id}/effects/{effect_id}
POST  /characters/{character_id}/resources/{resource_id}/change
```

触发事件：

- 后续实现角色状态和操作日志模块后定义。

---

# 12 场景与地图 API

```text
POST   /rooms/{room_id}/scenes
GET    /rooms/{room_id}/scenes
GET    /scenes/{scene_id}
PATCH  /scenes/{scene_id}
DELETE /scenes/{scene_id}
POST   /rooms/{room_id}/current-scene

PATCH  /scenes/{scene_id}/map
```

触发事件：

- 后续实现场景地图模块后定义。

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

# 15 骰子 API

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

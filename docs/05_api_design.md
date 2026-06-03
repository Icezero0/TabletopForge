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
GET   /users/{user_id}
```

站点管理接口：

```text
GET   /admin/users
PATCH /admin/users/{user_id}
```

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
POST /rooms/{room_id}/join-requests
GET  /rooms/{room_id}/join-requests
POST /rooms/{room_id}/join-requests/{request_id}/approve
POST /rooms/{room_id}/join-requests/{request_id}/reject

GET    /rooms/{room_id}/members
PATCH  /rooms/{room_id}/members/{member_id}/room-role
PATCH  /rooms/{room_id}/members/{member_id}/game-role
DELETE /rooms/{room_id}/members/{member_id}
```

可能触发事件：

- ROOM_MEMBER_JOINED
- ROOM_MEMBER_REMOVED
- ROOM_MEMBER_ROLE_CHANGED

---

# 8 普通消息 API

```text
POST /rooms/{room_id}/messages
GET  /rooms/{room_id}/messages
```

触发事件：

- CHAT_MESSAGE_CREATED

---

# 9 RP 消息 API

```text
POST /rooms/{room_id}/rp-messages
GET  /rooms/{room_id}/rp-messages
```

触发事件：

- RP_MESSAGE_CREATED

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

- CHARACTER_CREATED
- CHARACTER_UPDATED
- CHARACTER_DELETED

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

- CHARACTER_STATE_CHANGED
- CHARACTER_HP_CHANGED
- CHARACTER_EFFECT_ADDED
- CHARACTER_EFFECT_REMOVED
- CHARACTER_RESOURCE_CHANGED
- OPERATION_LOG_CREATED

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

- SCENE_CREATED
- SCENE_UPDATED
- SCENE_CHANGED
- MAP_UPDATED

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

- TOKEN_CREATED
- TOKEN_MOVED
- TOKEN_UPDATED
- TOKEN_DELETED

---

# 14 资源 API

```text
POST   /assets
GET    /assets
GET    /rooms/{room_id}/assets
PATCH  /assets/{asset_id}
DELETE /assets/{asset_id}
```

触发事件：

- ASSET_CREATED
- ASSET_UPDATED
- ASSET_DELETED

---

# 15 骰子 API

```text
POST /rooms/{room_id}/dice-rolls
GET  /rooms/{room_id}/dice-rolls
```

触发事件：

- DICE_ROLLED

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
GET  /admin/feedback
GET  /admin/feedback/{feedback_id}
PATCH /admin/feedback/{feedback_id}
```

管理接口需要 site_role 权限。

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

# TabletopForge WebSocket 协议设计

版本：v0.3  
状态：Draft（2026-06-19 已补当前实现摘要）

---

# 1 文档定位

本文档描述 TabletopForge 的 WebSocket 连接方式、消息结构、频道模型、基础消息类型与业务事件。

---

# 2 使用场景

WebSocket 用于房间内实时事件同步，包括：

- 成员在线状态
- 普通聊天
- 角色状态变化
- 场景切换
- Token 移动
- 骰子结果
- Pointer / 对象占用
- DND5E tabletop 状态同步

RP 消息、操作日志仍属于后续方向。

---

# 3 连接方式

```text
/ws
```

客户端建立连接后需要进行认证。

---

# 4 基础消息类型

```text
AUTH
HEARTBEAT
COMMAND
EVENT
ACK
ERROR
```

## 4.1 AUTH

客户端发送认证信息。

```json
{
  "type": "AUTH",
  "token": "jwt-token"
}
```

## 4.2 HEARTBEAT

心跳消息。

```json
{
  "type": "HEARTBEAT",
  "ts": 1710000000
}
```

## 4.3 EVENT

服务端广播事件。

```json
{
  "type": "EVENT",
  "event": "TOKEN_MOVED",
  "payload": {}
}
```

## 4.4 ACK

确认客户端 command 或服务端处理结果。

## 4.5 ERROR

错误消息。

---

# 5 频道模型

## 5.1 USER channel

用于用户级通知，例如审批结果、系统通知。

## 5.2 ROOM channel

用于房间内广播，例如消息、Token、角色状态。

---

# 6 业务事件

当前后端已实现的主要事件类型为：

```text
notification
room_info
room_members
room_user_presence
session_closed
message
dice_roll
room_characters
tabletop_settings_updated
tabletop_snapshot_replaced
map_created
map_updated
map_deleted
drawing_created
drawing_updated
drawing_deleted
token_created
token_updated
token_deleted
token_transform_preview
character_state_updated
room_character_updated
pointer_presence
pointer_laser
object_selection
```

前端当前拆分为：

```text
useRoomRealtimeSession      # 房间基础事件
useTabletopRealtimeEvents   # DND5E/tabletop 专用事件
```

## 6.1 房间成员事件

```text
room_members
room_user_presence
session_closed
```

## 6.2 消息事件

```text
message
```

## 6.3 角色事件

```text
room_characters
character_state_updated
room_character_updated
```

## 6.4 跑团桌面 Tabletop 事件（MVP）

房间频道广播；payload 含 `room_id`，变更类事件含实体快照字段。

```text
tabletop_settings_updated
tabletop_snapshot_replaced
map_created
map_updated
map_deleted
drawing_created
drawing_updated
drawing_deleted
token_created
token_updated
token_deleted
token_transform_preview
pointer_presence
pointer_laser
object_selection
```

**Pointer COMMAND**（须已 `room_enter`；发送方 `game_role` 为 GM/PL；OB 仅接收）：

```text
pointer_presence   # data: { room_id, x, y } 场景坐标
pointer_laser      # data: { room_id, active, x, y }；前端本地渲染 fading trail
```

**Pointer EVENT**（广播）：

```json
{
  "event": "pointer_presence",
  "data": {
    "room_id": 1,
    "user_id": 2,
    "display_name": "Alice",
    "x": 120.5,
    "y": 340.0
  }
}
```

```json
{
  "event": "pointer_laser",
  "data": {
    "room_id": 1,
    "user_id": 2,
    "display_name": "Alice",
    "active": true,
    "x": 80,
    "y": 60
  }
}
```

示例（`map_created`）：

```json
{
  "type": "EVENT",
  "event": "map_created",
  "payload": {
    "room_id": 1,
    "map": {
      "id": 10,
      "asset_id": 42,
      "x": 0,
      "y": 0,
      "scale": 1,
      "locked": false,
      "z_index": 0
    }
  }
}
```

## 6.5 场景归档事件

```text
tabletop_snapshot_replaced
```

场景自身 CRUD 当前主要通过 HTTP 完成；切换场景后以 `tabletop_snapshot_replaced` 通知各端重载快照。

## 6.6 Token / 对象占用事件

```text
token_created
token_updated
token_deleted
token_transform_preview
object_selection
```

说明：

- `token_transform_preview` 用于拖拽中实时预览，不通过 HTTP 高频提交。
- `object_selection` 用于对象占用/释放提示，避免拖拽竞争；只读查看信息不应被占用阻塞。

## 6.7 骰子事件

```text
dice_roll
```

掷骰写入 `room_dice_rolls` 后广播；前端按当前 active scene 过滤。

## 6.8 日志事件

```text
OPERATION_LOG_CREATED
```

尚未落地。

## 6.9 战斗事件

```text
tabletop_settings_updated
```

当前战斗状态存储在 `room_tabletop_settings.combat_state`，通过 tabletop settings 更新广播同步。尚未拆出独立 combat event。

---

# 7 示例事件

## 7.1 Token 移动

```json
{
  "type": "EVENT",
  "event": "TOKEN_MOVED",
  "payload": {
    "room_id": "room_001",
    "scene_id": "scene_001",
    "token_id": "token_001",
    "x": 120,
    "y": 240,
    "updated_by": "user_001"
  }
}
```

## 7.2 角色 HP 变化

```json
{
  "type": "EVENT",
  "event": "CHARACTER_HP_CHANGED",
  "payload": {
    "room_id": "room_001",
    "character_id": "char_001",
    "old_hp": 20,
    "new_hp": 13,
    "delta": -7,
    "reason": "damage"
  }
}
```

## 7.3 RP 消息

```json
{
  "type": "EVENT",
  "event": "RP_MESSAGE_CREATED",
  "payload": {
    "room_id": "room_001",
    "message_id": "rp_001",
    "character_id": "char_001",
    "action_text": "墨尔赫拔出剑，面对着狼群。",
    "speech_text": "小心，这群狼很危险。"
  }
}
```

---

# 8 前端处理原则

1. WebSocket 事件应统一分发处理。
2. 服务端事件是最终状态来源。
3. Token 拖拽等交互可以进行临时视觉更新。
4. 断线重连后应通过 HTTP 重新拉取房间当前状态。
5. 重复事件应具备幂等处理能力。

---

# 9 服务端处理原则

1. WebSocket 广播服务端确认后的事件。
2. 不依赖客户端自报权限。
3. 需要持久化的 command 必须进入业务服务层。
4. 广播事件应包含足够的 room_id / scene_id / entity_id。
5. 敏感事件需要根据可见性过滤接收者。

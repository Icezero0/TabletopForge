# TabletopForge WebSocket 协议设计

版本：v0.2  
状态：Draft

---

# 1 文档定位

本文档描述 TabletopForge 的 WebSocket 连接方式、消息结构、频道模型、基础消息类型与业务事件。

---

# 2 使用场景

WebSocket 用于房间内实时事件同步，包括：

- 成员在线状态
- 普通聊天
- RP 消息
- 角色状态变化
- 场景切换
- Token 移动
- 骰子结果
- 操作日志

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

当前后端地基已实现的事件类型为：

```text
notification
room_info
room_members
room_user_presence
session_closed
message
```

下面列出的角色、场景、Token、骰子、日志、战斗事件属于后续业务模块扩展方向。

## 6.1 房间成员事件

```text
room_members
session_closed
```

## 6.2 消息事件

```text
message
```

## 6.3 角色事件

```text
CHARACTER_CREATED
CHARACTER_UPDATED
CHARACTER_DELETED
CHARACTER_STATE_CHANGED
CHARACTER_HP_CHANGED
CHARACTER_RESOURCE_CHANGED
CHARACTER_EFFECT_ADDED
CHARACTER_EFFECT_REMOVED
```

## 6.4 场景地图事件

```text
SCENE_CREATED
SCENE_UPDATED
SCENE_CHANGED
MAP_UPDATED
```

## 6.5 Token 事件

```text
TOKEN_CREATED
TOKEN_MOVED
TOKEN_UPDATED
TOKEN_DELETED
```

## 6.6 骰子事件

```text
DICE_ROLLED
```

## 6.7 日志事件

```text
OPERATION_LOG_CREATED
```

## 6.8 战斗事件

```text
COMBAT_STARTED
COMBAT_ENDED
TURN_CHANGED
ROUND_CHANGED
```

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

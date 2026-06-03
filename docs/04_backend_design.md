# TabletopForge 后端设计

版本：v0.2  
状态：Draft

---

# 1 文档定位

本文档描述 TabletopForge 后端的模块结构、分层方式、服务边界、权限校验、事务与日志原则。

---

# 2 后端职责

后端负责：

- 用户认证
- 用户资料管理
- 房间管理
- 成员关系与审批
- 权限校验
- 消息持久化
- RP 消息持久化
- 角色卡与状态管理
- 场景、地图、Token 管理
- 资源元信息管理
- 骰子计算与记录
- 操作日志
- WebSocket 实时广播

---

# 3 推荐目录结构

```text
app/
├── core/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── exceptions.py
│   └── pagination.py
├── auth/
├── users/
├── rooms/
├── members/
├── approvals/
├── permissions/
├── messages/
├── rp_messages/
├── characters/
├── character_states/
├── rulesets/
├── dice/
├── assets/
├── scenes/
├── maps/
├── tokens/
├── operation_logs/
├── feedback/
└── realtime/
```

---

# 4 模块分层

每个业务模块内部建议采用：

```text
router
service
repository
models
schemas
```

## 4.1 router

负责 HTTP 接口定义、请求参数接收和响应返回。

不应包含复杂业务逻辑。

## 4.2 service

负责业务规则、权限校验、事务编排、日志生成和事件发布。

service 是业务逻辑主要承载层。

## 4.3 repository

负责数据库访问。

不应包含权限判断和复杂业务规则。

## 4.4 models

负责 ORM 数据模型。

## 4.5 schemas

负责请求和响应结构。

---

# 5 权限校验

权限校验应在 service 层或 permission service 中完成。

推荐按权限域拆分：

- site permission
- room permission
- game permission

示例：

```text
check_site_permission(user, permission)
check_room_permission(user, room_id, permission)
check_game_permission(user, room_id, permission)
```

---

# 6 事务原则

以下操作应在同一事务中完成：

- 修改角色状态 + 写操作日志
- 创建 Token + 写操作日志
- 切换场景 + 写操作日志
- 审批成员 + 创建成员关系
- 掷骰 + 写骰子记录

事务提交后再发布 WebSocket 事件。

---

# 7 操作日志原则

关键业务操作需要记录日志，包括：

- 角色 HP 变化
- 角色资源变化
- 状态效果变化
- Token 创建、移动、删除
- 场景切换
- 身份变化
- 骰子结果

日志记录应尽量由 service 层统一触发。

---

# 8 WebSocket 事件发布

服务层在业务操作成功后发布事件。

推荐流程：

```text
Service 完成业务操作
-> Commit transaction
-> Build event payload
-> Realtime publisher 发布事件
```

事件发布失败不应导致已提交的核心业务数据回滚，但需要记录错误。

---

# 9 命名约定

推荐沿用统一命名风格：

- `find_xxx`：查找单个对象，查不到返回 None
- `get_xxx`：获取单个对象，查不到抛 NotFoundError
- `get_xxxs`：列表或分页查询
- `create_xxx`：创建
- `update_xxx`：更新
- `delete_xxx`：删除或软删除

示例：

```text
find_room_by_id
get_room_by_id
get_rooms
find_character_by_id
get_character_by_id
get_characters
```

---

# 10 业务模块边界

## 10.1 rooms

只负责房间基础信息与房间生命周期。

## 10.2 members

负责房间成员关系和 room_role / game_role。

## 10.3 characters

负责角色卡基础信息。

## 10.4 character_states

负责角色当前状态和高频状态修改。

## 10.5 scenes / maps / tokens

负责地图桌面相关数据。

## 10.6 dice

负责骰子表达式解析、计算和记录。

## 10.7 operation_logs

负责操作日志写入和查询。

---

# 11 后端设计原则

1. router 保持薄层。
2. service 承载业务逻辑。
3. repository 只处理数据访问。
4. 权限校验不可只依赖前端。
5. 关键状态变化必须写日志。
6. WebSocket 广播服务端确认后的事件。
7. 跨模块调用优先通过 service，不直接访问其他模块 repository。

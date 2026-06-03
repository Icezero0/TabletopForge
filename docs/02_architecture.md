# TabletopForge 系统架构设计

版本：v0.2  
状态：Draft

---

# 1 文档定位

本文档描述 TabletopForge 的系统架构、模块划分、数据流、通信方式与扩展原则。

---

# 2 架构风格

系统采用前后端分离架构与模块化单体后端。

选择模块化单体的原因：

- 当前业务规模适合单体部署
- 模块边界清楚即可满足开发需求
- 事务和权限校验更容易集中管理
- 部署成本低，适合单 VPS 或小规模部署

---

# 3 系统结构

```text
Client Browser
  ├─ HTTP API
  └─ WebSocket
        ↓
Backend Application
  ├─ API Routers
  ├─ Services
  ├─ Repositories
  ├─ Domain Models
  ├─ Permission Services
  ├─ Realtime Manager
  └─ Database / Object Storage
```

---

# 4 顶层领域模块

## 4.1 Account Domain

负责用户、认证、站点身份。

包含：

- auth
- users
- feedback

## 4.2 Room Domain

负责房间、成员、审批、房间设置。

包含：

- rooms
- room_members
- room_join_requests
- role_change_requests
- permissions

## 4.3 Communication Domain

负责普通消息、RP 消息、实时事件。

包含：

- messages
- rp_messages
- realtime

## 4.4 Character Domain

负责角色卡、角色状态、资源、状态效果。

包含：

- characters
- character_states
- character_resources
- character_effects

## 4.5 Tabletop Domain

负责地图桌面、场景、Token、资源库。

包含：

- scenes
- maps
- tokens
- assets

## 4.6 Rule Domain

负责 DND5E 计算、骰子、战斗辅助。

包含：

- dice
- rulesets
- combat

## 4.7 Audit Domain

负责关键操作追踪。

包含：

- operation_logs

---

# 5 数据流原则

## 5.1 持久化操作

需要修改数据库的操作必须经过后端服务层：

```text
Frontend -> HTTP API / WebSocket Command -> Service -> Repository -> Database
```

服务层负责：

- 参数校验
- 权限校验
- 业务规则
- 事务控制
- 日志记录
- 实时事件发布

## 5.2 实时同步

状态变更完成后，由服务端发布实时事件：

```text
Service -> Realtime Manager -> WebSocket Clients
```

WebSocket 广播的应是服务端确认后的结果，而不是前端未经确认的本地状态。

---

# 6 房间作为协作边界

房间是系统中最重要的协作边界。

绝大多数业务数据均归属于某个房间：

- 成员
- 消息
- RP 消息
- 角色
- 场景
- 地图
- Token
- 骰子记录
- 操作日志

权限判断通常也以房间为上下文。

---

# 7 规则集扩展

系统优先实现 DND5E，但不应将所有字段和逻辑完全写死为 DND5E。

建议房间保留 `ruleset` 字段：

```text
DND5E
CUSTOM
```

规则相关逻辑通过规则集服务组织：

```text
rulesets/
├── base
├── dnd5e
└── custom
```

初始版本只实现 DND5E 必要计算，后续再扩展其他规则。

---

# 8 实时通信架构

实时通信以房间频道为核心。

```text
USER channel：用户级通知
ROOM channel：房间级事件
```

房间内事件包括：

- 消息创建
- RP 消息创建
- 角色状态变化
- Token 移动
- 场景切换
- 骰子结果
- 操作日志创建

---

# 9 存储架构

系统使用关系型数据库存储核心业务数据。

图片资源可存储在：

- 本地文件系统
- 对象存储
- 其他可访问文件服务

数据库中只保存资源元信息和访问 URL。

---

# 10 扩展原则

1. 新业务优先以模块形式添加。
2. 跨模块调用应通过 service 层完成，不直接跨模块访问 repository。
3. 权限校验集中在 service 层或 permission service 中。
4. 实时事件由业务操作触发，不应由前端伪造权威事件。
5. 地图、角色、骰子、日志等模块应保持边界清晰。

# TabletopForge 仓库现状

版本：v0.2  
状态：Living Document  
最后核对：2026-06-04（文档与 MVP 需求同步）
仓库：`Icezero0/TabletopForge`（`main`）

---

# 1 文档定位

本文档记录 TabletopForge **当前代码与文档的落地状态**，用于：

- 快速了解仓库已实现与未实现的能力
- 对照 `00_overview.md` 中的 Phase 1–5 判断进度
- 在开工新模块前确认依赖与缺口

本文档不替代各专项设计文档；**页面级 PRD** 见 `01_product_requirements.md` §5；接口字段、协议细节、权限矩阵仍以 `05_api_design.md`、`06_websocket_protocol.md`、`08_permission_design.md` 等为准。

**维护约定**：完成较大功能合并（新表、新模块、阶段里程碑）后更新本文档的「实现对照表」与「阶段判断」章节。

---

# 2 项目定位

TabletopForge 是面向 TRPG / DND 跑团的在线协作桌面系统，以**房间**为协作边界。目标能力包括角色卡、地图 Token、聊天与 RP、骰子、操作日志与 WebSocket 实时同步。

- 产品设计总览：`00_overview.md`（v0.2 Draft）
- 规则优先 DND5E，架构保留 `ruleset` 扩展空间
- 远程仓库：`https://github.com/Icezero0/TabletopForge.git`

---

# 3 技术栈与目录

| 层 | 技术 | 规模（约） |
|---|---|---|
| 前端 | Vue 3 + Vite 7 + TypeScript + Pinia + vue-router + vue-i18n + axios | ~97 个 `.vue` / `.ts` 源文件 |
| 后端 | FastAPI 模块化单体 + SQLAlchemy + Alembic | 8 个业务域模块 + 15 个 realtime 文件 |
| 测试 | pytest | 35 个测试文件 |
| 文档 | `docs/` 00–09 系列 + `09_module_design/` | 19 篇设计文档 |

```text
TabletopForge/
├── docs/           # 产品设计 / 架构 / API / WS / DB / 权限 / 模块设计
├── frontend/       # Vue SPA
├── backend/        # FastAPI + alembic + tests
└── README.md       # 文档入口索引
```

---

# 4 文档规划与代码落地对照

产品阶段划分见 `00_overview.md` 第 10 节（Phase 1–5）。**当前代码集中在 Phase 1 地基**；Phase 2–5 在 `09_module_design/` 有模块设计，后端尚无对应模块与数据表。

## 4.1 已实现

| 能力 | 后端模块 / 路径 | 前端页面 / Feature | 数据库表 |
|---|---|---|---|
| 注册 / 登录 / JWT | `auth`, `users` | `/auth/login`, `/auth/register` | `users` |
| 站点身份 `site_role` | `site/permissions` | 反馈管理页等 | `users.site_role` |
| 房间 CRUD / 可见性 | `rooms/room` | 首页创建房间、公开房间列表 | `rooms` |
| 成员与 `room_role` + `game_role` | `rooms/membership`, `rooms/permissions`, `rooms/game_permissions` | 房间成员 Tab、双身份展示与改 game_role | `room_members`（`role` + `game_role`） |
| 入房审批 | `rooms/join_request` | `JoinRequestsPage`、房间 Requests Tab | `room_join_requests` |
| 站内通知 | `notifications` | `NotificationsPage` | `notifications` |
| 房间普通聊天 | `messages` + realtime 广播 | `RoomChatTab`, `ChatPanel` | `messages` |
| 头像 / 反馈截图 | `assets`（avatar、feedback） | 资料编辑、联系页截图上传 | `assets` |
| 用户反馈 | `feedback` | `ContactPage`, `FeedbackAdminPage` | `feedbacks` |
| WebSocket 实时 | `realtime/*` | `useRoomRealtimeSession` | — |

HTTP 路由（`backend/app/api/v1/router.py`）当前注册：

- `auth`, `assets`, `users`, `rooms`, `notifications`, `room_join_request`, `messages`, `feedback`

ORM 模型导出（`backend/app/db/models.py`）与上表一致，无角色、场景、Token、骰子、操作日志等实体。

数据库迁移：`20260604_0001_initial_schema.py` + `20260604_0002_add_room_member_game_role.py`（`room_members.game_role`）。

## 4.2 文档已规划、代码未落地

| 模块（设计文档） | 说明 |
|---|---|
| 角色卡 / 角色状态 | `09_module_design/character_card.md`；预期表如 `characters`, `character_states` 等 |
| RP 消息 | `09_module_design/chat_and_rp.md`；`rp_messages` |
| 地图桌面 | `09_module_design/tabletop_scene.md`；`scenes`, `maps` 等 |
| Token | `09_module_design/token_system.md` |
| 骰子 / DND5E 规则 | `09_module_design/dice.md`, `dnd5e_rules.md` |
| 操作日志 | `09_module_design/operation_log.md` |
| 战斗辅助 | `09_module_design/combat_assistant.md` |
| 业务资源库（地图/Token 素材） | `09_module_design/asset_library.md`；当前 `assets` 仅头像与反馈图 |
| 跑团桌面（Table） | `01_product_requirements.md` §4.2、`09_module_design/tabletop_scene.md` 等 |

**身份说明**：`room_members.game_role`（`GM` | `PL` | `OB`）已落地，与 `room_role`（DB 列 `role`）分离；Tabletop 权限桩见 `game_permissions.py`（`08` §6.4，Step 4 起消费）。

房间页（`frontend/src/pages/room/RoomPage.vue`）当前为旧布局：工作区 Tab **聊天、成员、入房请求**。**跑团主界面**（地图核心 + 顶栏工具 + 左上角色列表 / 悬浮聊天 + 底栏素材 + 右侧 InfoPanel / 备忘录）**尚未实现**；交互见 `03_frontend_design.md` §4.2。

---

# 5 架构与通信（当前落地）

与 `02_architecture.md` 一致：

- **前后端分离**：HTTP 写入权威状态；WebSocket 广播服务端确认后的事件。
- **模块化单体**：`modules/{auth,users,rooms,messages,notifications,feedback,assets,site}` + `realtime/`。
- **协作边界**：已落地数据（消息、成员、审批等）均按 `room_id` 归属。
- **权限分层**：`site_role`、`room_role`、`game_role` 已实现（Tabletop 业务校验待 Step 4+）。

```text
Client (Vue)
  ├─ HTTP API  → FastAPI (Service → Repository → DB)
  └─ WebSocket → realtime/ (channels, presence, rest_sync, publisher)
```

---

# 6 前端路由与状态

路由定义：`frontend/src/router/routes.ts`。

| 路径 | 名称 | 需登录 | 说明 |
|---|---|---|---|
| `/auth/login`, `/auth/register` | login, register | 否 | 已登录会重定向首页 |
| `/` | home | 是 | 我的房间、创建房间 |
| `/rooms/:id` | room | 是 | 房间工作区；首次进入有 sync gate |
| `/profile` | profile | 是 | 资料与头像 |
| `/join-requests` | join-requests | 是 | 待处理的入房审批 |
| `/public-rooms` | public-rooms | 是 | 公开房间列表 |
| `/notifications` | notifications | 是 | 站内通知 |
| `/contact` | contact | 是 | 用户反馈 |
| `/feedback-admin` | feedback-admin | 是 | 站点管理员处理反馈 |

主要 Pinia Store：`auth`, `rooms`, `messages`, `notifications`, `entities`, `toasts`, `media-viewer`。

房间相关 composable：`useRoomWorkspaceLayout`, `useRoomRealtimeSession`, `useRoomJoinRequests`, `useRoomMemberActions`。

---

# 7 实时层现状

目录：`backend/app/realtime/`。

包含：协议（`protocol`）、频道（`channels`）、WS 认证、房间 handler、在线 presence、`rest_sync`（HTTP 变更后推送）、`publisher`、`dispatcher` 等。

与 `06_websocket_protocol.md` 设计方向一致。当前主要服务**房间级消息与成员相关事件**；Token 移动、场景切换、角色状态、骰子结果等游戏事件**尚未接入**。

---

# 8 测试覆盖概况

- **API 测试**：auth/users、rooms/messages/notifications、rooms 附加场景等（`backend/tests/api/`）。
- **单元测试**：auth、rooms repository、feedback、realtime 各子模块（`backend/tests/unit/`）。

已落地模块具备基础测试；未实现域暂无对应用例。

---

# 9 阶段进度判断

| 文档阶段（`00_overview.md` §10） | 状态 |
|---|---|
| Phase 1：基础房间与权限 | **大部分完成**（Table 区未实现） |
| 跑团桌面 MVP（`01` §4.2） | **进行中**（Step 1 `game_role` 已落地；Table 布局与地图/角色待 Step 2–5） |
| Phase 4：RP 与骰子 | **未开始**（普通聊天已具备；不在跑团桌面 MVP） |
| Phase 5：战斗辅助 | **未开始** |

## 9.1 近期演进线索（提交历史摘要）

从 Git 历史可见大致路径：

1. 继承 icinema 基础建设
2. 文档体系 v0.2 整理
3. 清理与 asset 资源库落地
4. 统一 initial schema（2026-06-04）
5. 前端房间 / 聊天 / 实时会话打磨

## 9.2 建议开发顺序

与 [`01_product_requirements.md`](01_product_requirements.md) §4.2 一致：

1. ~~迁移 `game_role`~~（已完成）→ Table 布局（Step 2）→ Tabletop 权限消费（Step 4）+ 业务 assets。
2. Table 视口、网格常显、地图底图（上传、锁定、z=0）。
3. Token 层（z=1）与角色 / 怪物数据模型。
4. 绘制层（z=2）、橡皮擦与框选删除（测距 ○ 后续）。
5. 每步更新 `05_api_design.md`、`07_database_design.md` 与本节实现对照表。

---

# 10 相关文档索引

| 主题 | 文档 |
|---|---|
| 系统边界与 Phase | `00_overview.md` |
| 模块划分与数据流 | `02_architecture.md` |
| 前端结构 | `03_frontend_design.md` |
| 后端分层 | `04_backend_design.md` |
| HTTP API | `05_api_design.md` |
| WebSocket | `06_websocket_protocol.md` |
| 表结构（设计态） | `07_database_design.md` |
| 权限矩阵 | `08_permission_design.md` |
| 业务模块细节 | `09_module_design/*.md` |

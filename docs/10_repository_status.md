# TabletopForge 仓库现状

版本：v0.4  
状态：Living Document  
最后核对：2026-06-07（角色 Token 配置 + 资源库引用 + 当前桌面实现核对）
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
| 前端 | Vue 3 + Vite 7 + TypeScript + Pinia + vue-router + vue-i18n + axios | 角色、房间、桌面、素材库等已形成实际页面与 feature 目录 |
| 后端 | FastAPI 模块化单体 + SQLAlchemy + Alembic | auth/users/rooms/messages/notifications/feedback/assets/library/characters + realtime |
| 测试 | pytest | API + unit 测试覆盖已落地模块；最新 Token Config 仍需补专项用例 |
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

产品阶段划分见 `00_overview.md` 第 10 节（Phase 1–5）。**当前代码已经越过纯 Phase 1 地基**：基础房间、权限、普通聊天、资源库、跑团桌面、地图/绘制/Token、角色卡、房间角色库、角色状态与 InfoPanel 均已有落地；RP、骰子、操作日志、战斗辅助仍主要停留在设计文档。

## 4.1 已实现

| 能力 | 后端模块 / 路径 | 前端页面 / Feature | 数据库表 |
|---|---|---|---|
| 注册 / 登录 / JWT | `auth`, `users` | `/auth/login`, `/auth/register` | `users` |
| 站点身份 `site_role` | `site/permissions` | 反馈管理页等 | `users.site_role` |
| 房间 CRUD / 可见性 | `rooms/room` | 首页创建房间、公开房间列表 | `rooms` |
| 成员与 `room_role` + `game_role` | `rooms/membership`, `rooms/permissions`, `rooms/game_permissions` | 房间成员 Tab、双身份展示与改 game_role、`PlayerColorPicker` | `room_members`（`role` + `game_role` + `player_color`） |
| 入房审批 | `rooms/join_request` | `JoinRequestsPage`、房间 Requests Tab | `room_join_requests` |
| 站内通知 | `notifications` | `NotificationsPage` | `notifications` |
| 房间普通聊天 | `messages` + realtime 广播 | `RoomChatTab`, `ChatPanel` | `messages` |
| 头像 / 头像历史 / 反馈截图 / 底层 image/audio | `assets`, `users` | 资料编辑、联系页截图上传；资源库页面 | `assets`, `user_avatar_history` |
| 用户反馈 | `feedback` | `ContactPage`, `FeedbackAdminPage` | `feedbacks` |
| 个人资源库（map_background / token / sound） | `library` | `LibraryPage` | `library_resources` |
| 角色卡（DnD 5e） | `characters` | `CharactersPage`（列表）、`CharacterEditPage`（新建/编辑，7 Tab）、`CharacterImportDialog` | `characters`, `character_states` |
| 角色 Token 配置 | `characters` + `library` | `CharacterTokenTab`, `TokenCard`, `TokenPanelEditorDialog` | `character_token_configs`，可关联 `library_resources` |
| AI 角色导入预览 | `characters/import_service` | 编辑页「AI 导入」；`POST /characters/import-preview` | — |
| WebSocket 实时 | `realtime/*` | `wsClient`, `useRoomRealtimeSession` | — |
| 个人备忘录（按房间） | `rooms/personal_memo` | `PersonalMemo` | `room_personal_memos` |

HTTP 路由（`backend/app/api/v1/router.py`）当前注册：

- `auth`, `assets`, `users`, `rooms`, `notifications`, `room_join_request`, `messages`, `feedback`, `library`, `characters`

ORM 模型（当前代码定义）：
`User`, `UserAvatarHistory`, `Asset`, `Room`, `RoomMember`, `RoomJoinRequest`,
`RoomPersonalMemo`, `RoomTabletopSettings`, `RoomMap`, `RoomDrawing`,
`RoomToken`, `RoomCharacter`, `Notification`, `Message`, `Feedback`,
`LibraryResource`, `Character`, `CharacterState`, `CharacterTokenConfig`。

数据库迁移链：

- `20260604_0001_initial_schema`
- `20260604_0002_add_room_member_game_role`
- `20260604_0003_add_room_personal_memos`
- `20260605_0004_add_asset_hash_ref_count_and_avatar_history`
- `20260604_0004_add_room_tabletop`
- `20260606_0005_add_library_resources`
- `20260606_0006_add_characters`
- `20260606_0007_add_room_tokens`
- `20260606_0008_extend_characters_kind_token_image`
- `20260606_0009_add_character_states`
- `20260606_0010_add_room_characters`
- `20260606_0011_add_room_member_player_color`
- `20260606_0012_migrate_character_kinds`
- `20260607_0013_add_character_token_configs`
- `20260607_0014_add_library_resource_to_token_config`（current head）

## 4.2 规划模块与落地差异

| 模块（设计文档） | 说明 |
|---|---|
| RP 消息 | `09_module_design/chat_and_rp.md`；`rp_messages` 尚未落地 |
| 地图桌面（MVP 扁平） | `rooms/tabletop`；`room_tabletop_settings`, `room_maps`, `room_drawings`, **`room_tokens`** 已落地；地图/绘制/Token HTTP + WS 已接入 |
| **房间角色库 / CharacterState** | **Phase 2–4 已落地**：`room_characters`、`character_states`；`GET/POST /rooms/{id}/characters` + **`POST .../characters/link`**（全局库关联）；`characters.kind`（`pc_main`/`pc_additional`/`npc`）；`kind=npc` 时 PL 仅 `damage_taken`（presenter）；GM PATCH 降 HP 累计伤害；WS `state_summary_public` |
| Token | **Phase 1–4 已落地**：`room_tokens` CRUD、WS、`TokenLayer`；`linked_character_id`、`spawn-token`、`state_summary`（HP/AC/PP）、`character_state_updated` WS |
| InfoPanel / 场上列表 | **Phase 3–5 已落地**：`InfoPanel`（六维 + State；不展示 `custom_fields`）；`InGameCharacterList`；`AddRoomCharacterDialog` + `CharacterSpawnPopover`（合并全局库、`link` 上场、GM 创建者）+ `MapSpawnPopover`（地图切换）；Context Menu「查看信息」 |
| 角色 Token 配置 | **2026-06-07 已落地**：`character_token_configs`；角色编辑页 Token Tab 可生成主要 Token、添加次要 Token、上传图片、编辑 panel 初始值；primary config 缺少 `library_resource_id` 时后端自动创建 `library_resources(type=token)` 并维护 `usage_count` |
| 骰子 / DND5E 规则 | `09_module_design/dice.md`, `dnd5e_rules.md` |
| 操作日志 | `09_module_design/operation_log.md` |
| 战斗辅助 | `09_module_design/combat_assistant.md` |
| 资源库 Token/声音素材类型 | 后端 `library` 模块已落地 `map_background` / `token` / `sound`；业务 asset **`token_image`** 已用于地图 Token 和角色 Token 配置 |
| 跑团桌面（Table） | `01_product_requirements.md` §4.2、`09_module_design/tabletop_scene.md` 等；当前房间页已实现全屏 TableStage + 悬浮面板工作区 |

**身份说明**：`room_members.game_role`（`GM` | `PL` | `OB`）已落地，与 `room_role`（DB 列 `role`）分离；Tabletop 权限已在地图、绘制、Token、角色状态等服务中消费，规则集中在 `game_permissions.py`。

房间页（`frontend/src/pages/room/RoomPage.vue`）已实现 **全屏地图 + 悬浮可收起面板**（`features/table/`）：`TableStage` + `MapViewport` 铺满视口；地图/绘制/**Token** 协作；底栏 **`CharacterSpawnPopover`**（房间库 + 全局库合并、未入库 `link` 上场、GM 显示创建者）与 **`MapSpawnPopover`**（地图列表切换）+ 左上 **InGameCharacterList**；Token **HP/AC/PP 预览**（`npc` 对 PL 仅伤害）；右侧 **InfoPanel** 单槽。

---

# 5 架构与通信（当前落地）

与 `02_architecture.md` 一致：

- **前后端分离**：HTTP 写入权威状态；WebSocket 广播服务端确认后的事件。
- **模块化单体**：`modules/{auth,users,rooms,messages,notifications,feedback,assets,site,library}` + `realtime/`。
- **协作边界**：已落地数据（消息、成员、审批等）均按 `room_id` 归属。
- **权限分层**：`site_role`、`room_role`、`game_role` 已实现；Tabletop 业务校验已接入地图、绘制、Token 与角色状态写入。

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
| `/library` | library | 是 | 用户资源库（地图 / Token / 声音素材） |
| `/characters` | characters | 是 | 角色卡列表 |
| `/characters/new` | character-new | 是 | 新建角色卡 |
| `/characters/:id` | character-edit | 是 | 编辑角色卡 |
| `/feedback-admin` | feedback-admin | 是 | 站点管理员处理反馈 |
| `/site-admin` | site-admin | 是 | 站点管理 |

主要 Pinia Store：`auth`, `rooms`, `messages`, `notifications`, `entities`, `toasts`, `media-viewer`。

房间相关 composable：`useRoomWorkspaceLayout`, `useRoomRealtimeSession`, `useRoomJoinRequests`, `useRoomMemberActions`。

---

# 7 实时层现状

目录：`backend/app/realtime/`。

包含：协议（`protocol`）、频道（`channels`）、WS 认证、房间 handler、在线 presence、`rest_sync`（HTTP 变更后推送）、`publisher`、`dispatcher` 等。

与 `06_websocket_protocol.md` 设计方向一致。已接入 tabletop 事件（settings/map/drawing/**token**）、角色状态更新、房间成员/房间信息 signal、普通消息、通知、presence、pointer/laser、session close；骰子结果等游戏事件尚未接入。

---

# 8 测试覆盖概况

- **API 测试**：auth/users、rooms/messages/notifications、assets/feedback、room tabletop、room tokens、room characters、GM NPC visibility、character import 等（`backend/tests/api/`）。
- **单元测试**：auth、rooms repository、feedback、realtime 各子模块（`backend/tests/unit/`）。

已落地模块具备基础测试；最新 `character_token_configs` / `library_resource_id` 引用维护建议补专项测试；未实现域暂无对应用例。

---

# 9 阶段进度判断

| 文档阶段（`00_overview.md` §10） | 状态 |
|---|---|
| Phase 1：基础房间与权限 | **大部分完成**；房间、成员、入房审批、普通聊天、通知、站点身份、游戏身份均已落地 |
| 跑团桌面 MVP（`01` §4.2） | **Step 5 已完成并进入深化**：地图/绘制/Token/角色绑定/InfoPanel/场上列表/玩家主色/地图 Popover/全局库 link 上场已落地；2026-06-07 起继续深化角色 Token 配置 |
| Phase 4：RP 与骰子 | **未开始**（普通聊天已具备；不在跑团桌面 MVP） |
| Phase 5：战斗辅助 | **未开始** |

## 9.1 近期演进线索（提交历史摘要）

从 Git 历史可见大致路径：

1. 继承 icinema 基础建设
2. 文档体系 v0.2 整理
3. 清理与 asset 资源库落地
4. 统一 initial schema（2026-06-04）
5. 前端房间 / 聊天 / 实时会话打磨
6. 角色卡模块落地（2026-06-06）：`characters` 表、CRUD API、角色编辑页（DnD 5e 结构化数据）、角色列表页、脏数据守卫
7. 房间 Popover 增强（2026-06-06）：`POST /rooms/{id}/characters/link`；前端 `spawnCharacters.ts` 合并全局库；GM 创建者展示（`4730ec6`）
8. 角色 Token 配置深化（2026-06-07）：`character_token_configs`、`library_resource_id` 关联、角色编辑 Token Tab、主要/次要 Token panel 初始值。

## 9.2 建议开发顺序

与 [`01_product_requirements.md`](01_product_requirements.md) §4.2 一致：

1. 补齐 `character_token_configs` 相关测试：创建/更新/删除 config、primary 自动创建 `library_resources(type=token)`、`usage_count` 增减。
2. 将角色 Token 配置真正用于上场 Token 选择：spawn 时支持选择 primary/secondary token config，而不是只取 `character.token_image_asset_id || portrait_asset_id`。
3. 梳理 `backend/app/db/models.py` 的集中导出，避免新模型只存在于业务模块中而文档/迁移维护时漏判。
4. 推进 RP 与骰子：普通聊天已具备，下一步应引入 RP 消息结构、骰子表达式、结果广播和房间内可见性。
5. 推进操作日志与战斗辅助：优先记录 Token/HP/地图/角色状态等已落地对象的关键变更。
6. 每个较大阶段后同步更新 `05_api_design.md`、`07_database_design.md` 与本文档。

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

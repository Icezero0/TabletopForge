# TabletopForge 仓库现状

版本：v0.6  
状态：Living Document  
最后核对：2026-06-19（房间类型 / DND5E 模式拆分 / ThunderStone 原型 / 当前数据库迁移核对）  
仓库：`Icezero0/TabletopForge`（`main`）

---

# 1 文档定位

本文档记录 TabletopForge **当前代码已经落地的状态**。若与早期 PRD、架构或模块设计文档冲突，以本文档和当前前后端代码为准。

维护约定：

- 完成新表、新业务模块、房间模式拆分、实时协议扩展后，应优先更新本文档。
- 具体字段和协议仍需同步维护 `05_api_design.md`、`06_websocket_protocol.md`、`07_database_design.md`。
- `09_module_design/` 中部分文档仍保留早期设想，不能直接视为当前实现。

---

# 2 当前定位

TabletopForge 已从单一 DND 跑团桌面，推进为：

```text
房间基础层
  ├─ 成员 / 权限 / 邀请 / 通知 / 聊天 / 基础 WebSocket
  ├─ 房间类型 Room.type
  └─ 不依赖具体游戏模式

DND5E 房间模式
  ├─ 地图桌面 / 指示物 / 角色卡 / 掷骰 / 战斗 / 场景 / 迷雾 / 音乐
  └─ 当前主要可用模式

ThunderStone 房间模式
  ├─ DBG 电子化方向
  ├─ 当前只有前端原型布局
  └─ 卡牌资产与结构化定义整理中
```

---

# 3 技术栈与目录

| 层 | 技术 / 目录 | 当前状态 |
|---|---|---|
| 前端 | Vue 3 + Vite 7 + TypeScript + Pinia + vue-router + vue-i18n | 已有 DND5E 房间模式、ThunderStone 原型、资源库、角色卡、房间工作区 |
| 后端 | FastAPI + SQLAlchemy + Alembic | 模块化单体；房间、角色、资源库、骰子、场景、实时层均已落地 |
| 数据 | SQLite dev / Alembic | 当前迁移 head：`20260618_0034_add_room_type` |
| 文档 | `docs/` | 本文档已更新；部分专项文档仍需继续追平 |
| ThunderStone 数据 | `data/thunderstone/source/cards` | 已导入卡牌图片与 localizer work state，尚未生成正式 catalog |

---

# 4 房间与游戏模式

## 4.1 房间基础层

已落地：

- 房间 CRUD、公开/私有、加入审批。
- 成员身份：
  - `room_role`：房间管理身份，DB 列名为 `role`。
  - `game_role`：游戏身份，`GM | PL | OB`。
- 玩家主色 `player_color`。
- 房间成员、邀请、权限与房间设置逻辑已在前端抽为 `useRoomGovernance`。
- 房间基础 WebSocket 已在前端抽为 `useRoomRealtimeSession`，负责：
  - 进入/离开房间
  - presence
  - 房间信息与成员刷新
  - 普通消息
  - 掷骰日志
  - session close

## 4.2 Room.type

`rooms.type` 已落地，当前取值：

```text
DND5E
ThunderStone
```

创建房间时选择类型，创建后不允许修改。历史房间迁移默认 `DND5E`。

前端入口：

- `frontend/src/pages/room/RoomPage.vue`：按 `room.type` 分发。
- `Dnd5eRoomMode.vue`：现有 DND5E 房间。
- `ThunderStoneRoomMode.vue`：ThunderStone 原型。

## 4.3 DND5E 模式

当前 DND5E 模式已经包含：

- 地图桌面、缩放、平移、网格标定。
- 地图资源库与场上地图。
- 绘制工具、测距、Pointer。
- 指示物创建、拖拽、图层、右键菜单、信息面板。
- 对象占用：只在拖拽等人类级长操作中占用，允许多人只读查看信息。
- 角色列表、房间角色、角色可见性、隐藏数据。
- 角色卡与 token config。
- 掷骰日志、暗骰、主体、预设、公式编辑器。
- 战斗面板、自动先攻、回合、加入战斗、设置当前回合、本轮/下轮行动。
- 战争迷雾、GM/非 GM 透明度控制。
- 背景音乐、播放列表和本地音量。
- 场景保存/切换。
- 个人备忘录。

## 4.4 ThunderStone 模式

当前仅为原型：

- 前端有村庄区域、地下城区域、玩家区域的静态布局。
- 未落地后端专用模型。
- 当前讨论方向：
  - 卡牌图片与文字分离。
  - 使用 `.card_localizer_work/*_image.png` 作为空白卡牌底图。
  - 使用 `work_state.json` 的 `texts` 生成草稿结构化卡牌定义。
  - 后续建立卡牌状态、牌区、牌堆、原子动作与效果脚本系统。

---

# 5 已实现模块总览

| 能力 | 后端模块 / 路径 | 前端位置 | 主要数据 |
|---|---|---|---|
| 注册 / 登录 / JWT | `auth`, `users` | 登录/注册页 | `users` |
| 用户资料 / 头像 | `users`, `assets` | 资料页 | `users`, `user_avatar_history`, `assets` |
| 站点权限 | `site/permissions` | 反馈/站点管理 | `users.site_role` |
| 房间基础 | `rooms/room` | 首页、公开房间、房间页 | `rooms` |
| 成员 / 邀请 / 审批 | `rooms/membership`, `rooms/join_request` | `GovernanceDock`, `useRoomGovernance` | `room_members`, `room_join_requests` |
| 通知 | `notifications` | 通知页 | `notifications` |
| 普通聊天 | `messages` | 会话面板 | `messages` |
| 资源库 | `library`, `assets` | 资源库页、房间素材面板 | `library_resources`, `assets` |
| 角色卡 | `character` | 角色列表、角色编辑页 | `characters`, `character_states`, `character_token_configs` |
| DND 桌面 | `rooms/tabletop` | `features/table/*` | `room_maps`, `room_drawings`, `room_tokens`, `room_tabletop_settings` |
| 房间角色 | `rooms/characters` | 房间角色列表、指示物生成 | `room_characters` |
| 掷骰 | `dice`, `rooms/dice` | 掷骰日志/编辑器/预设 | `room_dice_rolls`, `dice_presets` |
| 场景 | `rooms/scenes` | 素材面板「切换场景」 | `room_scenes` |
| 个人备忘录 | `rooms/personal_memo` | 右下备忘录 | `room_personal_memos` |
| WebSocket | `realtime/*` | `wsClient`, room/tabletop realtime composables | 无单独表 |

---

# 6 数据库迁移现状

当前迁移链已经从早期 `0014` 推进到：

```text
20260618_0034_add_room_type
```

重要新增能力：

- `room_dice_rolls`
- `room_scenes`
- `dice_presets`
- `characters.resources`
- `room_character.hide_data`
- `RoomTabletopSettings.combat_state`
- `RoomTabletopSettings.music_state`
- `RoomTabletopSettings.fog_state`
- `characters.primary_token_resource_id`
- `rooms.type`

详见 `07_database_design.md` 的「当前实现补充」章节。

---

# 7 WebSocket 现状

后端实时层仍位于 `backend/app/realtime/`。

前端已拆分：

- `useRoomRealtimeSession`：房间基础事件。
- `useTabletopRealtimeEvents`：DND/tabletop 专用事件。

已使用事件包括：

- `room_info`
- `room_members`
- `room_user_presence`
- `session_closed`
- `message`
- `dice_roll`
- `room_characters`
- `tabletop_settings_updated`
- `tabletop_snapshot_replaced`
- `map_created / map_updated / map_deleted`
- `drawing_created / drawing_updated / drawing_deleted`
- `token_created / token_updated / token_deleted`
- `token_transform_preview`
- `character_state_updated`
- `room_character_updated`
- `pointer_presence`
- `pointer_laser`
- `object_selection`

---

# 8 文档同步情况

本轮已对齐的文档：

- `00_overview.md`：已补房间类型、DND5E / ThunderStone 分离与当前能力摘要。
- `05_api_design.md`：已补 room type、DND5E tabletop、scene、dice、dice presets 等当前接口。
- `06_websocket_protocol.md`：已补当前事件摘要，但仍未写全每个 payload。
- `07_database_design.md`：已补当前实现摘要，但仍未按 ORM 逐表展开所有字段。
- `09_module_design/dice.md`：已改为当前实现态。
- `09_module_design/combat_assistant.md`：已改为当前实现态。
- `09_module_design/tabletop_scene.md`：已补场景、迷雾、音乐等当前实现。
- `09_module_design/thunderstone.md`：已新增 ThunderStone 原型与卡牌资产整理说明。

仍明显落后的文档：

- `01_product_requirements.md`：仍偏早期 DND 跑团产品阶段，含大量 MVP 历史表述。
- `03_frontend_design.md`：仍偏早期固定面板布局与旧工作区规划。
- `04_backend_design.md`：仍偏早期模块划分，未体现 room mode 分离。
- `08_permission_design.md`：需要补齐当前战斗、迷雾、音乐、场景、掷骰预设等权限细节。
- `09_module_design/asset_library.md`、`token_system.md`、`character_card.md`：已补当前摘要；后续仍可继续补齐字段级细节与示例。

---

# 9 近期建议

1. 为 ThunderStone 建立卡牌 catalog 生成脚本与正式数据模型。
2. 将 `07_database_design.md` 按当前 ORM 逐表追平。
3. 将 `06_websocket_protocol.md` 补全 payload 示例。
4. 为 DND5E / ThunderStone 的房间模式边界补一份架构说明。
5. 追平 `01_product_requirements.md` 与 `03_frontend_design.md`，避免 MVP 历史描述误导后续实现。

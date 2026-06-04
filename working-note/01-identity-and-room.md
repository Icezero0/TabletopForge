# Step 1：基础身份与房间治理

**目标**：跑团权限与房间治理地基就绪，用户能创建房间、拉人/加入、配置双层身份。本步 **不做** 跑团主界面五区布局与地图/角色业务。

**依据**：`docs/08` §4–5、`docs/01` §2、`docs/07` room_members。

---

## 本步做

### 1.1 `game_role` 数据与 API

- `room_members` 增加 `game_role`：`GM` | `PL` | `OB`（默认入房建议 `PL`）。
- Alembic 迁移；ORM / Schema 更新。
- 读写成员时返回 `room_role` + `game_role`，二者 **不** 互相推导。

### 1.2 身份配置

- 治理者（`room_role` 为 `owner` / `manager`）可为成员设置 `game_role`。
- 创建房间时，创建者可选择自己的初始 `game_role`（如房主当 `PL`）。
- 后端按 `08` §6.2 校验治理操作，按 §6.4 预留 Tabletop 校验挂载点（具体地图权限 Step 4 再用）。

### 1.3 房间创建与设置

- **已有**：创建房间、可见性、入房审核模式。
- **本步补齐/对齐**：
  - 房间设置（名称、可见性、审核模式等）与 [`RoomSettingsTab`](../frontend/src/features/room/components/workspace/RoomSettingsTab.vue) 行为一致。
  - 文档化房间级配置项边界（仍 **单活跃地图**，无 Campaign/Session）。

### 1.4 拉人与加入

- **已有**：公开房间列表、入房申请、审批、`JoinRequestsPage`、通知。
- **本步验收**：
  - 邀请/申请 → 审批 → `room_member` 创建且带默认 `game_role`。
  - 成员列表展示 **双身份**（治理角色 + 游戏角色），而非混为一谈。

### 1.5 站点侧（顺带）

- **已有**：`SiteAdminPage`、站点 `site_role`。
- 本步仅确认与房间流程无冲突，不扩展 Tabletop。

---

## 本步不做

- 跑团主界面新布局（Step 2）。
- 地图、Token、绘制、角色卡表（Step 4–5）。
- `game_role=OB` 完整只读体验（可落库枚举，UI 可后置）。
- Campaign / Session / Scene。

---

## 验收清单（简要）

- [ ] 房主 `owner` + `game_role=PL` 可创建房间并进入。
- [ ] 另一用户 `game_role=GM` 可被治理者指派，且与 `room_role=member` 不矛盾。
- [ ] 入房审批通过后成员带 `game_role`。
- [ ] 房间设置修改持久化。
- [ ] 公开房间申请 + 审批流端到端可用。

---

## 主要触点（实现时查阅）

| 层 | 路径 |
|---|---|
| 模型 | `backend/app/modules/rooms/models.py` |
| 成员 API | `rooms/membership`、`room_join_request` |
| 前端房间 | `RoomPage`、`JoinRequestsPage`、`public-rooms` |
